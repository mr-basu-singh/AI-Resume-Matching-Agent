import streamlit as st
import pandas as pd

from src.utils.file_handler import extract_text_from_pdf
from src.agents.recruiter_matcher import score_candidate_against_jd
from src.agents.ranker import rank_candidates


# OPTIONAL: LangGraph (NEW SYSTEM)
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
st.subheader("Smart ATS System for Resume Screening & Ranking")


# ======================================================
# MODE SELECTION
# ======================================================
mode = st.radio(
    "Select Mode",
    ["Old System (Rule Based)", "LangGraph + RAG (AI System)"]
)


# ======================================================
# INPUT SECTION
# ======================================================
job_description = st.text_area("Paste Job Description", height=200)

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
        st.warning("Please provide JD and resumes")
        st.stop()

    # --------------------------------------------------
    # EXTRACT RESUMES
    # --------------------------------------------------
    resumes = []
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

        resume_data.append({
            "name": file.name,
            "text": text
        })

        resumes.append(text)

    if not resume_data:
        st.error("None of the uploaded resumes could be read. Please upload text-based PDFs.")
        st.stop()


    # ======================================================
    # OLD SYSTEM
    # ======================================================
    if mode == "Old System (Rule Based)":

        results = []

        for r in resume_data:
            result = score_candidate_against_jd(
                resume_text=r["text"],
                job_description=job_description,
                file_name=r["name"]
            )
            results.append(result)

        ranked_df = rank_candidates(results)


    # ======================================================
    # LANGGRAPH SYSTEM
    # ======================================================
    else:

        output = langgraph_app.invoke({
            "job_description": job_description,
            "resumes": resume_data
        })

        ranked_df = output["ranked"]


    # ======================================================
    # FILTERING
    # ======================================================
    ranked_df = ranked_df[
        ranked_df["Final Score"] >= min_score
    ].reset_index(drop=True)

    if ranked_df.empty:
        st.warning("No candidates meet the minimum score filter.")
        st.stop()

    # ❌ FIX: avoid duplicate Rank column error
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
    st.dataframe(ranked_df, use_container_width=True)


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
    # DETAILED VIEW (RECRUITER STYLE)
    # ======================================================
    st.markdown("## 👤 Candidate Details")

    for _, row in ranked_df.iterrows():

        with st.expander(f"{row['Ran