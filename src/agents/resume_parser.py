from src.llm.llm_config import get_llm
from src.prompts.prompts import RESUME_PARSER_PROMPT

def parse_resume(resume_text: str) -> str:
    if not resume_text or not resume_text.strip():
        return "No resume text could be extracted from this file."

    llm = get_llm()
    pro