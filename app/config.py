import os
from dotenv import load_dotenv

load_dotenv()

# 从环境变量读取智谱 API Key（必须配置）
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")
if not ZHIPU_API_KEY:
    raise ValueError("请在 .env 文件中设置 ZHIPU_API_KEY")

# 嵌入模型（本地运行，首次自动下载）
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"

# 大语言模型
LLM_MODEL = "glm-4-flash"
LLM_API_BASE = "https://open.bigmodel.cn/api/paas/v4/"

# 文本分割参数
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

# 检索返回片段数
TOP_K = 4

# 存储路径
DATA_DIR = "data"
INDEX_DIR = "faiss_index"