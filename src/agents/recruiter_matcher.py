import re


# ======================================================
# TEXT NORMALIZATION
# ======================================================
def normalize(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"[^a-z0-9+.# ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ======================================================
# EXTRACT KEYWORDS FROM JD (DYNAMIC APPROACH)
# ======================================================
def extract_jd_keywords(jd_text: str):
    """
    Extract meaningful words from JD dynamically
    """
    words = re.findall(r"\b[a-zA-Z]{3,}\b", jd_text.lower())

    stopwords = {
        "the", "and", "for", "with", "this", "that", "are", "you",
        "will", "have", "has", "job", "role", "work", "working",
        "team", "experience", "candidate", "skills", "should",
        "required", "requirements", "responsibilities"
    }

    keywords = [w for w in words if w not in stopwords]

    # remove duplicates
    return list(set(keywords))


# ======================================================
# MATCH SCORE CALCULATION
# ======================================================
def calculate_match_score(resume, jd_keywords):
    if not jd_keywords:
        return 0, []

    matched = []
    for word in jd_keywords:
        if re.search(r"\b" + re.escape(word) + r"\b", resume):
            matched.append(word)

    score = (len(matched) / len(jd_keywords)) * 100
    return min(int(score), 100), matched


# ======================================================
# EXPERIENCE SCORE CALCULATION (CONTEXT AWARE)
# ======================================================
def calculate_experience_score(resume: str) -> int:
    """
    Old logic gave 80 just because the word "experience" appeared
    anywhere in the resume - which also matches phrases like
    "no experience", "0 years of experience", "fresher", or an
    empty "Experience" section header. This version checks for
    actual signals of experience instead of a bare word match.
    """

    # --------------------------------------------------
    # EXPLICIT "NO EXPERIENCE" SIGNALS -> 0%
    # --------------------------------------------------
    no_experience_phrases = [
        "no work experience", "no prior experience", "no experience",
        "0 years of experience", "0 years experience", "fresher",
        "seeking my first job", "no professional experience"
    ]
    if any(p in resume for p in no_experience_phrases):
        return 0

    # --------------------------------------------------
    # EXPLICIT "X YEARS OF EXPERIENCE" SIGNAL
    # --------------------------------------------------
    years_matches = re.findall(
        r"(\d+(?:\.\d+)?)\+?\s*(?:years|yrs)\s*(?:of\s*)?experience", resume
    )
    if years_matches:
        years = max(float(y) for y in years_matches)
        if years <= 0:
            return 0
        return min(int(40 + years * 10), 100)

    # --------------------------------------------------
    # WORK-HISTORY SIGNALS: date ranges + role language
    # (avoids counting a lone word like "experience"/"built")
    # --------------------------------------------------
    has_date_range = re.search(
        r"(19|20)\d{2}\s*(-|to|–)\s*((19|20)\d{2}|present|current)", resume
    )
    has_role_language = any(
        p in resume for p in [
            "worked at", "working at", "employed at", "work experience",
            "professional experience", "managed a team", "led a team",
            "responsibilities included"
        ]
    )

    if has_date_range and has_role_language:
        return 75
    elif has_date_range:
        return 55
    elif has_role_language:
        return 50

    # --------------------------------------------------
    # NO SIGNAL OF EXPERIENCE AT ALL -> 0%
    # --------------------------------------------------
    return 0


# ======================================================
# MAIN FUNCTION
# ======================================================
def score_candidate_against_jd(resume_text: str, job_description: str, file_name: str):

    resume = normalize(resume_text)
    jd = normalize(job_description)

    # --------------------------------------------------
    # JD KEYWORDS (IMPORTANT FIX)
    # --------------------------------------------------
    jd_keywords = extract_jd_keywords(jd)

    # --------------------------------------------------
    # MATCH SCORE (GENERIC)
    # --------------------------------------------------
    skill_score, matched_skills = calculate_match_score(resume, jd_keywords)

    # --------------------------------------------------
    # EXPERIENCE SCORE (CONTEXT AWARE)
    # --------------------------------------------------
    experience_score = calculate_experience_score(resume)

    # --------------------------------------------------
    # PROJECT SCORE (DOMAIN FREE)
    # --------------------------------------------------
    project_score = 50

    if "project" in resume or "developed" in resume or "built" in resume:
        project_score = 80

    # --------------------------------------------------
    # EDUCATION SCORE (GENERIC)
    # --------------------------------------------------
    education_score = 60

    if any(x in resume for x in ["b.tech", "btech", "bachelor", "master", "degree"]):
        education_score = 80

    # --------------------------------------------------
    # FINAL SCORE (BALANCED ATS MODEL)
    # --------------------------------------------------
    final_score = int(
        skill_score * 0.6 +
        experience_score * 0.2 +
        project_score * 0.15 +
        education_score * 0.05
    )

    final_score = min(final_score, 100)

    # --------------------------------------------------
    # RECOMMENDATION
    # --------------------------------------------------
    if final_score >= 80:
        recommendation = "Strong Fit"
    elif final_score >= 60:
        recommendation = "Moderate Fit"
    elif final_score >= 40:
        recommendation = "Stretch Fit"
    else:
        recommendation = "Not Recommended"

    # --------------------------------------------------
    # REASON (EXPLAINABLE AI STYLE)
    # --------------------------------------------------
    reason = (
        f"Matched {len(matched_skills)} of {len(jd_keywords)} JD keywords."
    )

    # --------------------------------------------------
    # OUTPUT
    # --------------------------------------------------
    return {
        "Candidate Name": file_name,
        "Skill Score": skill_score,
        "Experience Score": experience_score,
        "Project Score": project_score,
        "Education Score": education_score,
        "Final Score": final_score,
        "Matched Skills": matched_skills,
        "Missing Skills": list(set(jd_keywords) - set(matched_skills)),
        "Recommendation": recommendation,
        "Reason": reason
    }
