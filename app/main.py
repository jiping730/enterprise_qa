import os
import shutil
from pathlib import Path
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.models import AskRequest, AskResponse, UploadResponse
from app.document_loader import load_and_split, ALLOWED_EXTENSIONS
from app.vector_store import add_documents, reset_knowledge_base
from app.qa_chain import answer_question
from app.config import DATA_DIR

# 项目根目录（app/main.py 的上两级）
BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(title="企业文档智能问答助手", version="2.0")

# 数据目录（相对根目录）
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

# 挂载静态文件（使用绝对路径，彻底解决找不到目录的问题）
static_dir = BASE_DIR / "static"
if not static_dir.exists():
    raise RuntimeError(f"静态文件目录不存在: {static_dir}")
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", response_class=FileResponse)
async def index():
    return FileResponse(str(static_dir / "index.html"))

@app.post("/upload", response_model=UploadResponse)
async def upload_documents(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="没有选择文件")
    saved_paths = []
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")
        file_path = os.path.join(DATA_DIR, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        saved_paths.append(file_path)

    all_docs = []
    for path in saved_paths:
        try:
            docs = load_and_split(path)
            all_docs.extend(docs)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"处理 {os.path.basename(path)} 失败: {str(e)}")

    if all_docs:
        add_documents(all_docs)
        return UploadResponse(
            message=f"成功！已处理 {len(files)} 个文件，生成 {len(all_docs)} 个文本片段。",
            file_count=len(files),
            chunk_count=len(all_docs)
        )
    else:
        return UploadResponse(message="文件已上传但未提取到任何文本内容。", file_count=len(files), chunk_count=0)

@app.get("/documents")
async def list_documents():
    if not os.path.exists(DATA_DIR):
        return {"documents": []}
    files = [f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))]
    return {"documents": sorted(files)}

@app.delete("/reset")
async def reset():
    reset_knowledge_base()
    if os.path.exists(DATA_DIR):
        shutil.rmtree(DATA_DIR)
        Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    return {"message": "知识库已清空，所有文档和索引已删除。"}

@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")
    answer, sources = answer_question(req.question)
    return AskResponse(answer=answer, sources=sources)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)