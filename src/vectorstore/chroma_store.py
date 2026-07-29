import chromadb

client = chromadb.PersistentClient(path="data/chroma_db")
collection = client.get_or_create_collection("resumes")


def add_to_chroma(doc_id, text, embedding):
    collection.add(
        ids=[doc_id],
        documents=[text],
        embeddings=[embedding]
    )


def search_chroma(query_embedding, k=3):
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k
    )
    return results