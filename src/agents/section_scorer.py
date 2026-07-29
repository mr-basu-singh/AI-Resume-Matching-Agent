"""
Section-by-section candidate scoring against a JD.

Experience math is done in plain Python from LLM-extracted raw numbers
(months of experience vs. months required) - that's exact arithmetic,
and LLMs are unreliable at precise arithmetic, so we never ask the LLM
to invent that percentage itself.

Skill matching is two-stage, the way real ATS/resume-screening pipelines
(Workday, Greenhouse, LinkedIn Recruiter and similar) actually do it:

  1. A deterministic keyword/phrase scan across the ENTIRE raw resume
     text - not just a parsed "skills" list, and not dependent on any
     LLM call. If a required skill (or an obvious sub-phrase of a
     compound one, e.g. "Tool Calling" inside "Function/Tool Calling")
     appears literally anywhere in the resume - the skills section, a
     project bullet, a job description, anywhere - it's matched. This
     can never be missed by an LLM attention slip, because no LLM is
     involved in this pass at all.

  2. An LLM semantic judgment pass for skills that AREN'T a literal
     text match - things like a resume that lists "FAISS, ChromaDB,
     Embeddings" clearly having "RAG and retrieval systems" skill even
     without using that exact phrase. This pass must cite evidence for
     every verdict (SkillEvidence) so it can't hallucinate a match, and
     defaults to "missing" when evidence is weak or indirect.

A skill counts as matched if EITHER stage found it. The final skill
PERCENTAGE is still computed deterministically in Python from those
verdicts - only the classification itself is delegated to keyword
matching / the LLM, never the arithmetic.

Project relevance and education-field relatedness also come from the
same LLM call, using the same evidence-based rubric.
"""

import re

from src.llm.llm_config import get_llm
from src.models.schema import JDRequirements, ParsedResume, SectionJudgment


# ======================================================
# WEIGHTS
# Priority order requested: skill > project > experience > education
# ======================================================
SKILL_WEIGHT = 0.40
PROJECT_WEIGHT = 0.30
EXPERIENCE_WEIGHT = 0.20
EDUCATION_WEIGHT = 0.10


# ======================================================
# EXPERIENCE SCORE (deterministic)
# ======================================================
def _format_months(months) -> str:
    months = int(round(months))
    if months <= 0:
        return "No experience"

    years, rem_months = divmod(months, 12)
    parts = []
    if years:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if rem_months:
        parts.append(f"{rem_months} month{'s' if rem_months != 1 else ''}")

    return " ".join(parts) if parts else "No experience"


def score_experience(jd: JDRequirements, resume: ParsedResume):
    required_months = max(jd.required_experience_years, 0) * 12
    candidate_months = max(resume.total_experience_months, 0)
    candidate_text = _format_months(candidate_months)

    if required_months <= 0:
        # JD doesn't ask for experience at all - never penalize for this,
        # just report what the candidate actually has for context.
        detail = f"{candidate_text} (not required for this role)"
        return 100, detail

    if candidate_months <= 0:
        detail = f"No experience (JD requires {_format_months(required_months)})"
        return 0, detail

    ratio = candidate_months / required_months
    experience_score = round(min(ratio, 1.0) * 100)

    if candidate_months >= required_months:
        detail = f"{candidate_text} (meets/exceeds JD requirement of {_format_months(required_months)})"
    else:
        detail = f"{candidate_text} (JD requires {_format_months(required_months)} - {experience_score}% match)"

    return experience_score, detail


# ======================================================
# STAGE 1: DETERMINISTIC KEYWORD SCAN (no LLM involved)
# ======================================================
def _normalize_text(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]", " ", (text or "").lower())


def deterministic_skill_match(skill: str, normalized_resume_text: str) -> bool:
    """
    Exact/near-exact match of a required skill against the FULL raw resume
    text (skills section, project bullets, experience bullets - everywhere).
    Compound skill names like "Function/Tool Calling" are split so that a
    resume containing just "Tool Calling" still counts as a real, literal
    match. Only whole phrases or clearly delineated sub-phrases are checked -
    never a single generic short word alone (so "Model Training" won't
    false-positive off a stray word like "train" appearing elsewhere).
    """
    if not normalized_resume_text:
        return False

    skill_norm = _normalize_text(skill).strip()
    if not skill_norm:
        return False

    candidates = {skill_norm}
    lowered = skill.lower()
    for sep in ["/", ",", " or ", " and "]:
        if sep in lowered:
            for part in lowered.split(sep):
                p = _normalize_text(part).strip()
                if p:
                    candidates.add(p)

    for c in candidates:
        words = c.split()
        if not words:
            continue
        if len(words) == 1 and len(c) <= 4:
            # short single token (e.g. "api", "aws") - require a real word
            # boundary match, not a bare substring, to avoid noise
            if re.search(rf"\b{re.escape(c)}\b", normalized_resume_text):
                return True
        elif c in normalized_resume_text:
            return True

    return False


