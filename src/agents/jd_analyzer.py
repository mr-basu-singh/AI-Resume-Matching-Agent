from src.llm.llm_config import get_llm
from src.models.schema import JDRequirements


JD_EXTRACTION_PROMPT = """
You are an expert technical recruiter. Read the job description / role details below,
written by HR, and extract exactly what this role needs from a candidate.

Be precise:
- required_skills should only include skills clearly mandatory for the role.
- preferred_skills are explicitly "nice to have" / "bonus" / "plus" skills.
- required_experience_years: if the JD says things like "freshers welcome", "0-1 years",
  or doesn't mention experience at all, use 0. If it says "at least 1 year" use 1,
  "2-3 years" use 2, etc.
- required_education_field / required_education_level: leave as empty string "" if the JD
  does not specify a field or level.

Job Description / Role Details:
{jd_text}
"""


def _empty_requirements(summary: str) -> JDRequirements:
    return JDRequirements(
        role_title="Unknown Role",
        required_skills=[],
        preferred_skills=[],
        required_experience_years=0,
        required_education_field="",
        required_education_level="",
        key_requirements_summary=summary,
    )


def analyze_jd(jd_text: str) -> JDRequirements:
    if not jd_text or not jd_text.strip():
        return _empty_requirements("No job description was provided.")

    llm = get_llm()
    structured_llm = llm.with_structured_output(JDRequirements)
    prompt = JD_EXTRACTION_PROMPT.format(jd_text=jd_text[:8000])

    try:
        return structured_llm.invoke(prompt)
    except Exception as e:
        # Don't let one LLM/API hiccup crash the whole batch run
        return _empty_requirements(f"JD analysis failed: {e}")
