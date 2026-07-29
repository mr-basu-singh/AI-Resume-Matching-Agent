from src.llm.llm_config import get_llm
from src.models.schema import ParsedResume


RESUME_EXTRACTION_PROMPT = """
You are an expert resume screener. Read the resume text below and extract structured
information about the candidate. Be strict and literal - only extract what is actually
written in the resume, do not assume or invent information.

Rules:
- candidate_skills: list every technical/professional skill mentioned ANYWHERE in the
  resume - not just under a dedicated "Skills" header. Many candidates only mention a
  tool or technology inside a project bullet or job description (e.g. "built a REST API
  using FastAPI and deployed it with Docker") without repeating it in a formal skills
  section. Scan the summary, the skills section, every project description, every work
  experience bullet, and certifications for any tool, technology, framework, language,
  or competency mentioned, and include ALL of them here - do not limit yourself to what's
  under a formal "Skills:" heading.
- total_experience_months: count ONLY real professional/work experience (internships
  count). Coursework, personal/academic projects, and certifications are NOT work
  experience. If the resume shows no professional work history at all (e.g. a fresher
  or student resume with no internship/job), use 0.
- education_field / education_level: based on the highest degree mentioned.
- projects: for EACH project, write a substantive one-to-two sentence description that
  captures what it actually does, the key techniques/methods used, and the technologies
  involved - pull this from the resume's bullet points under that project, not just the
  project's title. A bare title like "AIForge: AI Evaluation Platform" is NOT enough;
  write something like "AIForge: AI Evaluation & Agent Testing Platform - built a
  benchmarking system evaluating 4 LLMs using LLM-as-a-Judge metrics and a hallucination
  detection system, validated with a unit test suite." This detail is what a later step
  uses to judge whether the candidate has specific skills, so do not compress it away.

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
