from src.llm.llm_config import get_llm
from src.prompts.prompts import JD_ANALYZER_PROMPT

def analyze_jd(jd_text: str) -> str:
    llm = get_llm()
    prompt = JD_ANALYZER_PROMPT.format(jd_text=jd_text)
    response = llm.invoke(prompt)
    return response.content