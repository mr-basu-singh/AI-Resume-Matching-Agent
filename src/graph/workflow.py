from langgraph.graph import StateGraph, END

from src.agents.resume_parser import parse_resume
from src.agents.jd_analyzer import analyze_jd
from src.agents.llm_scorer import score_candidate_with_llm
from src.agents.ranker import rank_candidates

# ✅ RAG (BEST RETRIEVER)
from src.vectorstore.retriever import retrieve_llm_context
from src.vectorstore.faiss_store import reset_index, add_document


# ======================================================
# NODE 1: PARSE RESUMES
# ======================================================
def parse_node(state):
    parsed_resumes = []

    for r in state["resumes"]:

        if isinstance(r, dict):
            parsed = parse_resume(r["text"])
        else:
            parsed = parse_resume(r)

        parsed_resumes.append(parsed)

    state["parsed_resumes"] = parsed_resumes
    return state


# ======================================================
# NODE 2: JD ANALYSIS
# ======================================================
def jd_node(state):
    state["jd_analysis"] = analyze_jd(state["job_description"])
    return state


# ======================================================
# NODE 3: INDEX CURRENT RESUME BATCH INTO FAISS
# ======================================================
def index_node(state):
    """
    Previously nothing ever added the currently uploaded resumes to the
    FAISS index before rag_node searched it - so RAG context either came
    back empty (fresh install) or was stale/unrelated resumes left over
    from a completely different screening run.

    Each screening run here is a self-contained batch (one JD + one set
    of uploaded resumes), so we reset the index and index just this
    batch, giving the RAG step real, relevant "similar resume" context
    to work with, without leaking data across unrelated runs.
    """

    reset_index()

    for r in state["resumes"]:

        if isinstance(r, dict):
            text = r["text"]
            name = r.get("name", "unknown")
        else:
            text = r
            name = "unknown_resume.pdf"

        if text and text.strip():
            add_document(text, {"name": name})

    return state


# ======================================================
# NODE 4: RAG CONTEXT GENERATION
# ======================================================
def rag_node(state):
    """
    Uses FAISS + embeddings to fetch similar resumes context
    """

    state["rag_context"] = retrieve_llm_context(
        state["job_description"],
        k=3
    )

    return state


# ======================================================
# NODE 5: SCORING (LLM, using parsed resume + JD analysis + RAG context)
# ======================================================
def scoring_node(state):
    """
    Previously this ignored parsed_resumes/jd_analysis/rag_context and
    scored with the same plain keyword-overlap function as the rule-based
    "Old System" mode - so the two modes produced effectively identical
    results. Now it actually uses the LLM with the enriched context.
    """

    scores = []

    parsed_resumes = state.get("parsed_resumes", [])
    jd_analysis = state.get("jd_analysis", "")
    rag_context = state.get("rag_context", "")

    for i, r in enumerate(state["resumes"]):

        # -----------------------------
        # Handle structured / unstructured input
        # -----------------------------
        if isinstance(r, dict):
            resume_text = r["text"]
            file_name = r["name"]
        else:
     