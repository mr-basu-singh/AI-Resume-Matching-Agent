🤖 AI Resume Matching Agent

An intelligent Agentic AI recruiter assistant that screens, scores, and ranks multiple resumes against a job description using LLMs.

This tool helps recruiters quickly identify the best candidates and helps job seekers understand how well their resume matches a role.

🚀 Features
Upload multiple resumes (PDF)
Paste job description
AI compares resume with job requirements
Weighted scoring system
Candidate ranking
Matched skills detection
Missing skills detection
Recruiter recommendation (Strong Fit / Moderate Fit / Stretch Fit / Not Recommended)
Top candidate highlight
Candidate breakdown view
Score filtering
CSV export of ranked candidates
Clean recruiter dashboard UI
🧠 How It Works

Step 1
User pastes job description

Step 2
User uploads multiple resumes

Step 3
AI extracts text from resumes

Step 4
LLM compares resume with job description

Step 5
AI calculates weighted score:

Final Score =

Skill Match → 40%
Experience → 20%
Projects → 20%
Education → 20%

Step 6
Candidates are ranked by Final Score

Step 7
Dashboard displays results

# 🏗️ Project Structure

AI-Resume-Matching-Agent/
│
├── app.py
├── requirements.txt
├── README.md
│
└── src/
    ├── agents/
    │   ├── interview_prep.py
    │   ├── jd_analyzer.py
    │   ├── matcher.py
    │   ├── ranker.py
    │   ├── recruiter_matcher.py
    │   └── resume_parser.py
    │
    ├── graph/
    │   └── workflow.py
    │
    ├── llm/
    │   └── llm_config.py
    │
    ├── models/
    │   └── schema.py
    │
    ├── prompts/
    │   └── prompts.py
    │
    └── utils/
        ├── file_handler.py
        ├── pdf_reader.py
        └── text_cleaner.py
⚙️ Tech Stack

Python
Streamlit
LangChain
Groq LLM (LLaMA 3)
PDF Text Extraction (PyPDF)
Pandas
Regex Parsing
Agentic AI Workflow

📊 Scoring System

Each candidate is scored using:

Skill Score (40%)
Experience Score (20%)
Project Score (20%)
Education Score (20%)

Final Score is calculated automatically and used for ranking.

🖥️ Installation

Clone repository

git clone https://github.com/your-username/AI-Resume-Matching-Agent.git
cd AI-Resume-Matching-Agent

Create virtual environment

python -m venv venv
venv\Scripts\activate

Install dependencies

pip install -r requirements.txt
🔑 Environment Variables

Create .env file:

GROQ_API_KEY=your_api_key
▶️ Run App
streamlit run app.py
📌 Example Use Case

Job Description:
Generative AI Engineer

Upload resumes:

Python Developer
AI Engineer
Data Scientist
ML Intern

AI Output:
Rank 1 — AI Engineer — 82% — Strong Fit
Rank 2 — Python Developer — 68% — Moderate Fit
Rank 3 — Data Scientist — 60% — Stretch Fit
Rank 4 — ML Intern — 45% — Not Recommended

📸 Features in UI

Recruiter Dashboard
Top 3 Candidates
Score Cards
Candidate Ranking Table
Candidate Details View
Score Filtering
CSV Export

🎯 Use Cases

Recruiters screening candidates
HR resume filtering
Job seekers checking resume match
Internship screening
Campus hiring automation
Resume shortlisting

🔮 Future Improvements

Resume parser improvements
JD skill extraction agent
Interview question generator
Candidate summary generator
ATS keyword optimization
Multi-job comparison
Cloud deployment
Database storage

🙌 Author

Kumar Basu Singh
B.Tech Electrical & Electronics Engineering
AI Enthusiast | Agentic AI Developer

⭐ Project Goal

Build a real-world Agentic AI recruiter assistant that automates resume screening and candidate ranking using LLM intelligence.

📄 License

MIT License
