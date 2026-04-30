import os
import shutil
from pathlib import Path
from typing import List
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.responses import HTMLResponse
import uvicorn

from app.models import AskRequest, AskResponse, UploadResponse
from app.document_loader import load_and_split, ALLOWED_EXTENSIONS
from app.vector_store import add_documents, reset_knowledge_base, get_retriever
from app.qa_chain import answer_question
from app.config import DATA_DIR

# 确保存储目录存在
Path(DATA_DIR).mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title="企业文档智能问答助手",
    version="1.0",
    description="上传 PDF/TXT/DOCX 文档，通过自然语言提问获取带来源标注的答案"
)

# --------------------- 前端 HTML 页面 ---------------------
@app.get("/", response_class=HTMLResponse)
async def index():
    return """
<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <title>企业文档问答</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; max-width: 900px; margin: 50px auto; padding: 20px; }
        h2 { color: #2c3e50; }
        .section { margin-bottom: 30px; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }
        input[type="file"] { margin: 10px 0; }
        button { padding: 8px 20px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #2980b9; }
        #status, #answerArea { white-space: pre-wrap; background: #f9f9f9; padding: 15px; border-radius: 4px; margin-top: 10px; }
        #docList { margin-top: 10px; }
        .source-item { background: #eef5fb; padding: 10px; margin: 5px 0; border-radius: 4px; }
    </style>
</head>
<body>
    <h2>📄 企业文档智能问答助手</h2>
    <div class="section">
        <h3>📤 上传文档</h3>
        <input type="file" id="fileInput" multiple accept=".pdf,.txt,.docx">
        <button onclick="uploadFiles()">上传并处理</button>
        <p id="uploadStatus"></p>
        <button onclick="listDocuments()">📋 查看已上传文档</button>
        <div id="docList"></div>
        <button onclick="resetKB()" style="background:#e74c3c;">⚠️ 清空知识库</button>
    </div>
    <div class="section">
        <h3>❓ 提问</h3>
        <input type="text" id="questionInput" size="60" placeholder="例如：合同有效期到什么时候？">
        <button onclick="askQuestion()">提问</button>
        <div id="answerArea"></div>
    </div>
    <script>
        async function uploadFiles() {
            const files = document.getElementById('fileInput').files;
            if (!files.length) return alert('请选择文件');
            const formData = new FormData();
            for (let f of files) formData.append('files', f);
            const res = await fetch('/upload', {method:'POST', body:formData});
            const data = await res.json();
            document.getElementById('uploadStatus').innerText = data.message;
        }
        async function listDocuments() {
            const res = await fetch('/documents');
            const data = await res.json();
            let html = '<b>已处理文档：</b><br>';
            if (data.documents.length===0) html += '（无文档）';
            else data.documents.forEach(f => html += `• ${f}<br>`);
            document.getElementById('docList').innerHTML = html;
        }
        async function resetKB() {
            if (!confirm('确定要清空所有知识库内容吗？此操作不可恢复。')) return;
            const res = await fetch('/reset', {method:'DELETE'});
            const data = await res.json();
            document.getElementById('uploadStatus').innerText = data.message;
            listDocuments();
        }
        async function askQuestion() {
            const q = document.getElementById('questionInput').value.trim();
            if (!q) return alert('请输入问题');
            const res = await fetch('/ask', {
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body: JSON.stringify({question: q})
            });
            const data = await res.json();
            let html = `<b>回答：</b><br>${data.answer}<br><br><b>参考来源：</b><br>`;
            if (data.sources.length) {
                data.sources.forEach((s,i) => {
                    html += `<div class="source-item">[${i+1}] 文档：${s.source}，页码：${s.page ?? '-'}<br>片段：${s.content}</div>`;
                });
            } else {
                html += '无来源信息';
            }
            document.getElementById('answerArea').innerHTML = html;
        }
    </script>
</body>
</html>
"""

# --------------------- API 接口 ---------------------

@app.post("/upload", response_model=UploadResponse)
async def upload_documents(files: list[UploadFile] = File(...)):
    """上传一个或多个文档，自动解析并存入知识库"""
    if not files:
        raise HTTPException(status_code=400, detail="没有选择文件")

    allowed_ext = ALLOWED_EXTENSIONS
    saved_paths = []
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_ext:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")
        # 保存到本地 data 目录
        file_path = os.path.join(DATA_DIR, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        saved_paths.append(file_path)

    # 处理所有文件
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
    """列出 data 目录下所有已上传的文件名"""
    if not os.path.exists(DATA_DIR):
        return {"documents": []}
    files = [f for f in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, f))]
    return {"documents": sorted(files)}

@app.delete("/reset")
async def reset():
    """清空知识库及所有上传的文档"""
    reset_knowledge_base()
    # 清空 data 目录
    if os.path.exists(DATA_DIR):
        shutil.rmtree(DATA_DIR)
        Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
    return {"message": "知识库已清空，所有文档和索引已删除。"}

@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    """用户提问，返回答案与来源"""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")
    answer, sources = answer_question(req.question)
    return AskResponse(answer=answer, sources=sources)

# --------------------- 直接运行入口 ---------------------
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)