# ======================================================
# COMBINE STAGE 1 (keyword scan) + STAGE 2 (LLM judgment)
# INTO THE FINAL SKILL SCORE (deterministic math)
# ======================================================
def score_skills(jd: JDRequirements, judgment: SectionJudgment, resume_text: str = ""):
    required = [s for s in jd.required_skills if s and s.strip()]
    preferred = [s for s in jd.preferred_skills if s and s.strip()]

    if not required and not preferred:
        # JD didn't specify concrete skills - nothing to penalize against
        return 100, [], []

    llm_verdict = {ev.skill.strip().lower(): bool(ev.matched) for ev in judgment.skill_assessment}
    normalized_resume_text = _normalize_text(resume_text)

    def is_matched(skill: str) -> bool:
        # Stage 1 first: a literal match in the resume text always counts,
        # regardless of what the LLM said.
        if deterministic_skill_match(skill, normalized_resume_text):
            return True
        # Stage 2: fall back to the LLM's evidence-grounded semantic verdict.
        return llm_verdict.get(skill.strip().lower(), False)

    matched_required = [s for s in required if is_matched(s)]
    matched_preferred = [s for s in preferred if is_matched(s)]
    missing_required = [s for s in required if s not in matched_required]

    required_weight = len(required) * 1.0
    preferred_weight = len(preferred) * 0.5
    total_weight = required_weight + preferred_weight

    earned = len(matched_required) * 1.0 + len(matched_preferred) * 0.5

    skill_score = round(min(earned / total_weight, 1.0) * 100) if total_weight > 0 else 100
    matched_skills = matched_required + matched_preferred

    return skill_score, matched_skills, missing_required


# ======================================================
# STAGE 2: SKILL MATCH + PROJECT + EDUCATION JUDGMENT (LLM)
# ======================================================
JUDGMENT_PROMPT = """
You are an expert technical recruiter judging ONE candidate for a specific role.
You must be strict, literal, and evidence-based. Do not guess, do not assume, and
do not give the candidate credit for anything you cannot point to directly in
their resume.

========================
ROLE REQUIREMENTS
========================
Role: {role_title}
What HR needs: {key_requirements_summary}

Required skills:
{required_skills}

Preferred skills:
{preferred_skills}

Required education field: {required_education_field}
Required education level: {required_education_level}

========================
CANDIDATE'S LISTED SKILLS (structured extraction)
========================
{candidate_skills}

========================
CANDIDATE'S PROJECTS (structured extraction)
========================
{projects}

========================
CANDIDATE'S EXPERIENCE SUMMARY
========================
{experience_summary}

========================
CANDIDATE'S EDUCATION
========================
{education_details}
(Field: {education_field}, Level: {education_level})

========================
ORIGINAL FULL RESUME TEXT (search this too - a skill can be mentioned inside a
project bullet or job description without being repeated in a skills list)
========================
{raw_resume_text}

TASK 1 - SKILL ASSESSMENT (skill_assessment field):
For EVERY skill listed under "Required skills" and "Preferred skills" above, produce one
entry with: the exact skill string (copied verbatim), matched (true/false), and evidence
(a direct quote or close paraphrase from ANYWHERE in the candidate's resume - skills list,
project descriptions, experience, or the full resume text - or "No evidence found." if none).

STRICT RULES - DO NOT HALLUCINATE:
- Search the WHOLE resume, not just the skills list. Many candidates only mention a tool
  or technology inside a project bullet or job description (e.g. "built with FastAPI and
  Docker") without repeating it in a formal skills section - that still counts as evidence.
- If a skill name, or an obvious synonym or substring of it, appears literally anywhere in
  the resume, that IS direct evidence. Example: required skill is "Function/Tool Calling"
  and the resume contains "Tool Calling" - that MUST be matched=true. Do not require
  perfect wording symmetry.
- Evaluating, benchmarking, comparing, or selecting between existing/pre-trained models
  (e.g. "compared 4 LLMs and identified the best one") is NOT the same as "Fine-tuning" or
  "Model Training". Only mark those matched if the resume explicitly describes training a
  model, fine-tuning weights, or adjusting model parameters on custom data.
- Do not infer a skill just because the candidate works in a related area. Building RAG
  pipelines does not automatically imply "Testing" or "Observability" unless explicitly
  mentioned somewhere in the resume.
- If you are genuinely unsure or the evidence is weak/indirect, mark matched=false. A false
  "matched" misleads the whole screening process far more than an under-credit does.

TASK 2 - project_score (0-100): how relevant and strong are their projects for this
specific role's requirements? No projects listed should not automatically mean 0 - use a
low but non-zero score (10-20) if everything else is otherwise reasonable.

TASK 3 - education_score (0-100): how well their education matches what the JD needs.
- If required_education_field above is "Not specified", you MUST score 80-100 based on
  level only - do not penalize for field when the JD didn't ask for one.
- If a field WAS specified: same/matching field = 85-100; a closely related technical
  field (e.g. JD wants Computer Science, candidate has Electrical/Electronics/IT) =
  45-65 partial credit, never treat a related engineering field as a total mismatch; a
  clearly unrelated field = 10-30.

Explain the project and education scores briefly, and give one overall one-to-two
sentence summary of why this candidate lands where they do.
"""


