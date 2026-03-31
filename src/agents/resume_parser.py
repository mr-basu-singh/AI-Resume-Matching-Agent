from src.llm.llm_config import get_llm
from src.prompts.prompts import RESUME_PARSER_PROMPT

def parse_resume(resume_text: str) -> str:
    llm = get_llm()
    prompt = RESUME_PARSER_PROMPT.format(resume_text=resume_text)
    response = llm.invoke(prompt)
    return response.content