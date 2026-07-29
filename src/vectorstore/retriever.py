from src.vectorstore.faiss_store import search


# -----------------------------
# MAIN RETRIEVER FUNCTION
# -----------------------------
def retrieve_context(query: str, k: int = 3):
    """
    Retrieves top-k similar resumes/contexts from FAISS
    and formats them into LLM-friendly structured context.
    """

    results = search(query, k)

    if not results:
        return "No relevant context found from vector database."

    formatted_chunks = []

    for i, r in enumerate(results, start=1):

        name = r.get("name", "unknown")
        text = r.get("text", "")
        score = r.get("score", 0.0)

        chunk = f"""
========================
📌 MATCH {i}
========================

👤 Candidate/File: {name}
📊 Similarity Score: {round(score, 4)}

🧠 Extracted Resume Context:
{text}

------------------------
"""

        formatted_chunks.append(chunk)

    return "\n".join(formatted_chunks)


# -----------------------------
# ADVANCED RETRIEVAL (OPTIONAL USE)
# -----------------------------
def retrieve_context_with_scores(query: str, k: int = 3):
    """
    Returns structured JSON-like output for advanced pipelines.
    Useful for debugging or ranking improvements.
    """

    results = search(query, k)

    structured = []

    for r in results:
        structured.append({
            "candidate_name": r.get("name", "unknown"),
            "similarity_score": r.get("score", 0.0),
            "resume_snippet": r.get("text", "")
        })

    return structured


# -----------------------------
# CLEAN CONTEXT FOR LLM (BEST OPTION)
# -----------------------------
def retrieve_llm_context(query: str, k: int = 3):
    """
    BEST function for LangGraph + LLM scoring.
    Returns compact, clean prompt-ready context.
    """

    results = search(query, k)

    if not results:
        return ""

    context = []

    for r in results:

        context.append(
            f"""
Candidate: {r.get('name', 'unknown')}
Score: {round(r.get('score', 4), 4)}

Skills/Content:
{r.get('text', '')}
"""
        )

    return "\n".join(context)