"""
LLM-based candidate scorer for the LangGraph + RAG pipeline.

Previously, the "LangGraph + RAG (AI System)" mode in the UI ran the
parse/JD-analysis/RAG nodes, then silently threw their output away and
scored candidates with the same plain keyword-overlap function used by
the "Old System (Rule Based)" mode. This module is the real fix: it
uses the LLM, with the parsed resume + JD analysis + RAG context, and
returns a structured, schema-validated score via CandidateScore.
"""

from src.llm.llm_config import get_llm
from src.models.schema import CandidateScore


SCORING_PROMPT = """
You are an expert technical recruiter scoring ONE candidate resume against a job description.

Be strict and well-calibrated. Do not inflate scores:
- If the resume shows no real professional work experience (no employer, no dates, no role
  responsibilities - e.g. a fresher/student resume, or an empty "Experience" section), experience_score
  MUST be 0.
- Only count a skill as "matched" if it is clearly present in the candidate's resume, not just
  because it appears in the job description.
- final_score should be a realistic weighted combination of the sub-scores, not just an average.

========================
JOB DESCRIPTION ANALYSIS
========================
{jd_analysis}

========================
RAG CONTEXT (similar resumes retrieved for calibration only - this is NOT the candidate being
scored, use it only to judge relative skill/experience level)
========================
{rag_context}

========================
CANDIDATE'S PARSED RESUME (structured extraction)
========================
{parsed_resume}

========================
CANDIDATE'S RAW RESUME TEXT
========================
{resume_text}

Score the candidate:
- skill_score (0-100): overlap between resume skills and JD required/preferred skills
- experience_score (0-100): 0 if no real work experience is evidenced, otherwise scaled to years/seniority shown
- project_score (0-100): quality/relevance of projects shown
- education_score (0-100): relevance of education to the role
- final_score (0-100): overall fit, weighting skills and experience most heavily
- matched_skills: skills present in both resume and JD
- missing_skills: JD-required skills absent from the resume
- recommendation: one of "Strong Fit", "Moderate Fit", "Stretch Fit", "Not Recommended"
- reason: one or two sentence explanation grounded in the resume content
"""


def score_candidate_with_llm(
    resume_text: str,
    parsed_resume: str,
    jd_analysis: str,
    rag_context: str,
    file_name: str,
) -> dict:

    llm = get_llm()
    structured_llm = llm.with_structured_output(CandidateScore)

    prompt = SCORING_PROMPT.format(
        jd_analysis=jd_analysis or "N/A",
        rag_context=rag_context or "N/A",
        parsed_resume=parsed_resume or "N/A",
        # guard against extremely long resumes blowing up the prompt
        resume_text=(resume_text or "")[:6000],
    )

    try:
        result: CandidateScore = structured_llm.invoke(prompt)
    except Exception as e:
        # One bad LLM call (rate limit, malformed output, network hiccup)
        # should not crash the whole batch - fall back to a safe, clearly
        # flagged zero score instead of raising.
        return {
            "Candidate Name": file_name,
            "Skill Score": 0,
            "Experience Score": 0,
            "Project Score": 0,
            "Education Score": 0,
            "Final Score": 0,
            "Matched Skills": [],
            "Missing Skills": [],
            "Recommendation": "Not Recommended",
            "Reason": f"LLM scoring failed for this candidate: {e}",
        }

    return {
        "Candidate Name": file_name,
        "Skill Score": result.skill_score,
        "Experience Score": result.experience_score,
        "Project Score": result.project_score,
        "Education Score": result.education_score,
        "Final Score": result.final_score,
        "Matched Skills": result.matched_skills,
        "Missing Skills": result.missing_skills,
        "Recommendation": result.recommendation,
        "Reason": result.reason,
    }
