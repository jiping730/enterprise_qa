企业多知识库智能问答平台

基于私有文档的企业级问答系统。支持多知识库隔离、用户权限管理、在线文档维护、对话历史记忆，并使用 MySQL 持久化查询日志。完全本地运行，适合中小团队内部知识管理。

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688)
![LangChain](https://img.shields.io/badge/LangChain-0.2.16-green)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1)
![license](https://img.shields.io/badge/license-MIT-lightgrey)

## 功能亮点

- **多知识库管理**：创建多个独立知识库，不同知识库数据与索引完全隔离。

- **用户认证与权限**：JWT 登录/注册，知识库所有者可授权其他用户访问。

- **文档在线管理**：支持 PDF、TXT、DOCX 多文件上传，拖拽添加，点击"开始分析"处理，支持文档删除。

- **智能问答**：基于文档片段检索 + GLM-4-Flash 生成答案，回答附带来源（文档名、页码/全文标记、相似度分数）。

- **置信度展示**：根据检索相似度自动给出可信度说明（✅/⚠️/❓）。

- **多轮对话**：同一会话内上下文记忆，支持连续追问。

- **查询日志**：每次问答自动记录到 MySQL，包含用户、问题、时间、答案摘要。

- **现代界面**：侧边栏 + 工作区布局，聊天式问答，拖拽上传，回车发送，按钮状态禁用。

## 技术栈

| 层级 | 技术选型 |
|------|----------|
| 后端框架 | FastAPI |
| 数据库 | MySQL 8.0+ (SQLAlchemy ORM) |
| 认证 | JWT (python-jose + passlib) |
| 大模型 | 智谱 GLM-4-Flash (OpenAI 兼容接口) |
| 嵌入模型 | BAAI/bge-small-zh-v1.5 (本地) |
| 向量库 | FAISS (CPU) |
| 编排框架 | LangChain |
| 前端 | 原生 HTML/CSS/JS (SPA) |

## 项目结构

```
enterprise_qa/
├── app/                    # 后端核心代码
│   ├── config.py           # 配置项（数据库、模型、密钥）
│   ├── database.py         # MySQL 连接与初始化
│   ├── models_db.py        # ORM 模型（用户、知识库、文档、日志）
│   ├── models_api.py       # Pydantic 接口模型
│   ├── auth.py             # 密码哈希、JWT 工具、权限依赖
│   ├── document_loader.py  # 文档加载与智能分块
│   ├── vector_store.py     # 多知识库向量索引、检索、删除
│   ├── qa_chain.py         # 检索+LLM 生成+置信度+日志记录
│   └── main.py             # FastAPI 主路由与静态文件服务
├── static/                 # 前端静态文件
│   ├── login.html          # 登录/注册页
│   ├── index.html          # 主界面（知识库列表、文档管理、聊天）
│   ├── css/
│   │   └── style.css       # 全局样式
│   └── js/
│       ├── api.js          # 请求封装（自动带 JWT）
│       ├── auth.js         # 登录/注册逻辑
│       └── main.js         # 主界面交互逻辑
├── data/                   # 用户上传文档保存目录（按 kb 分目录）
├── faiss_index/            # FAISS 向量索引保存目录（按 kb 分目录）
├── requirements.txt        # Python 依赖包列表
├── .env.example            # 环境变量模板
└── README.md               # 本文件
```

## 环境搭建与运行

### 前置要求

- Python 3.10+（推荐 3.12）
- MySQL 8.0+ 已安装并运行
- 智谱 API Key（从 [智谱开放平台](https://open.bigmodel.cn/) 免费申请）
- Git（可选，用于克隆代码）

### 1. 克隆项目

```bash
git clone https://github.com/jiping730/enterprise_qa.git
cd enterprise_qa
```

### 2. 创建 MySQL 数据库

登录 MySQL，执行以下 SQL（请修改密码）：

```sql
CREATE DATABASE enterprise_qa CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'qa_user'@'localhost' IDENTIFIED BY '你的数据库密码';
GRANT ALL PRIVILEGES ON enterprise_qa.* TO 'qa_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 创建虚拟环境并激活

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

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

若遇到 greenlet 编译错误，先执行：

```bash
pip install greenlet --only-binary=:all:
```

### 5. 配置环境变量

复制模板并编辑：

```bash
cp .env.example .env
```

打开 `.env` 文件，填写以下信息：

```text
ZHIPU_API_KEY=你的智谱 API Key
DB_USER=qa_user
DB_PASSWORD=你的数据库密码
DB_HOST=localhost
DB_PORT=3306
DB_NAME=enterprise_qa
SECRET_KEY=请生成一个随机长字符串用于JWT加密
```

### 6. 初始化数据库表并启动服务

```bash
python app/main.py
```

首次运行会自动创建所有 MySQL 表（ORM 的 Base.metadata.create_all）。终端输出：

```text
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 7. 访问系统

浏览器打开 http://localhost:8000，自动跳转到登录页。

### 8. 开始使用

- **注册账号**：点击"立即注册"，输入用户名和密码。
- **登录**：使用注册的账号登录。
- **创建知识库**：在左侧输入知识库名称，点击"创建"。
- **上传文档**：进入知识库，拖拽或点击上传区域选择文件（可多选），点击"开始分析"。
- **提问**：在输入框输入问题，按回车或点击发送，系统给出带来源和置信度的答案。
- **权限管理**：知识库所有者可以通过授权按钮将知识库共享给其他用户。

## 常用命令

- 启动服务：`python app/main.py`
- 后台运行（Linux/macOS）：`nohup python app/main.py &`
- 更换端口：修改 `app/main.py` 底部的 `port=8000` 或直接使用 `uvicorn app.main:app --port 9000`
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

A: 项目已配置 HuggingFace 国内镜像（hf-mirror.com），会自动从镜像下载。若仍失败，可手动下载模型到本地，并修改 `app/config.py` 中的 `EMBEDDING_MODEL` 为模型绝对路径。

**Q: 上传文件后提问提示"请先上传文档"？**

A: 检查 `.env` 中的 ZHIPU_API_KEY 是否正确；检查终端是否有报错；可执行诊断脚本 diagnose_final.py 查看索引状态。

**Q: 如何切换为大模型？**

A: 修改 `app/config.py` 中 `EMBEDDING_MODEL = "BAAI/bge-large-zh-v1.5"`，重启服务（首次下载约 1.3GB）。

**Q: 支持 GPU 加速吗？**

A: 支持。安装 CUDA 版本的 PyTorch，并将 `app/vector_store.py` 中的 `model_kwargs={"device": "cuda"}`。

**Q: 查询日志存储在哪里？**

A: 存储在 MySQL 的 `query_logs` 表中，可用 Navicat 或 phpMyAdmin 查看。

## 贡献与致谢

本项目基于 LangChain、FastAPI、FAISS 等开源框架构建。

嵌入模型由 BAAI 提供（bge-small-zh-v1.5）。

大语言模型由智谱 AI 提供（GLM-4-Flash）。

欢迎提交 Issue 或 Pull Request。

## 许可证

本项目基于 MIT 许可证开源。详见 LICENSE 文件。