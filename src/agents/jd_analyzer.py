from src.llm.llm_config import get_llm
from src.prompts.prompts import JD_ANALYZER_PROMPT

def analyze_jd(jd_text: str) -> str:
    if not jd_text or not jd_text.strip():
        return "No job description text was provided."

    llm = get_llm()
    prompt = JD_A