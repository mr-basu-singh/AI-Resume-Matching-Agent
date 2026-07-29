import faiss
import numpy as np
import os
import pickle

from src.vectorstore.embeddings import get_embedding

# -----------------------------
# CONFIG
# -----------------------------
DIM = 384

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../data/faiss_index")
)

INDEX_PATH = os.path.join(BASE_DIR, "index.faiss")
META_PATH = os.path.join(BASE_DIR, "meta.pkl")

os.makedirs(BASE_DIR, exist_ok=True)

# -----------------------------
# INIT
# -----------------------------
metadata_store = []

if os.path.exists(INDEX_PATH):
    index = faiss.read_index(INDEX_PATH)
    print("FAISS index loaded")
else:
    index = faiss.IndexFlatL2(DIM)
    print("New FAISS index created")


# -----------------------------
# LOAD META
# -----------------------------
if os.path.exists(META_PATH):
    with open(META_PATH, "rb") as f:
        metadata_store = pickle.load(f)


# -----------------------------
# SAVE INDEX + META
# -----------------------------
def save_all():
    faiss.write_index(index, INDEX_PATH)

    with open(META_PATH, "wb") as f:
        pickle.dump(metadata_store, f)


# -----------------------------
# RESET INDEX
# -----------------------------
def reset_index():
    """
    Clears the FAISS index and metadata store.

    Each screening run in this app uploads a fresh, unrelated batch
    of resumes for a fresh JD. Without a reset, resumes from a
    previous, unrelated run stayed in the index forever and kept
    getting surfaced as "similar resume" RAG context for later runs.
    Call this at the start of each run before indexing the current
    batch of uploaded resumes.
    """
    global index, metadata_store

    index = faiss.IndexFlatL2(DIM)
    metadata_store = []

    save_all()


# -----------------------------
# ADD DOCUMENT (IMPROVED)
# -----------------------------
def add_document(text: str, meta: dict):
    """
    Store BOTH:
    - embedding (FAISS)
    - full text (for RAG context)
    """

    global index, metadata_store

    vector = np.array([get_embedding(text)]).astype("float32")

    index.add(vector)

    metadata_store.append({
        "text": text,
        "name": meta.get("name", "unknown")
    })

    save_all()


# -----------------------------
# SEARCH (IMPROVED RAG OUTPUT)
# -----------------------------
def search(query: str, k: int = 3):
    if index.ntotal == 0:
        return []

    query_vec = np.array([get_embedding(query)]).astype("float32")

    distances, indices = index.search(query_vec, k)

    results = []

    for i, dist in zip(indices[0], distances[0]):

        if 0 <= i < len(metadata_store):

            item = metadata_store[i]

            results.append({
                "name": item["name"],
                "text": item["text"][:500],
                "score": float(dist)
            })

    return results
