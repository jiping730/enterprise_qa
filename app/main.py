import os
import shutil
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import DATA_DIR, INDEX_DIR
from app.database import init_db, get_db
from app.models_db import User, KnowledgeBase, Document as DBDocument, QueryLog
from app.models_api import AskRequest, AskResponse, UploadResponse
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_kb_permission,
)
from app.document_loader import load_and_split, ALLOWED_EXTENSIONS
from app.vector_store import add_documents_to_kb, delete_document_from_kb
from app.qa_chain import answer_question

# ---------- 项目根目录 & 静态文件 ----------
BASE_DIR = Path(__file__).resolve().parent.parent
static_dir = BASE_DIR / "static"

if not static_dir.exists():
    raise RuntimeError(f"静态文件目录不存在: {static_dir}。请确认项目结构正确。")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="企业多知识库问答平台", version="2.0", lifespan=lifespan)

# 挂载静态文件（绝对路径）
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# ---------- 页面路由 ----------
@app.get("/")
@app.get("/login")
async def login_page():
    return FileResponse(str(static_dir / "login.html"))

@app.get("/app")
async def main_page():
    return FileResponse(str(static_dir / "index.html"))

# ---------- 认证 ----------
@app.post("/register")
def register(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    if db.query(User).filter_by(username=username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(username=username, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    return {"message": "注册成功"}

@app.post("/token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter_by(username=form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

# ---------- 知识库管理 ----------
@app.post("/kbs")
def create_kb(
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    kb = KnowledgeBase(name=name, description=description, owner_id=user.id)
    db.add(kb)
    db.commit()
    # 创建者自动获得自己知识库的授权
    user.kbs.append(kb)
    db.commit()
    return {"id": kb.id, "name": kb.name}

@app.get("/kbs")
def list_kbs(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    kbs = (
        db.query(KnowledgeBase)
        .filter(
            (KnowledgeBase.owner_id == user.id)
            | (KnowledgeBase.authorized_users.any(id=user.id))
        )
        .all()
    )
    return [
        {
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "owner": kb.owner.username,
        }
        for kb in kbs
    ]

@app.delete("/kbs/{kb_id}")
def delete_kb(
    kb_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    kb = db.query(KnowledgeBase).get(kb_id)
    if not kb or kb.owner_id != user.id:
        raise HTTPException(status_code=403, detail="仅知识库所有者可删除")

    # 1. 删除知识库下的所有文档（数据库记录 + 物理文件 + 向量索引）
    docs = db.query(DBDocument).filter_by(kb_id=kb_id).all()
    for doc in docs:
        # 物理文件
        file_path = os.path.join(DATA_DIR, f"kb_{kb_id}", doc.filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        # 向量索引
        delete_document_from_kb(kb_id, doc.filename)
        # 数据库记录
        db.delete(doc)
    db.flush()  # 确保外键约束先解除

    # 2. 删除该知识库的所有查询日志
    logs = db.query(QueryLog).filter(QueryLog.kb_id == kb_id).all()
    for log in logs:
        db.delete(log)
    db.flush()

    # 3. 清理空目录与索引
    kb_data_path = os.path.join(DATA_DIR, f"kb_{kb_id}")
    if os.path.exists(kb_data_path):
        shutil.rmtree(kb_data_path)
    index_dir = os.path.join(INDEX_DIR, f"kb_{kb_id}")
    if os.path.exists(index_dir):
        shutil.rmtree(index_dir)

    # 4. 删除知识库本身
    db.delete(kb)
    db.commit()
    return {"message": "知识库已删除"}

@app.post("/kbs/{kb_id}/authorize")
def authorize_user(
    kb_id: int,
    username: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    kb = db.query(KnowledgeBase).get(kb_id)
    if not kb or kb.owner_id != user.id:
        raise HTTPException(status_code=403, detail="仅知识库所有者可授权")
    target = db.query(User).filter_by(username=username).first()
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    if target in kb.authorized_users:
        return {"message": "该用户已有权限"}
    kb.authorized_users.append(target)
    db.commit()
    return {"message": f"用户 {username} 已获得访问权限"}

# ---------- 文档管理 ----------
@app.get("/kbs/{kb_id}/documents")
def list_docs(
    kb_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    kb = get_kb_permission(kb_id, db, user)
    docs = db.query(DBDocument).filter_by(kb_id=kb_id).all()
    return [
        {"id": doc.id, "filename": doc.filename, "upload_time": doc.upload_time}
        for doc in docs
    ]

@app.post("/kbs/{kb_id}/upload")
async def upload_docs(
    kb_id: int,
    files: list[UploadFile] = File(...),   # 多文件
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    kb = get_kb_permission(kb_id, db, user)

    processed = 0
    total_chunks = 0

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            continue

        kb_data_dir = os.path.join(DATA_DIR, f"kb_{kb_id}")
        Path(kb_data_dir).mkdir(parents=True, exist_ok=True)
        file_path = os.path.join(kb_data_dir, file.filename)
        with open(file_path, "wb") as f_buf:
            f_buf.write(await file.read())

        docs = load_and_split(file_path)
        add_documents_to_kb(kb_id, docs)

        db_doc = DBDocument(filename=file.filename, kb_id=kb_id)
        db.add(db_doc)
        processed += 1
        total_chunks += len(docs)

    db.commit()
    return UploadResponse(
        message=f"成功处理 {processed} 个文件，生成 {total_chunks} 个片段",
        file_count=processed,
        chunk_count=total_chunks,
    )

@app.delete("/kbs/{kb_id}/documents/{doc_id}")
def delete_doc(
    kb_id: int,
    doc_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    kb = get_kb_permission(kb_id, db, user)
    doc = db.query(DBDocument).filter_by(id=doc_id, kb_id=kb_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    file_path = os.path.join(DATA_DIR, f"kb_{kb_id}", doc.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    delete_document_from_kb(kb_id, doc.filename)

    db.delete(doc)
    db.commit()
    return {"message": "文档已删除"}

# ---------- 问答 ----------
@app.post("/kbs/{kb_id}/ask", response_model=AskResponse)
def ask_question(
    kb_id: int,
    req: AskRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    kb = get_kb_permission(kb_id, db, user)
    answer, sources, confidence = answer_question(
        kb_id=kb_id,
        question=req.question,
        user=user,
        filter_docs=req.documents,
        session_id=req.session_id,
    )
    return AskResponse(answer=answer, sources=sources, confidence=confidence)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)