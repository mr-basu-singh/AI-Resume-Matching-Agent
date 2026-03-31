import streamlit as st
from src.utils.file_handler import extract_text_from_pdf
from src.agents.recruiter_matcher import score_candidate_against_jd
from src.agents.ranker import rank_candidates

st.set_page_config(
    page_title="AI Resume Matching Agent",
    page_icon="📄",
    layout="wide"
)

st.markdown("""
    <style>
        .main-title {
            font-size: 34px;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }
        .sub-text {
            font-size: 16px;
            color: #b0b0b0;
            margin-bottom: 1.5rem;
        }
        .card {
            padding: 18px;
            border-radius: 14px;
            background-color: #111827;
            border: 1px solid #2d3748;
            margin-bottom: 14px;
        }
        .card h3 {
            margin: 0;
            font-size: 16px;
            color: #d1d5db;
        }
        .card p {
            margin: 6px 0 0;
            font-size: 28px;
            font-weight: 700;
            color: white;
        }
        .candidate-box {
            padding: 16px;
            border-radius: 14px;
            background-color: #111827;
            border: 1px solid #2d3748;
            margin-bottom: 12px;
        }
        .candidate-name {
            font-size: 18px;
            font-weight: 700;
            color: white;
        }
        .candidate-score {
            font-size: 24px;
            font-weight: 700;
            color: #22c55e;
        }
        .badge {
            display: inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 600;
            margin-top: 6px;
            margin-bottom: 8px;
        }
        .strong-fit {
            background-color: #14532d;
            color: #bbf7d0;
        }
        .moderate-fit {
            background-color: #78350f;
            color: #fde68a;
        }
        .stretch-fit {
            background-color: #7f1d1d;
            color: #fecaca;
        }
        .not-recommended {
            background-color: #3f3f46;
            color: #e4e4e7;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">AI Resume Matching Agent</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-text">Recruiter mode for screening, scoring, and ranking multiple resumes against one job description.</div>',
    unsafe_allow_html=True
)

with st.container():
    st.markdown("### Job Input")
    job_description = st.text_area("Paste Job Description", height=220)

    uploaded_resumes = st.file_uploader(
        "Upload Candidate Resumes (PDF)",
        type=["pdf"],
        accept_multiple_files=True
    )

    min_score_filter = st.slider("Minimum Final Score Filter", min_value=0, max_value=100, value=0, step=5)

def get_badge_class(recommendation: str) -> str:
    rec = recommendation.lower().strip()
    if "strong" in rec:
        return "strong-fit"
    elif "moderate" in rec:
        return "moderate-fit"
    elif "stretch" in rec:
        return "stretch-fit"
    return "not-recommended"

if st.button("Screen Candidates", use_container_width=True):
    if not job_description or not uploaded_resumes:
        st.warning("Please paste the job description and upload resumes.")
    else:
        candidate_results = []

        progress_bar = st.progress(0)
        status_text = st.empty()

        total_files = len(uploaded_resumes)

        for i, uploaded_file in enumerate(uploaded_resumes, start=1):
            status_text.write(f"Processing {i} of {total_files}: {uploaded_file.name}")

            resume_text = extract_text_from_pdf(uploaded_file)

            result = score_candidate_against_jd(
                resume_text=resume_text,
                job_description=job_description,
                file_name=uploaded_file.name
            )

            candidate_results.append(result)
            progress_bar.progress(i / total_files)

        ranked_df = rank_candidates(candidate_results)

        filtered_df = ranked_df[ranked_df["Final Score"] >= min_score_filter].reset_index(drop=True)
        filtered_df.insert(0, "Filtered Rank", filtered_df.index + 1)

        st.success("Candidate screening completed.")

        total_candidates = len(ranked_df)
        shown_candidates = len(filtered_df)
        top_score = int(ranked_df["Final Score"].max()) if not ranked_df.empty else 0
        avg_score = round(ranked_df["Final Score"].mean(), 1) if not ranked_df.empty else 0

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
                <div class="card">
                    <h3>Total Resumes</h3>
                    <p>{total_candidates}</p>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
                <div class="card">
                    <h3>Shown After Filter</h3>
                    <p>{shown_candidates}</p>
                </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
                <div class="card">
                    <h3>Top Final Score</h3>
                    <p>{top_score}%</p>
                </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
                <div class="card">
                    <h3>Average Final Score</h3>
                    <p>{avg_score}%</p>
                </div>
            """, unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["Overview", "Rankings", "Candidate Details"])

        with tab1:
            st.markdown("### Top 3 Candidates")

            top_candidates = filtered_df.head(3)

            if top_candidates.empty:
                st.info("No candidates match the current filter.")
            else:
                for _, row in top_candidates.iterrows():
                    badge_class = get_badge_class(row["Recommendation"])
                    st.markdown(f"""
                        <div class="candidate-box">
                            <div class="candidate-name">{row['Candidate Name']}</div>
                            <div class="candidate-score">{row['Final Score']}%</div>
                            <div class="badge {badge_class}">{row['Recommendation']}</div>
                            <div><strong>Skill Score:</strong> {row['Skill Score']}</div>
                            <div><strong>Experience Score:</strong> {row['Experience Score']}</div>
                            <div><strong>Project Score:</strong> {row['Project Score']}</div>
                            <div><strong>Education Score:</strong> {row['Education Score']}</div>
                            <div style="margin-top: 8px;"><strong>Matched Skills:</strong> {row['Matched Skills']}</div>
                            <div style="margin-top: 8px;"><strong>Reason:</strong> {row['Reason']}</div>
                        </div>
                    """, unsafe_allow_html=True)

        with tab2:
            st.markdown("### Ranked Candidate Table")
            st.dataframe(filtered_df, use_container_width=True)

            csv = filtered_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Filtered Results as CSV",
                data=csv,
                file_name="ranked_candidates.csv",
                mime="text/csv"
            )

        with tab3:
            st.markdown("### Candidate Breakdown")

            if filtered_df.empty:
                st.info("No candidate details to show.")
            else:
                for _, row in filtered_df.iterrows():
                    badge_class = get_badge_class(row["Recommendation"])
                    with st.expander(f"{row['Candidate Name']} | {row['Final Score']}%"):
                        st.markdown(
                            f'<div class="badge {badge_class}">{row["Recommendation"]}</div>',
                            unsafe_allow_html=True
                        )
                        st.write(f"**Skill Score:** {row['Skill Score']}")
                        st.write(f"**Experience Score:** {row['Experience Score']}")
                        st.write(f"**Project Score:** {row['Project Score']}")
                        st.write(f"**Education Score:** {row['Education Score']}")
                        st.write(f"**Matched Skills:** {row['Matched Skills']}")
                        st.write(f"**Missing Skills:** {row['Missing Skills']}")
                        st.write(f"**Reason:** {row['Reason']}")