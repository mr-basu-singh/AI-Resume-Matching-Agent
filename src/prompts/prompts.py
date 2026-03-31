RESUME_PARSER_PROMPT = """
You are a resume analysis assistant.

Read the resume text and extract:
1. Skills
2. Education
3. Projects
4. Tools
5. Experience level

Return the output in a clean structured format.

Resume:
{resume_text}
"""

JD_ANALYZER_PROMPT = """
You are a job description analysis assistant.

Read the job description and extract:
1. Required skills
2. Preferred skills
3. Role responsibilities
4. Experience needed

Return the output in a clean structured format.

Job Description:
{jd_text}
"""

MATCHER_PROMPT = """
You are a job match assistant.

Compare the resume details with the job description details.

Return:
1. Matching skills
2. Missing skills
3. Match score out of 100
4. Suggestions to improve the resume

Resume Details:
{resume_data}

Job Description Details:
{jd_data}
"""