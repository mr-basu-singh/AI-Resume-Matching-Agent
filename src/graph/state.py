from typing import TypedDict, List, Any


class ResumeState(TypedDict):
    job_description: str
    resumes: List[Any]  # each item: str, or {"name": str, "text": str}

    parsed_resumes: List[Any]  # List[ParsedResume]
    jd_requirements: Any        # JDRequirements

    scores: List[dict]
    ranked: Any                 # pandas DataFrame
