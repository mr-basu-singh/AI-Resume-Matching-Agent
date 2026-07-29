from pydantic import BaseModel, Field
from typing import List


# ======================================================
# WHAT THE JD / HR ACTUALLY NEEDS FROM A CANDIDATE
# ======================================================
class JDRequirements(BaseModel):
    role_title: str = Field(description="Job title / role name")

    required_skills: List[str] = Field(
        default_factory=list,
        description="Skills the JD explicitly requires or clearly implies are mandatory"
    )
    preferred_skills: List[str] = Field(
        default_factory=list,
        description="Skills mentioned as nice-to-have / preferred / bonus, not mandatory"
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
            "'Electrical Engineering'. Leave empty string if the JD does not specify a field."
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
        description="Candidate's field of study, e.g. 'Computer Science', 'Electrical and Electronics Engineering'"
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
        description="Short names/descriptions of projects listed on the resume"
    )


# ======================================================
# THE TWO SCORES THAT NEED GENUINE JUDGMENT, NOT COUNTING
# ======================================================
class SectionJudgment(BaseModel):
    project_score: int = Field(
        description="0-100: how relevant/strong the candidate's projects are for this specific role"
    )
    project_reason: str = Field(description="One sentence explaining the project score")

    education_score: int = Field(
        description=(
            "0-100: how well the candidate's education matches what the JD needs. "
            "Same field as required = high score (85-100). A closely related technical "
            "field (e.g. JD wants Computer Science, candidate has Electrical/Electronics/IT) "
            "with a relevant degree level = partial credit (45-65), never treat a related "
            "engineering field as a total mismatch. Clearly unrelated field entirely = low "
            "score (10-30). If JD does not specify a required field, judge by level only "
            "and default toward 80-100."
        )
    )
    education_reason: str = Field(
        description="One sentence explaining the education score, mention the field comparison explicitly"
    )

    overall_reason: str = Field(
        description="One or two sentence overall summary of why this candidate lands at this final ranking"
    )
