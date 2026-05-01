from app.config import INDEX_DIR
from app.vector_store import load_vector_store

print(f"INDEX_DIR（绝对路径）: {INDEX_DIR}")
store = load_vector_store()
if store:
    print(f"✅ 索引加载成功，向量数: {store.index.ntotal}")
    # 显示文档源
    sources = {}
    for doc_id, doc in store.docstore._dict.items():
        src = doc.metadata.get("source", "未知")
        sources[src] = sources.get(src, 0) + 1
    for src, cnt in sources.items():
        print(f"  {src}  ({cnt} 片段)")
else:
    print("❌ 索引仍不存在，请检查上传日志。")