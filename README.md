企业文档智能问答助手

基于私有文档的本地智能问答系统。上传 PDF、TXT、DOCX 文件，使用自然语言提问，系统自动检索文档片段并生成带来源标注的答案。支持多文档选择、置信度评估、多轮对话记忆。完全本地运行，适合企业内部知识库场景。

![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.2.16-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688)
![license](https://img.shields.io/badge/license-MIT-lightgrey)

## 功能亮点

- **多格式文档解析**：支持 PDF、TXT、DOCX 三种常见企业文档格式。

- **智能分块与向量化**：采用中文友好的文本分割策略，使用 BGE 中文嵌入模型，将文档片段存入本地 FAISS 向量数据库。

- **自然语言问答**：输入问题后，自动检索最相关的文档片段，并交由大模型生成最终答案。

- **来源透明标注**：回答中明确指出引用自哪个文档的哪一页，并显示参考片段的原文（前 200 字）。

- **多文档筛选**：可选择只从特定文档中检索，支持全选/反选，适应多文件场景。

- **答案置信度说明**：根据检索相似度自动给出答案可信度提示（✅ 高度相关 / ⚠️ 部分相关 / ❓ 推断等）。

- **多轮对话记忆**：基于会话 ID 保持上下文，支持连续追问，记忆最近 20 轮对话。

- **前后端分离的现代界面**：独立静态资源，聊天式交互，支持拖拽上传、键盘发送、加载动画。

## 项目结构

```
enterprise_qa/
├── app/                    # 后端核心代码
│   ├── __init__.py
│   ├── config.py           # 所有配置项（路径、模型、API Key）
│   ├── models.py           # Pydantic 请求/响应模型
│   ├── document_loader.py  # 文档加载与智能分块
│   ├── vector_store.py     # 向量化、FAISS 存储及检索
│   ├── qa_chain.py         # 问答链：检索+LLM 生成+置信度
│   └── main.py             # FastAPI 主程序，挂载 API 和静态文件
├── static/                 # 前端静态文件
│   ├── index.html          # 聊天式 UI 主页面
│   ├── css/
│   │   └── style.css       # 现代化样式
│   └── js/
│       └── app.js          # 前端交互逻辑
├── data/                   # 用户上传的文档保存目录（自动创建）
├── faiss_index/            # FAISS 向量索引持久化目录（自动创建）
├── requirements.txt        # Python 依赖包列表
├── .env.example            # 环境变量模板
├── .gitignore
└── README.md               # 本文件
```

## 技术栈

- **编程语言**：Python 3.12

- **Web 框架**：FastAPI

- **大语言模型**：智谱 GLM-4-Flash（通过 OpenAI 兼容接口调用）

- **文档解析**：PyPDF2 (pypdf)、docx2txt、Unstructured（可选）

- **向量模型**：BAAI/bge-small-zh-v1.5（默认，95MB，速度快；可配置为 large 版本）

- **向量数据库**：FAISS（CPU 版本）

- **编排框架**：LangChain / LangGraph

## 环境搭建与运行

### 前置要求

- Python 3.10 及以上（推荐 3.12）
- Git
- 智谱 API Key（从 [智谱开放平台](https://open.bigmodel.cn/) 免费申请）

### 1. 克隆项目

```bash
git clone https://github.com/jiping730/enterprise_qa.git
cd enterprise_qa
```

### 2. 创建虚拟环境并激活

**Windows**

```powershell
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

若遇到 greenlet 编译报错，请尝试：

```bash
pip install greenlet --only-binary=:all:
```

### 4. 配置 API Key

复制环境变量模板并修改：

```bash
cp .env.example .env
```

编辑 `.env` 文件，将 `your_api_key_here` 替换为你的智谱 API Key：

```text
ZHIPU_API_KEY=你的真实key
```

### 5. 启动服务

```bash
python app/main.py
```

服务启动后，终端会显示：

```text
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 6. 访问系统

打开浏览器，访问 http://localhost:8000，你将看到聊天式交互界面。

### 7. 开始使用

- **上传文档**：点击"📁 文档管理"展开上传区域，拖拽或选择 PDF/TXT/DOCX 文件，点击"上传并处理"。
- **提问**：在聊天输入框中输入问题，回车或点击发送。
- **限定文档（可选）**：在"📌 限定检索文档"区域勾选需要搜索的文档，未勾选则检索全部。
- **连续对话**：直接继续提问，系统会记住对话上下文。
- **清空知识库**：点击"⚠️ 清空知识库"可删除所有文档和索引。

## 常用命令

- 启动服务：`python app/main.py`
- 后台运行（Linux/macOS）：`nohup python app/main.py &`
- 指定端口：修改 `app/main.py` 底部的 `port=8000` 或直接用 `uvicorn app.main:app --port 9000`
- 查看已安装包：`pip list`

## 自定义配置

编辑 `app/config.py` 可调整以下参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| EMBEDDING_MODEL | 嵌入模型名称 | BAAI/bge-small-zh-v1.5 |
| LLM_MODEL | 大语言模型 | glm-4-flash |
| CHUNK_SIZE | 文本分块大小 | 500 |
| CHUNK_OVERLAP | 分块重叠长度 | 50 |
| TOP_K | 检索返回的片段数 | 4 |
| DATA_DIR | 文档存储目录 | data |
| INDEX_DIR | 向量索引目录 | faiss_index |

## 常见问题

**Q: 首次运行时下载模型很慢或超时？**

A: 项目已内置 HuggingFace 镜像（hf-mirror.com）。如果仍然失败，可手动下载模型并放置在本地路径，然后修改 `app/config.py` 中的 `EMBEDDING_MODEL` 为模型绝对路径。

**Q: 上传文件后提问提示"请先上传文档"？**

A: 检查 `.env` 中的 API Key 是否正确；检查终端是否有报错；执行 `python diagnose_final.py` 查看索引状态。

**Q: 如何切换嵌入模型为 large 版本？**

A: 修改 `app/config.py` 中 `EMBEDDING_MODEL = "BAAI/bge-large-zh-v1.5"`，重启服务即可（首次需下载约 1.3GB 模型）。

**Q: 如何重置知识库？**

A: 点击前端"清空知识库"按钮，或者手动删除 `faiss_index` 和 `data` 文件夹后重启。

**Q: 多轮对话记忆能保存多久？**

A: 当前版本对话记忆保存在内存中，服务重启后历史会丢失。如有持久化需求，可简单改造为 Redis 存储。

**Q: 支持 GPU 加速吗？**

A: 支持。安装 CUDA 版本的 PyTorch，并修改 `app/vector_store.py` 中 `model_kwargs={"device": "cuda"}`。

## 贡献与致谢

本项目基于 LangChain、FastAPI、FAISS 等优秀开源框架构建。

嵌入模型由 BAAI 提供（bge-small-zh-v1.5）。

大语言模型由智谱 AI 提供（GLM-4-Flash）。

欢迎提交 Issue 或 Pull Request。

## 许可证

本项目基于 MIT 许可证开源。详见 LICENSE 文件。