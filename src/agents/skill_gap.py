from src.llm.llm_config import get_llm

def skill_gap_analyzer(resume_text: str, jd_text: str) -> str:
    llm = get_llm()

    prompt = f"""
You are a hiring assistant.

Compare resume and job description.

Return ONLY:

Missing Skills:
- ...

Recommended Skills to Learn:
- ...

Resume:
{resume_text}

Job Description:
{jd_text}
"""

    response = llm.invoke(prompt)
    return response.content