# 🤖 AI Resume Matching Agent (Agentic AI)

An Agentic AI Recruiter Assistant that analyzes resumes, compares them with job descriptions, scores candidates, and ranks them automatically.

This tool helps:

- Recruiters shortlist candidates faster  
- Companies rank multiple resumes instantly  
- Job seekers check resume match score  
- HR automate screening process  

---

# 🚀 Features

- Upload multiple resumes (PDF)  
- Paste job description  
- AI analyzes job requirements  
- Resume parsing agent  
- Matching agent  
- Recruiter ranking agent  
- Weighted scoring system  
- Candidate ranking  
- Match explanation  
- Missing skills detection  
- Fit recommendation  
- CSV export  
- Clean Streamlit UI  
- Multi-agent workflow  

---

# 🧠 Agentic AI Architecture

This project uses multi-agent architecture:

1. Resume Parser Agent  
2. Job Description Analyzer Agent  
3. Matcher Agent  
4. Recruiter Matcher Agent  
5. Ranker Agent  
6. Interview Prep Agent  

Each agent performs one task and passes output to next agent.

---

# ⚙️ Scoring System

Candidates are scored using:

Skill Match → 40%  
Experience → 20%  
Projects → 20%  
Education → 20%  

Final Score = Weighted Score

Candidates are ranked based on Final Score.

---

# 🏗️ Project Structure

```
AI-Resume-Matching-Agent
│
├── app.py
├── README.md
├── requirements.txt
│
└── src
    ├── agents
    │   ├── interview_prep.py
    │   ├── jd_analyzer.py
    │   ├── matcher.py
    │   ├── ranker.py
    │   ├── recruiter_matcher.py
    │   └── resume_parser.py
    │
    ├── llm
    │   └── llm_config.py
    │
    ├── utils
    │   ├── file_handler.py
    │   ├── pdf_reader.py
    │   └── text_cleaner.py
    │
    ├── models
    │   └── schema.py
    │
    ├── prompts
    │   └── prompts.py
    │
    └── graph
        └── workflow.py
```

---

# 🧩 Agents Explanation

### resume_parser.py
Extracts structured information from resume  
Skills, experience, education, projects

### jd_analyzer.py
Analyzes job description and extracts:
- Required skills  
- Experience level  
- Responsibilities  
- Preferred qualifications  

### matcher.py
Matches resume with job description

Calculates:
- skill match  
- experience match  
- project relevance  
- education match  

### recruiter_matcher.py
Handles multiple resume scoring against single job description.

Used in Recruiter Mode

Returns:
- Score  
- Reason  
- Fit level  

### ranker.py
Ranks candidates based on final score

Returns:
- Rank 1  
- Rank 2  
- Rank 3  

### interview_prep.py
Optional agent that generates interview questions based on resume + JD.

---

# 🔁 Agent Workflow

Job Description  
↓  
JD Analyzer Agent  
↓  
Resume Parser Agent  
↓  
Matcher Agent  
↓  
Recruiter Matcher Agent  
↓  
Ranker Agent  
↓  
Final Candidate Ranking  

---

# 🖥️ UI Features

- Recruiter dashboard  
- Upload multiple resumes  
- Paste job description  
- Candidate ranking table  
- Top candidate highlight  
- Score filtering  
- CSV export  
- Candidate explanation  

---

# 📊 Example Output

Rank 1 — AI Engineer — 82% — Strong Fit  
Rank 2 — Python Developer — 74% — Moderate Fit  
Rank 3 — Data Scientist — 65% — Stretch Fit  

---

# ⚙️ Installation

Clone repository

```
git clone https://github.com/yourusername/AI-Resume-Matching-Agent.git
cd AI-Resume-Matching-Agent
```

Create virtual environment

```
python -m venv venv
venv\Scripts\activate
```

Install dependencies

```
pip install -r requirements.txt
```

---

# 🔑 Environment Variables

Create `.env` file

```
GROQ_API_KEY=your_key
HUGGINGFACE_API_KEY=your_key
TAVILY_API_KEY=your_key
```

---

# ▶️ Run Application

```
streamlit run app.py
```

App will open at:

```
http://localhost:8501
```

---

# 📦 Dependencies

- Streamlit  
- LangChain  
- Groq  
- PyPDF  
- Pandas  
- Python-dotenv  
- Regex  
- Typing  

---

# 🎯 Use Cases

- Resume screening  
- HR automation  
- Recruiter shortlist  
- Campus hiring  
- Internship filtering  
- Resume match checker  
- ATS style scoring  

---

# 🔮 Future Improvements

- ATS score  
- Skill gap detection  
- Resume improvement suggestions  
- Interview question generator  
- Job recommendation mode  
- Candidate summary generator  
- Database storage  
- Cloud deployment  

---

# 👨‍💻 Author

Kumar Basu Singh  
B.Tech Electrical & Electronics Engineering  
Agentic AI Developer

Built using multi-agent architecture and LLMs.

---

# ⭐ If you like this project

Star the repository  
Fork the repo  
Build on top of it  

---

# 📄 License

MIT License
