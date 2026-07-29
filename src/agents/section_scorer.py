"""
Section-by-section candidate scoring against a JD.

Experience math is done in plain Python from LLM-extracted raw numbers
(months of experience vs. months required) - that's exact arithmetic,
and LLMs are unreliable at precise arithmetic, so we never ask the LLM
to invent that percentage itself.

Skill matching, project relevance, and education-field relatedness all
genuinely need semantic judgment, not string comparison - but semantic
judgment without grounding is exactly how an LLM hallucinates ("Fine-tuning"
credited for a candidate who only ever evaluated pre-trained models) or
misses obvious matches ("Tool Calling" marked missing when it's spelled
out verbatim in the resume). To fight that, the LLM must produce a
per-skill evidence quote before deciding match/no-match (SkillEvidence),
and the final skill PERCENTAGE is still computed deterministically in
Python from those verdicts - only the classification itself is the LLM's job.

The judgment call also gets the ORIGINAL raw resume text, not just the
already-summarized ParsedResume fields, as a fallback reference - so a
detail that got compressed away during the first extraction pass (e.g.
a tech mentioned in a project's tech-stack line but not its description)
can still be found instead of being lost to double summarization.
"""

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
# SKILL SCORE (deterministic math on top of the LLM's
# evidence-grounded per-skill verdicts)
# ======================================================
def score_skills_from_judgment(jd: JDRequirements, judgment: SectionJudgment):
    required = [s for s in jd.required_skills if s and s.strip()]
    preferred = [s for s in jd.preferred_skills if s and s.strip()]

    if not required and not preferred:
        # JD didn't specify concrete skills - nothing to penalize against
        return 100, [], []

    verdict = {ev.skill.strip().lower(): bool(ev.matched) for ev in judgment.skill_assessment}

    matched_required = [s for s in required if verdict.get(s.strip().lower(), False)]
    matched_preferred = [s for s in preferred if verdict.get(s.strip().lower(), False)]
    missing_required = [s for s in required if s not in matched_required]

    required_weight = len(required) * 1.0
    preferred_weight = len(preferred) * 0.5
    total_weight = required_weight + preferred_weight

    earned = len(matched_required) * 1.0 + len(matched_preferred) * 0.5

    skill_score = round(min(earned / total_weight, 1.0) * 100) if total_weight > 0 else 100
    matched_skills = matched_required + matched_preferred

    return skill_score, matched_skills, missing_required


# ======================================================
# SKILL MATCH + PROJECT + EDUCATION JUDGMENT (LLM)
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
ORIGINAL FULL RESUME TEXT (fallback reference only - use this to double-check for
evidence that may have been compressed out of the structured extraction above, e.g.
a technology mentioned in a project's tech-stack line but not its description)
========================
{raw_resume_text}

TASK 1 - SKILL ASSESSMENT (skill_assessment field):
For EVERY skill listed under "Required skills" and "Preferred skills" above, produce one
entry with: the exact skill string (copied verbatim), matched (true/false), and evidence
(a direct quote or close paraphrase from the candidate's skills/projects/experience/full
resume text, or "No evidence found." if none).

STRICT RULES - DO NOT HALLUCINATE:
- If a skill name, or an obvious synonym or substring of it, appears literally anywhere
  in the candidate's skills list or the full resume text, that IS direct evidence.
  Example: required skill is "Function/Tool Calling" and the candidate's skills list
  contains "Tool Calling" - that MUST be marked matched=true, because "Tool Calling" is
  explicitly, literally there. Do not require perfect wording symmetry.
- Evaluating, benchmarking, comparing, or selecting between existing/pre-trained models
  (e.g. "compared 4 LLMs and identified the best one", "benchmarked model quality vs
  cost") is NOT the same as "Fine-tuning" or "Model Training". Only mark those matched
  if the resume explicitly describes training a model, fine-tuning weights, or adjusting
  model parameters on custom data - not just using, calling, evaluating, or picking
  between models via an API.
- Do not infer a skill just because the candidate works in a related area. Building RAG
  pipelines does not automatically imply "Testing" or "Observability" skill unless those
  are explicitly mentioned somewhere in the resume.
- If you are genuinely unsure or the evidence is weak/indirect, mark matched=false. It is
  much worse to falsely credit a skill the candidate doesn't have than to under-credit one
  they do - a human recruiter will double check "missing" skills, but a false "matched"
  skill misleads the whole screening process.

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

    skill_score, matched_skills, missing_skills = score_skills_from_judgment(jd, judgment)
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
