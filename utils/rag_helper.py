import os

KNOWLEDGE_BASE_PATH = "./knowledge/"

async def get_rag_knowledge(doc_name: str):
    """读取知识库md文件，简易RAG，后续可替换成向量检索"""
    doc_path = os.path.join(KNOWLEDGE_BASE_PATH, doc_name)
    if not os.path.exists(doc_path):
        return "暂无知识库规则"
    with open(doc_path, "r", encoding="utf-8") as f:
        return f.read()
