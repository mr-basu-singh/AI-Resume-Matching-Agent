from langgraph.graph import StateGraph, END

from src.agents.resume_parser import parse_resume
from src.agents.jd_analyzer import analyze_jd
from src.agents.llm_scorer import score_candidate_with_llm
from src.agents.ranker import rank_candidates

# RAG (BEST RETRIEVER)
from src.vectorstore.retriever import retrieve_llm_context
from src.vectorstore.faiss_store import reset_index, add_document


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


def jd_node(state):
    state["jd_analysis"] = analyze_jd(state["job_description"])
    return state


def index_node(state):
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


def rag_node(state):
    state["rag_context"] = retrieve_llm_context(
        state["job_description"],
        k=3
    )

    return state


def scoring_node(state):
    scores = []

    parsed_resumes = state.get("parsed_resumes", [])
    jd_analysis = state.get("jd_analysis", "")
    rag_context = state.get("rag_context", "")

    for i, r in enumerate(state["resumes"]):

        if isinstance(r, dict):
            resume_text = r["text"]
            file_name = r["name"]
        else:
            resume_text = r
            file_name = "unknown_resume.pdf"

        parsed_resume = parsed_resumes[i] if i < len(parsed_resumes) else ""

        result = score_candidate_with_llm(
            resume_text=resume_text,
            parsed_resume=parsed_resume,
            jd_analysis=jd_analysis,
            rag_context=rag_context,
            file_name=file_name,
        )

        scores.append(result)

    state["scores"] = scores
    return state


def ranking_node(state):
    state["ranked"] = rank_candidates(state["scores"])
    return state


graph = StateGraph(dict)

graph.add_node("parse", parse_node)
graph.add_node("jd", jd_node)
graph.add_node("index", index_node)
graph.add_node("rag", rag_node)
graph.add_node("score", scoring_node)
graph.add_node("rank", ranking_node)

graph.set_entry_point("parse")

graph.add_edge("parse", "jd")
graph.add_edge("jd", "index")
graph.add_edge("index", "rag")
graph.add_edge("rag", "score")
graph.add_edge("score", "rank")
graph.add_edge("rank", END)

app = graph.compile()
