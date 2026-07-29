from src.vectorstore.faiss_store import add_document, search


def index_resumes(resumes: list):
    for i, r in enumerate(resumes):
        add_document(r, {"id": i})


def rag_match(job_description: str):
    return search(job_description, k=5)