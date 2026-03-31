import re
import pandas as pd


def parse_candidate_result(result_text: str) -> dict:
    def extract(pattern, default=""):
        match = re.search(pattern, result_text, re.IGNORECASE)
        return match.group(1).strip() if match else default

    candidate_name = extract(r"Candidate Name:\s*(.*)")
    skill_score = extract(r"Skill Score:\s*(\d+)", "0")
    experience_score = extract(r"Experience Score:\s*(\d+)", "0")
    project_score = extract(r"Project Score:\s*(\d+)", "0")
    education_score = extract(r"Education Score:\s*(\d+)", "0")
    final_score = extract(r"Final Score:\s*(\d+)", "0")
    matched_skills = extract(r"Matched Skills:\s*(.*)")
    missing_skills = extract(r"Missing Skills:\s*(.*)")
    recommendation = extract(r"Recommendation:\s*(.*)")
    reason = extract(r"Reason:\s*(.*)")

    return {
        "Candidate Name": candidate_name,
        "Skill Score": int(skill_score),
        "Experience Score": int(experience_score),
        "Project Score": int(project_score),
        "Education Score": int(education_score),
        "Final Score": int(final_score),
        "Matched Skills": matched_skills,
        "Missing Skills": missing_skills,
        "Recommendation": recommendation,
        "Reason": reason,
    }


def rank_candidates(candidate_results: list) -> pd.DataFrame:
    parsed_results = [parse_candidate_result(result) for result in candidate_results]
    df = pd.DataFrame(parsed_results)
    df = df.sort_values(by="Final Score", ascending=False).reset_index(drop=True)
    df.insert(0, "Rank", df.index + 1)
    return df