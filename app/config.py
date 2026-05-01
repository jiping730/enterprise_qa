import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 项目根目录（app/config.py 的上两级）
BASE_DIR = Path(__file__).resolve().parent.parent

ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")
if not ZHIPU_API_KEY:
    raise ValueError("请在 .env 文件中设置 ZHIPU_API_KEY")

EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"   # 或你实际使用的模型
LLM_MODEL = "glm-4-flash"
LLM_API_BASE = "https://open.bigmodel.cn/api/paas/v4/"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 4

# 改为绝对路径
DATA_DIR = str(BASE_DIR / "data")
INDEX_DIR = str(BASE_DIR / "faiss_index")