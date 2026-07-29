from src.llm.llm_config import get_llm
from src.prompts.prompts import JD_ANALYZER_PROMPT

def analyze_jd(jd_text: str) -> str:
    if not jd_text or not jd_text.strip():
        return "No job description text was provided."

    llm = get_llm()
    prompt = JD_ANALYZER_PROMPT.format(jd_text=jd_text)

    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        # Don't let one LLM/API hiccup crash the whole batch run
        return f"JD analysis failed: {e}"
