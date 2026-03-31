from src.llm.llm_config import get_llm
from src.prompts.prompts import MATCHER_PROMPT

def match_resume_to_jd(resume_data: str, jd_data: str) -> str:
    llm = get_llm()
    prompt = MATCHER_PROMPT.format(
        resume_data=resume_data,
        jd_data=jd_data
    )
    response = llm.invoke(prompt)
    return response.content