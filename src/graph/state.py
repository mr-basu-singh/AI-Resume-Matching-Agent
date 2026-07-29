from typing import TypedDict, List, Dict, Any


class ResumeState(TypedDict):
    job_description: str
    resumes: List[str]

    parsed_resumes: List[dict]
    jd_analysis: Dict[str, Any]
    rag_context: str

    embeddings: List[List[float]]
    vector_results: List[dict]

    scores: List