from src.llm.llm_config import get_llm
from src.models.schema import ParsedResume


RESUME_EXTRACTION_PROMPT = """
You are an expert resume screener. Read the resume text below and extract structured
information about the candidate. Be strict and literal - only extract what is actually
written in the resume, do not assume or invent information.

Rules:
- candidate_skills: list every technical/professional skill actually mentioned.
- total_experience_months: count ONLY real professional/work experience (internships
  count). Coursework, personal/academic projects, and certifications are NOT work
  experience. If the resume shows no professional work history at all (e.g. a fresher
  or student resume with no internship/job), use 0.
- education_field / education_level: based on the highest degree mentioned.

Resume:
{resume_text}
"""


def _empty_resume(summary: str) -> ParsedResume:
    return ParsedResume(
        candidate_skills=[],
        total_experience_months=0,
        experience_summary=summary,
        education_field="",
        education_level="",
        education_details="",
        projects=[],
    )


def parse_resume(resume_text: str) -> ParsedResume:
    if not resume_text or not resume_text.strip():
        return _empty_resume("No resume text could be extracted from this file.")

    llm = get_llm()
    structured_llm = llm.with_structured_output(ParsedResume)
    prompt = RESUME_EXTRACTION_PROMPT.format(resume_text=resume_text[:8000])

    try:
        return structured_llm.invoke(prompt)
    except Exception as e:
        # Don't let one LLM/API hiccup crash the whole batch run
        return _empty_resume(f"Resume parsing failed: {e}")
