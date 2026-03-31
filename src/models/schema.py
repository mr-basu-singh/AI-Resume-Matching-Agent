from pydantic import BaseModel, Field
from typing import List


class CandidateScore(BaseModel):
    candidate_name: str = Field(description="Candidate full name or resume file name")
    skill_score: int = Field(description="Score from 0 to 100")
    experience_score: int = Field(description="Score from 0 to 100")
    project_score: int = Field(description="Score from 0 to 100")
    education_score: int = Field(description="Score from 0 to 100")
    final_score: int = Field(description="Final weighted score from 0 to 100")
    matched_skills: List[str] = Field(description="Skills present in both resume and JD")
    missing_skills: List[str] = Field(description="Skills required in JD but missing in resume")
    recommendation: str = Field(description="One of: Strong Fit, Moderate Fit, Stretch Fit, Not Recommended")
    reason: str = Field(description="Short explanation for the ranking")