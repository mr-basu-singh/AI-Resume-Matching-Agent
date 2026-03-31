from src.llm.llm_config import get_llm


def score_candidate_against_jd(resume_text: str, job_description: str, file_name: str) -> str:
    llm = get_llm()

    prompt = f"""
You are an expert recruiter AI.

Compare the candidate resume with the job description.

Score the candidate using these rules:
- Skill Score: 0 to 100
- Experience Score: 0 to 100
- Project Score: 0 to 100
- Education Score: 0 to 100

Then calculate:
Final Score = (Skill Score * 0.4) + (Experience Score * 0.2) + (Project Score * 0.2) + (Education Score * 0.2)

Return the result in this exact format only:

Candidate Name: <candidate name or file name>
Skill Score: <number>
Experience Score: <number>
Project Score: <number>
Education Score: <number>
Final Score: <number>
Matched Skills: <comma separated skills>
Missing Skills: <comma separated skills>
Recommendation: <Strong Fit / Moderate Fit / Stretch Fit / Not Recommended>
Reason: <short explanation in 2 to 3 lines>

Resume File Name:
{file_name}

Resume Text:
{resume_text}

Job Description:
{job_description}
"""

    response = llm.invoke(prompt)
    return response.content