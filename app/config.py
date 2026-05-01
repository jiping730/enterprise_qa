import os
from dotenv import load_dotenv

load_dotenv()

# 项目根目录
import pathlib
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent

# 智谱 API
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")
if not ZHIPU_API_KEY:
    raise ValueError("请在 .env 文件中设置 ZHIPU_API_KEY")

# 嵌入模型
EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"

# LLM
LLM_MODEL = "glm-4-flash"
LLM_API_BASE = "https://open.bigmodel.cn/api/paas/v4/"

# 文本分割
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 4

# MySQL 数据库配置
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "enterprise_qa")
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# JWT 密钥（生产环境务必更换）
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")

# 存储目录（文档统一放在 data 下，按知识库分目录）
DATA_DIR = str(BASE_DIR / "data")
INDEX_DIR = str(BASE_DIR / "faiss_index")