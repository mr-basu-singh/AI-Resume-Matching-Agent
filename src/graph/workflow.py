from langgraph.graph import StateGraph, END

from src.agents.resume_parser import parse_resume
from src.agents.jd_analyzer import analyze_jd
from src.agents.section_scorer import score_candidate
from src.agents.ranker import rank_candidates


# ======================================================
# NODE 1: PARSE RESUMES (structured: skills, experience
# months, education, projects)
# ======================================================
def parse_node(state):
    parsed_resumes = []

    for r in state["resumes"]:
        text = r["text"] if isinstance(r, dict) else r
        parsed_resumes.append(parse_resume(text))

    state["parsed_resumes"] = parsed_resumes
    return state


# ======================================================
# NODE 2: JD ANALYSIS (structured: required/preferred
# skills, required experience, required education)
# ======================================================
def jd_node(state):
    state["jd_requirements"] = analyze_jd(state["job_description"])
    return state


# ======================================================
# NODE 3: SCORE EACH CANDIDATE SECTION BY SECTION
# (skill + experience computed deterministically,
# project + education scored by the LLM with a rubric)
# ======================================================
def scoring_node(state):
    scores = []

    jd_requirements = state["jd_requirements"]
    parsed_resumes = state.get("parsed_resumes", [])

    for i, r in enumerate(state["resumes"]):
        file_name = r["name"] if isinstance(r, dict) else "unknown_resume.pdf"
        parsed_resume = parsed_resumes[i] if i < len(parsed_resumes) else None

        if parsed_resume is None:
            continue

        result = score_candidate(jd_requirements, parsed_resume, file_name)
        scores.append(result)

    state["scores"] = scores
    return state


# ======================================================
# NODE 4: RANK CANDIDATES HIGHEST TO LOWEST
# ======================================================
def ranking_node(state):
    state["ranked"] = rank_candidates(state["scores"])
    return state


# ======================================================
# BUILD LANGGRAPH WORKFLOW
# ======================================================
graph = StateGraph(dict)

graph.add_node("parse", parse_node)
graph.add_node("jd", jd_node)
graph.add_node("score", scoring_node)
graph.add_node("rank", ranking_node)

graph.set_entry_point("parse")

graph.add_edge("parse", "jd")
graph.add_edge("jd", "score")
graph.add_edge("score", "rank")
graph.add_edge("rank", END)

app = graph.compile()
