import streamlit as st
import pandas as pd

from src.utils.file_handler import extract_text_from_pdf
from src.graph.workflow import app as langgraph_app


# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="AI Resume Matching Agent",
    page_icon="📄",
    layout="wide"
)


# ======================================================
# UI TITLE
# ======================================================
st.title("📄 AI Resume Matching Agent")
st.subheader("Skills, projects, experience & education matched section-by-section against your JD")


# ======================================================
# INPUT SECTION
# ======================================================
job_description = st.text_area(
    "Paste the Job Description (role details + what you need from candidates)",
    height=200
)

uploaded_files = st.file_uploader(
    "Upload Resumes (PDF)",
    type=["pdf"],
    accept_multiple_files=True
)

min_score = st.slider("Minimum Score Filter", 0, 100, 0)


# ======================================================
# RUN BUTTON
# ======================================================
if st.button("Run Screening"):

    if not job_description or not uploaded_files:
        st.warning("Please provide the job description and at least one resume")
        st.stop()

    # --------------------------------------------------
    # EXTRACT RESUMES
    # --------------------------------------------------
    resume_data = []

    for file in uploaded_files:

        try:
            text = extract_text_from_pdf(file)
        except Exception as e:
            st.warning(f"Skipped {file.name}: could not read PDF ({e})")
            continue

        if not text or not text.strip():
            st.warning(f"Skipped {file.name}: no extractable text found (likely a scanned/image PDF)")
            continue

        resume_data.append({"name": file.name, "text": text})

    if not resume_data:
        st.error("None of the uploaded resumes could be read. Please upload text-based PDFs.")
        st.stop()

    # --------------------------------------------------
    # RUN THE AGENT
    # --------------------------------------------------
    with st.spinner("Screening candidates..."):
        output = langgraph_app.invoke({
            "job_description": job_description,
            "resumes": resume_data
        })

    ranked_df = output["ranked"]

    # --------------------------------------------------
    # FILTERING
    # --------------------------------------------------
    ranked_df = ranked_df[
        ranked_df["Final Score"] >= min_score
    ].reset_index(drop=True)

    if ranked_df.empty:
        st.warning("No candidates meet the minimum score filter.")
        st.stop()

    if "Rank" in ranked_df.columns:
        ranked_df = ranked_df.drop(columns=["Rank"])

    ranked_df.insert(0, "Rank", ranked_df.index + 1)


    # ======================================================
    # METRICS
    # ======================================================
    st.success("Screening Completed")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Candidates", len(ranked_df))
    col2.metric("Top Score", int(ranked_df["Final Score"].max()))
    col3.metric("Average Score", int(ranked_df["Final Score"].mean()))
    col4.metric("Filtered", len(ranked_df))


    # ======================================================
    # DISPLAY TABLE
    # ======================================================
    st.markdown("## 📊 Ranking Table")
    st.dataframe(
        ranked_df[[
            "Rank", "Candidate Name", "Final Score", "Recommendation",
            "Skill Score", "Project Score", "Experience Score", "Education Score"
        ]],
        use_container_width=True
    )


    # ======================================================
    # DOWNLOAD CSV
    # ======================================================
    csv = ranked_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇ Download Results",
        data=csv,
        file_name="ranked_candidates.csv",
        mime="text/csv"
    )


    # ======================================================
    # DETAILED VIEW (SECTION BY SECTION)
    # ======================================================
    st.markdown("## 👤 Candidate Details")

    for _, row in ranked_df.iterrows():

        with st.expander(f"{row['Rank']}. {row['Candidate Name']} | {row['Final Score']}%"):

            matched = row["Matched Skills"]
            missing = row["Missing Skills"]
            matched_text = ", ".join(matched) if isinstance(matched, list) and matched else "None"
            missing_text = ", ".join(missing) if isinstance(missing, list) and missing else "None"

            st.markdown(f"""
### {row['Candidate Name'].replace('.pdf', '')}

**{row['Final Score']}% — {row['Recommendation']}**

---

**Skill Score: {row['Skill Score']}**
Matched Skills: {matched_text}
Missing Skills: {missing_text}

**Experience Score: {row['Experience Score']}**
{row['Experience Detail']}

**Project Score: {row['Project Score']}**
{row['Project Notes']}

**Education Score: {row['Education Score']}**
{row['Education Detail']}

---

**Overall:** {row['Reason']}
""")
