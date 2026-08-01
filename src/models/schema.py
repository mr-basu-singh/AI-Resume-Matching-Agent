from pydantic import BaseModel, Field
from typing import List


# ======================================================
# WHAT THE JD / HR ACTUALLY NEEDS FROM A CANDIDATE
# ======================================================
class JDRequirements(BaseModel):
    role_title: str = Field(description="Job title / role name")

    required_skills: List[str] = Field(
        default_factory=list,
        description="Atomic, specific skill/technology/competency keywords the JD explicitly requires or clearly implies are mandatory"
    )
    preferred_skills: List[str] = Field(
        default_factory=list,
        description="Atomic, specific skill/technology/competency keywords mentioned as nice-to-have / preferred / bonus, not mandatory"
    )

    required_experience_years: float = Field(
        default=0,
        description=(
            "Minimum years of professional work experience required by the JD. "
            "Use 0 if the JD does not mention any experience requirement, or explicitly "
            "welcomes freshers/entry-level candidates."
        )
    )

    required_education_field: str = Field(
        default="",
        description=(
            "The specific field of study the JD asks for, e.g. 'Computer Science', "
            "'Commerce'. Leave empty string if the JD does not specify a field."
        )
    )
    required_education_level: str = Field(
        default="",
        description=(
            "Minimum education level required, e.g. 'Bachelor's', 'Master's', 'Diploma'. "
            "Leave empty string if not specified."
        )
    )

    key_requirements_summary: str = Field(
        default="",
        description="One or two sentence summary of what this JD/HR is really looking for"
    )


# ======================================================
# STRUCTURED EXTRACTION OF A CANDIDATE'S RESUME
# ======================================================
class ParsedResume(BaseModel):
    candidate_skills: List[str] = Field(
        default_factory=list,
        description="All technical/professional skills explicitly present in the resume"
    )

    total_experience_months: int = Field(
        default=0,
        description=(
            "Total months of real professional/work experience evidenced in the resume "
            "(internships count, coursework/personal projects do NOT count). Use 0 if the "
            "resume shows no professional work experience (e.g. a fresher/student resume)."
        )
    )
    experience_summary: str = Field(
        default="",
        description=(
            "Short human-readable description of the candidate's work experience, e.g. "
            "'1 year 2 months as a Software Engineer at Acme Corp' or 'No professional "
            "work experience found - fresher/student resume'."
        )
    )

    education_field: str = Field(
        default="",
        description="Candidate's field of study, e.g. 'Computer Science', 'Commerce', 'Electrical and Electronics Engineering'"
    )
    education_level: str = Field(
        default="",
        description="Candidate's highest education level, e.g. 'Bachelor's', 'Master's', 'Diploma'"
    )
    education_details: str = Field(
        default="",
        description="Short description, e.g. 'B.Tech in Electrical and Electronics Engineering from XYZ University'"
    )

    projects: List[str] = Field(
        default_factory=list,
        description="Short names/descriptions of projects listed on the resume, include the technologies used in each"
    )


# ======================================================
# ONE SKILL'S EVIDENCE-GROUNDED ASSESSMENT
# Forcing the LLM to cite evidence per skill (instead of a
# bare true/false) is what keeps it from hallucinating matches
# or missing skills that are literally spelled out in the resume.
# ======================================================
class SkillEvidence(BaseModel):
    skill: str = Field(description="The exact skill string, copied verbatim from the list given to you")
    matched: bool = Field(description="True only if you found direct, explicit evidence in the resume")
    evidence: str = Field(
        description=(
            "The exact quote or close paraphrase from the resume's skills/projects/experience "
            "that justifies this decision. If matched=False, write 'No evidence found.'"
        )
    )


# ======================================================
# THE THINGS THAT NEED GENUINE JUDGMENT, NOT JUST COUNTING:
# skill matching (semantic - does the resume provide real
# evidence, even under a different name?), project relevance,
# and education-field relatedness
# ======================================================
class SectionJudgment(BaseModel):
    skill_assessment: List[SkillEvidence] = Field(
        default_factory=list,
        description="One entry for EVERY required and preferred skill given to you, each with its own evidence"
    )

    project_score: int = Field(
        description=(
            "0-100: how relevant/strong the candidate's projects are for THIS SPECIFIC role. "
            "No projects listed at all should not automatically mean 0 (use 10-20, since not "
            "every good candidate lists projects). But projects that DO exist and are from a "
            "completely different domain than the role (e.g. AI/software projects for a "
            "finance/accounting/operations role, or vice versa) genuinely contribute almost "
            "nothing to that specific job and should score low (0-10) - do not inflate this "
            "just to avoid a low number."
        )
    )
    project_reason: str = Field(description="One sentence explaining the project score")

    education_score: int = Field(
        description=(
            "0-100: how well the candidate's education matches what the JD needs. "
            "If required_education_field was NOT specified in the JD, you MUST score "
            "80-100 based on level only - do not penalize for field when the JD didn't "
            "ask for one. If a field WAS specified, distinguish two cases: (1) a DIFFERENT "
            "SPECIALIZATION WITHIN THE SAME BROAD DOMAIN as required (e.g. JD wants Computer "
            "Science, candidate has Electrical/Electronics/IT - both technical/engineering "
            "fields) = 45-65 partial credit, never a total mismatch. (2) a COMPLETELY "
            "DIFFERENT DOMAIN with no real overlap (e.g. JD wants Commerce/Accounting and the "
            "candidate has an Electrical Engineering or unrelated technical degree, or vice "
            "versa - an engineering degree does not meaningfully prepare someone for a "
            "specialized accounting/finance role) = 0-20, genuinely low. Same/matching field "
            "= 85-100. Do not inflate a genuinely unrelated domain just to avoid a low number."
        )
    )
    education_reason: str = Field(
        description="One sentence explaining the education score, mention the field comparison explicitly"
    )

    overall_reason: str = Field(
        description="One or two sentence overall summary of why this candidate lands at this final ranking"
    )
