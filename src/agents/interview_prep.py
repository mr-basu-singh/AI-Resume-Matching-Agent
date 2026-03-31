from src.llm.llm_config import get_llm

def generate_interview_questions(job_role: str) -> str:
    llm = get_llm()

    prompt = f"""
    You are an interview preparation assistant.

    Generate 10 interview questions for the role: {job_role}

    Include:
    1. Technical questions
    2. HR questions
    3. Project-based questions
    """

    response = llm.invoke(prompt)
    return response.content