def judge_candidate(jd: JDRequirements, resume: ParsedResume, resume_text: str = "") -> SectionJudgment:
    llm = get_llm()
    structured_llm = llm.with_structured_output(SectionJudgment)

    prompt = JUDGMENT_PROMPT.format(
        role_title=jd.role_title or "N/A",
        key_requirements_summary=jd.key_requirements_summary or "N/A",
        required_skills="\n".join(f"- {s}" for s in jd.required_skills) or "None specified",
        preferred_skills="\n".join(f"- {s}" for s in jd.preferred_skills) or "None specified",
        required_education_field=jd.required_education_field or "Not specified",
        required_education_level=jd.required_education_level or "Not specified",
        candidate_skills=", ".join(resume.candidate_skills) or "None listed",
        projects="\n".join(f"- {p}" for p in resume.projects) or "No projects listed",
        experience_summary=resume.experience_summary or "N/A",
        education_details=resume.education_details or "Not specified",
        education_field=resume.education_field or "Not specified",
        education_level=resume.education_level or "Not specified",
        raw_resume_text=(resume_text or "Not available")[:6000],
    )

    try:
        return structured_llm.invoke(prompt)
    except Exception as e:
        fallback_skills = [
            {"skill": s, "matched": False, "evidence": f"Scoring failed: {e}"}
            for s in list(jd.required_skills) + list(jd.preferred_skills)
        ]
        return SectionJudgment(
            skill_assessment=fallback_skills,
            project_score=0,
            project_reason=f"Scoring failed: {e}",
            education_score=0,
            education_reason=f"Scoring failed: {e}",
            overall_reason=f"Section scoring failed: {e}",
        )


# ======================================================
# COMBINE EVERYTHING INTO ONE CANDIDATE RESULT
# ======================================================
def score_candidate(jd: JDRequirements, resume: ParsedResume, file_name: str, resume_text: str = "") -> dict:
    judgment = judge_candidate(jd, resume, resume_text)

    skill_score, matched_skills, missing_skills = score_skills(jd, judgment, resume_text)
    experience_score, experience_detail = score_experience(jd, resume)

    final_score = round(
        skill_score * SKILL_WEIGHT
        + judgment.project_score * PROJECT_WEIGHT
        + experience_score * EXPERIENCE_WEIGHT
        + judgment.education_score * EDUCATION_WEIGHT
    )
    final_score = max(0, min(final_score, 100))

    if final_score >= 80:
        recommendation = "Strong Fit"
    elif final_score >= 60:
        recommendation = "Moderate Fit"
    elif final_score >= 40:
        recommendation = "Stretch Fit"
    else:
        recommendation = "Not Recommended"

    return {
        "Candidate Name": file_name,
        "Skill Score": skill_score,
        "Matched Skills": matched_skills,
        "Missing Skills": missing_skills,
        "Experience Score": experience_score,
        "Experience Detail": experience_detail,
        "Project Score": judgment.project_score,
        "Project Notes": judgment.project_reason,
        "Education Score": judgment.education_score,
        "Education Detail": judgment.education_reason,
        "Final Score": final_score,
        "Recommendation": recommendation,
        "Reason": judgment.overall_reason,
    }
