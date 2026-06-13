
import streamlit as st
import base64
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide"
)
from pypdf import PdfReader
import google.generativeai as genai
import re
def get_base64(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()
# Configure Gemini
genai.configure(
    api_key=st.secrets["GEMINI_API_KEY"]
)

model = genai.GenerativeModel("gemini-2.5-flash")


bg_image = get_base64("assets/background.png")

st.markdown(
    f"""
    <style>

    .stApp {{
        background-image: url("data:image/png;base64,{bg_image}");
        background-size: cover;
        background-repeat: no-repeat;
        background-position: center center;
        background-position: center;
        background-attachment: fixed;
    }}
    .main {{
        padding-top: 2rem;
    }}

    h1,h2,h3,p,label {{
        color:white !important;
    }}

    .stButton button {{
 
        width:100%;
        border:none;

        background: linear-gradient(
             90deg,
            #6366f1,
             #8b5cf6
        );

    color:white;
    border-radius:14px;
    height:55px;
    font-size:18px;
    font-weight:bold;
}}



[data-testid="stMetric"] {{

    background: rgba(255,255,255,0.08);

    border:1px solid rgba(
        255,255,255,0.1
    );

    border-radius:15px;

    padding:20px;
}}

    .main {{

        padding-top: 2rem;

        background: rgba(0,0,0,0.45);

        border-radius: 20px;

        padding: 20px;
        }}

        section[data-testid="stSidebar"] {{

        background: rgba(0,0,0,0.55);

        backdrop-filter: blur(15px);
    }}

    h1,h2,h3,p,label {{
        color:white !important;
}}

    </style>
    """,
    unsafe_allow_html=True
)

with st.sidebar:

    st.title("📄 Resume Analyzer")

    st.info("""
    Built using:

    • Python
    • Streamlit
    • Gemini AI
    • PyPDF
    """)
    st.markdown("### Resume Tips")

    st.markdown("""
        ✅ Keep resume 1 page

        ✅ Add GitHub projects

        ✅ Use action verbs

        ✅ Quantify achievements
    """)
    st.success("AI-Powered Career Assistant")

st.markdown("""
<style>

section[data-testid="stSidebar"] {
    background: rgba(0,0,0,0.3);
    backdrop-filter: blur(20px);
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="
padding:40px;
border-radius:20px;
background:rgba(0,0,0,0.45);
box-shadow:0 0 30px rgba(124,58,237,0.4);
backdrop-filter:blur(10px);
margin-bottom:30px;
">

<h1>🚀 AI Resume Analyzer</h1>

<h3>
Analyze resumes using AI and optimize your career.
</h3>

<p>
✔ ATS Score<br>
✔ Resume Feedback<br>
✔ Job Matching<br>
✔ Missing Skills Detection
</p>

</div>
""", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

with col1:
    st.info("📊 ATS Score")

with col2:
    st.info("🎯 Job Matching")

with col3:
    st.info("🤖 AI Feedback")

st.markdown("""
<style>

section[data-testid="stSidebar"] {
    background: rgba(0,0,0,0.3);
    backdrop-filter: blur(20px);
}

</style>
""", unsafe_allow_html=True)

job_description = st.text_area(
    "📋 Paste Job Description (Optional)",
    height=200,
    placeholder="Paste the job description here..."
)

uploaded_file = st.file_uploader(
    "Upload your resume",
    type=["pdf"]
)

if uploaded_file:

    reader = PdfReader(uploaded_file)

    resume_text = ""

    for page in reader.pages:
        text = page.extract_text()

        if text:
            resume_text += text

    st.success("Resume uploaded successfully!")
    st.write(resume_text[:1000])
    if st.button("Analyze Resume"):

        with st.spinner("🤖 AI is analyzing your resume..."):

            prompt = f"""
            You are an expert ATS system, recruiter, and career coach.
            Provide the ATS score in this exact format:

            ATS_SCORE: XX
            Analyze the following resume.

            Provide your response in exactly this format:

            # ATS Score
            Score: X/100



            MATCH_SCORE: XX

            # Strengths
            ...

            # Weaknesses
            ...

            # Missing Skills
            ...

            # Missing Keywords
            ...

            # Suggestions
            ...

            # Final Verdict
            ...
            """

            response = model.generate_content(prompt)

            analysis = response.text

            match = re.search(r"ATS_SCORE:\s*(\d+)", analysis)
            job_match = re.search(
                r"MATCH_SCORE:\s*(\d+)",
                analysis
            )

            if job_match:
                match_score = int(job_match.group(1))
            else:
                match_score = 0
            if match:
                ats_score = int(match.group(1))
            else:
                ats_score = 0

            st.markdown("## 📊 ATS Dashboard")

            if ats_score >= 80:
                st.success(f"ATS Score: {ats_score}/100")
            elif ats_score >= 60:              
                st.warning(f"ATS Score: {ats_score}/100")
            else:
                st.error(f"ATS Score: {ats_score}/100")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "ATS Score",
                    f"{ats_score}/100"
            )

            with col2:
                st.metric(
                    "Job Match",
                    f"{match_score}%"
                    )

            with col3:
                st.metric(
                    "Pages",
                    len(reader.pages)
                )
            tab1, tab2 = st.tabs([
                "📊 Resume Analysis",
                "🎯 Job Match"
            ])

            with tab1:

                st.subheader("Resume Analysis")

                st.markdown(analysis)

            with tab2:

                st.subheader("Job Match")
                
                if job_description:

                    if match_score >= 80:
                        st.success("Excellent Match")
                    elif match_score >= 60:
                        st.warning("Moderate Match")
                    else:
                        st.error("Poor Match")
                    st.metric(
                        "Job Match Score",
                        f"{match_score}%"
                    )

                    st.progress(match_score/100)
                    st.markdown("""
                    Job matching analysis is included in the report above.

                    Future upgrade:
                    - Match %
                    - Missing Skills
                    - Missing Keywords
                    - Improvement Suggestions
                    """)
                else:

                    st.warning(
                        "Paste a job description to use this feature."
                    )

                st.download_button(
                    "📥 Download Analysis",
                    analysis,
                    "resume_report.txt"
                )