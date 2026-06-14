import streamlit as st
import google.generativeai as genai
import pypdf
import re
import plotly.graph_objects as go
import plotly.express as px

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="ATS Resume Analyzer",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# GEMINI SETUP
# ─────────────────────────────────────────────
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        min-height: 100vh;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.05);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }

    /* Header */
    .main-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
    }
    .main-title {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.3rem;
    }
    .main-subtitle {
        color: rgba(255,255,255,0.55);
        font-size: 1rem;
        font-weight: 400;
        letter-spacing: 0.02em;
    }

    /* Score cards */
    .score-card {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease;
    }
    .score-card:hover {
        transform: translateY(-2px);
    }
    .score-label {
        color: rgba(255,255,255,0.5);
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 0.4rem;
    }
    .score-value {
        font-size: 2.8rem;
        font-weight: 700;
        line-height: 1;
    }
    .score-excellent { color: #34d399; }
    .score-good      { color: #60a5fa; }
    .score-average   { color: #fbbf24; }
    .score-poor      { color: #f87171; }

    /* Section cards */
    .section-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 14px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(8px);
    }
    .section-title {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.8rem;
    }
    .title-strengths  { color: #34d399; }
    .title-weaknesses { color: #f87171; }
    .title-keywords   { color: #a78bfa; }
    .title-tips       { color: #60a5fa; }

    /* Bullet items */
    .bullet-item {
        color: rgba(255,255,255,0.85);
        font-size: 0.92rem;
        padding: 0.35rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        line-height: 1.5;
    }
    .bullet-item:last-child { border-bottom: none; }

    /* Keyword badges */
    .badge-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.4rem;
    }
    .badge {
        padding: 0.3rem 0.75rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 500;
        letter-spacing: 0.02em;
    }
    .badge-missing {
        background: rgba(248, 113, 113, 0.15);
        border: 1px solid rgba(248, 113, 113, 0.4);
        color: #fca5a5;
    }
    .badge-present {
        background: rgba(52, 211, 153, 0.12);
        border: 1px solid rgba(52, 211, 153, 0.35);
        color: #6ee7b7;
    }

    /* Status pills */
    .status-pill {
        display: inline-block;
        padding: 0.25rem 0.8rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.04em;
    }

    /* Upload area */
    .upload-hint {
        color: rgba(255,255,255,0.4);
        font-size: 0.82rem;
        margin-top: 0.3rem;
    }

    /* Divider */
    .divider {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.08);
        margin: 1.5rem 0;
    }

    /* Info box */
    .info-box {
        background: rgba(96, 165, 250, 0.08);
        border: 1px solid rgba(96, 165, 250, 0.2);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        color: rgba(255,255,255,0.75);
        font-size: 0.88rem;
        line-height: 1.6;
    }

    /* Streamlit overrides */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed, #4f46e5);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 2rem;
        font-weight: 600;
        font-size: 0.95rem;
        width: 100%;
        transition: opacity 0.2s;
    }
    .stButton > button:hover {
        opacity: 0.88;
        border: none;
    }
    .stTextArea textarea {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 10px !important;
        color: rgba(255,255,255,0.85) !important;
        font-size: 0.88rem !important;
    }
    div[data-testid="stFileUploader"] {
        background: rgba(255,255,255,0.04);
        border: 1.5px dashed rgba(167,139,250,0.4);
        border-radius: 12px;
        padding: 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255,255,255,0.04);
        border-radius: 10px;
        padding: 0.2rem;
        gap: 0.2rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: rgba(255,255,255,0.55) !important;
        font-size: 0.88rem;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(124,58,237,0.35) !important;
        color: white !important;
    }
    div[data-testid="metric-container"] {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 0.8rem;
    }
    label, .stTextArea label {
        color: rgba(255,255,255,0.65) !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def extract_text_from_pdf(uploaded_file) -> tuple[str, int]:
    """Extract text from uploaded PDF. Returns (text, page_count)."""
    reader = pypdf.PdfReader(uploaded_file)
    pages = len(reader.pages)
    text = ""
    for page in reader.pages:
        text += (page.extract_text() or "") + "\n"
    return text.strip(), pages


def score_color_class(score: int) -> str:
    if score >= 80:
        return "score-excellent"
    elif score >= 65:
        return "score-good"
    elif score >= 45:
        return "score-average"
    return "score-poor"


def score_label(score: int) -> str:
    if score >= 80:
        return "Excellent"
    elif score >= 65:
        return "Good"
    elif score >= 45:
        return "Needs Work"
    return "Poor"


def parse_score(pattern: str, text: str) -> int:
    """Safely extract a numeric score from AI output."""
    match = re.search(pattern, text)
    if match:
        try:
            return max(0, min(100, int(match.group(1))))
        except ValueError:
            return 0
    return 0


def parse_list_section(header: str, text: str) -> list[str]:
    """Extract a bullet-point section from the AI response."""
    pattern = rf"{header}[:\-]?\s*\n(.*?)(?=\n[A-Z_]{{3,}}:|\Z)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if not match:
        return []
    block = match.group(1).strip()
    items = []
    for line in block.splitlines():
        line = re.sub(r"^[\-\*\•\d\.\s]+", "", line).strip()
        if line and len(line) > 3:
            items.append(line)
    return items[:8]  # cap at 8 items


def parse_keywords(header: str, text: str) -> list[str]:
    """Extract comma-separated keywords from AI output."""
    pattern = rf"{header}[:\-]?\s*\n?(.*?)(?=\n[A-Z_]{{3,}}:|\Z)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if not match:
        return []
    raw = match.group(1).strip()
    keywords = [k.strip().strip("*-•") for k in re.split(r"[,\n]", raw)]
    return [k for k in keywords if k and len(k) > 1][:15]


def build_prompt(resume_text: str, job_description: str, has_jd: bool) -> str:
    """Build a structured prompt for Gemini."""
    resume_snippet = resume_text[:4000]  # Prevent token overflow

    if has_jd:
        jd_snippet = job_description[:2000]
        return f"""
You are an expert ATS (Applicant Tracking System) and resume coach.
Analyze the resume below against the job description provided.

Respond ONLY using the exact format below. Do not add any extra commentary, markdown headers, or preamble.

ATS_SCORE: [integer 0-100]
MATCH_SCORE: [integer 0-100]

STRENGTHS:
- [strength 1]
- [strength 2]
- [strength 3]
- [strength 4]

WEAKNESSES:
- [weakness 1]
- [weakness 2]
- [weakness 3]

MISSING_KEYWORDS:
[keyword1], [keyword2], [keyword3], [keyword4], [keyword5]

PRESENT_KEYWORDS:
[keyword1], [keyword2], [keyword3], [keyword4], [keyword5]

IMPROVEMENT_TIPS:
- [specific actionable tip 1]
- [specific actionable tip 2]
- [specific actionable tip 3]
- [specific actionable tip 4]

--- RESUME ---
{resume_snippet}

--- JOB DESCRIPTION ---
{jd_snippet}
"""
    else:
        return f"""
You are an expert ATS (Applicant Tracking System) and resume coach.
Analyze the resume below and give a general ATS quality score and feedback.

Respond ONLY using the exact format below. Do not add any extra commentary.

ATS_SCORE: [integer 0-100]
MATCH_SCORE: N/A

STRENGTHS:
- [strength 1]
- [strength 2]
- [strength 3]

WEAKNESSES:
- [weakness 1]
- [weakness 2]
- [weakness 3]

MISSING_KEYWORDS:
[general keywords commonly expected in resumes for this field]

PRESENT_KEYWORDS:
[keywords found in this resume]

IMPROVEMENT_TIPS:
- [specific actionable tip 1]
- [specific actionable tip 2]
- [specific actionable tip 3]

--- RESUME ---
{resume_snippet}
"""


def make_gauge(score: int, title: str) -> go.Figure:
    """Create a Plotly gauge chart for a score."""
    if score >= 80:
        color = "#34d399"
    elif score >= 65:
        color = "#60a5fa"
    elif score >= 45:
        color = "#fbbf24"
    else:
        color = "#f87171"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": title, "font": {"size": 13, "color": "rgba(255,255,255,0.6)"}},
        number={"font": {"size": 36, "color": color}, "suffix": "%"},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickwidth": 1,
                "tickcolor": "rgba(255,255,255,0.15)",
                "tickfont": {"color": "rgba(255,255,255,0.3)", "size": 10}
            },
            "bar": {"color": color, "thickness": 0.25},
            "bgcolor": "rgba(0,0,0,0)",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 45],  "color": "rgba(248,113,113,0.12)"},
                {"range": [45, 65], "color": "rgba(251,191,36,0.12)"},
                {"range": [65, 80], "color": "rgba(96,165,250,0.12)"},
                {"range": [80, 100],"color": "rgba(52,211,153,0.12)"},
            ],
        }
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "white"},
        height=200,
        margin=dict(t=40, b=10, l=20, r=20),
    )
    return fig


def render_bullets(items: list[str], icon: str = "•"):
    for item in items:
        st.markdown(f'<div class="bullet-item">{icon} {item}</div>', unsafe_allow_html=True)


def render_badges(keywords: list[str], badge_class: str):
    if not keywords:
        st.markdown('<p style="color:rgba(255,255,255,0.3);font-size:0.85rem;">None detected</p>', unsafe_allow_html=True)
        return
    badges = "".join(
        f'<span class="badge {badge_class}">{kw}</span>' for kw in keywords
    )
    st.markdown(f'<div class="badge-container">{badges}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding: 0.5rem 0 1.5rem 0;">
        <div style="font-size:1.4rem;font-weight:700;color:white;margin-bottom:0.3rem;">🎯 ATS Analyzer</div>
        <div style="font-size:0.78rem;color:rgba(255,255,255,0.4);letter-spacing:0.04em;">by Javed · AI Resume Tools</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="color:rgba(255,255,255,0.5);font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem;">Upload Resume</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Upload your resume (PDF)",
        type=["pdf"],
        label_visibility="collapsed"
    )
    st.markdown('<div class="upload-hint">Accepts text-based PDFs only</div>', unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    st.markdown('<div style="color:rgba(255,255,255,0.5);font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.5rem;">Job Description <span style="color:rgba(255,255,255,0.25);font-weight:400;">(optional)</span></div>', unsafe_allow_html=True)
    job_description = st.text_area(
        "Paste the job description",
        height=180,
        placeholder="Paste the job description here for a match score...",
        label_visibility="collapsed"
    )

    analyze_btn = st.button("Analyze Resume →", use_container_width=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown("""
    <div class="info-box">
        <strong style="color:rgba(255,255,255,0.8);">How it works</strong><br><br>
        1. Upload your resume PDF<br>
        2. Optionally paste a job description<br>
        3. Get your ATS score, keyword gaps, and actionable tips instantly
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MAIN AREA
# ─────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <div class="main-title">ATS Resume Analyzer</div>
    <div class="main-subtitle">Know exactly why your resume gets filtered out — before you apply</div>
</div>
""", unsafe_allow_html=True)


# ── No file uploaded state ──
if not uploaded_file:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align:center;padding:3rem 0;color:rgba(255,255,255,0.25);">
            <div style="font-size:3rem;margin-bottom:1rem;">📄</div>
            <div style="font-size:1rem;font-weight:500;margin-bottom:0.4rem;color:rgba(255,255,255,0.4);">Upload your resume to get started</div>
            <div style="font-size:0.82rem;">Supports text-based PDFs</div>
        </div>
        """, unsafe_allow_html=True)
    st.stop()


# ── File uploaded, not yet analyzed ──
resume_text, page_count = None, 0

if uploaded_file:
    try:
        resume_text, page_count = extract_text_from_pdf(uploaded_file)
    except Exception as e:
        st.error(f"Failed to read PDF: {e}")
        st.stop()

    if not resume_text.strip():
        st.error("⚠️ No text could be extracted from your PDF. It may be a scanned image. Please upload a text-based PDF.")
        st.stop()

    word_count = len(resume_text.split())
    st.markdown(f"""
    <div style="display:flex;gap:1rem;justify-content:center;margin-bottom:1.5rem;">
        <span style="background:rgba(52,211,153,0.12);border:1px solid rgba(52,211,153,0.25);color:#6ee7b7;padding:0.25rem 0.8rem;border-radius:999px;font-size:0.78rem;font-weight:600;">
            ✓ Resume loaded
        </span>
        <span style="color:rgba(255,255,255,0.35);font-size:0.78rem;padding:0.25rem 0;">
            {page_count} page{'s' if page_count != 1 else ''} · ~{word_count:,} words
        </span>
        {"<span style='background:rgba(96,165,250,0.12);border:1px solid rgba(96,165,250,0.25);color:#93c5fd;padding:0.25rem 0.8rem;border-radius:999px;font-size:0.78rem;font-weight:600;'>+ Job Description</span>" if job_description.strip() else ""}
    </div>
    """, unsafe_allow_html=True)


# ── Analysis ──
if analyze_btn and resume_text:
    has_jd = bool(job_description.strip())
    prompt = build_prompt(resume_text, job_description, has_jd)

    with st.spinner("Analyzing your resume with Gemini AI..."):
        try:
            response = model.generate_content(prompt)
            raw_output = response.text
        except Exception as e:
            st.error(f"Gemini API error: {e}")
            st.stop()

    # ── Parse scores ──
    ats_score   = parse_score(r"ATS_SCORE:\s*(\d+)", raw_output)
    match_score = parse_score(r"MATCH_SCORE:\s*(\d+)", raw_output) if has_jd else None

    # ── Parse sections ──
    strengths        = parse_list_section("STRENGTHS", raw_output)
    weaknesses       = parse_list_section("WEAKNESSES", raw_output)
    improvement_tips = parse_list_section("IMPROVEMENT_TIPS", raw_output)
    missing_keywords = parse_keywords("MISSING_KEYWORDS", raw_output)
    present_keywords = parse_keywords("PRESENT_KEYWORDS", raw_output)

    # ─────────────────────────────────────────
    # SCORE GAUGES
    # ─────────────────────────────────────────
    if has_jd:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.plotly_chart(make_gauge(ats_score, "ATS Score"), use_container_width=True, config={"displayModeBar": False})
        with col2:
            st.plotly_chart(make_gauge(match_score, "Job Match"), use_container_width=True, config={"displayModeBar": False})
        with col3:
            # Overall score = weighted average
            overall = int(ats_score * 0.5 + match_score * 0.5)
            st.markdown(f"""
            <div class="score-card" style="margin-top:1.5rem;">
                <div class="score-label">Overall Rating</div>
                <div class="score-value {score_color_class(overall)}">{overall}</div>
                <div style="color:rgba(255,255,255,0.4);font-size:0.78rem;margin-top:0.4rem;">{score_label(overall)}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.plotly_chart(make_gauge(ats_score, "ATS Score"), use_container_width=True, config={"displayModeBar": False})
        with col3:
            st.markdown(f"""
            <div class="score-card" style="margin-top:1.5rem;">
                <div class="score-label">Rating</div>
                <div class="score-value {score_color_class(ats_score)}">{score_label(ats_score)}</div>
                <div style="color:rgba(255,255,255,0.4);font-size:0.78rem;margin-top:0.4rem;">ATS General Score</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ─────────────────────────────────────────
    # TABS
    # ─────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["📊 Analysis", "🔍 Keywords", "💡 Tips"])

    # ── Tab 1: Analysis ──
    with tab1:
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("""
            <div class="section-card">
                <div class="section-title title-strengths">💪 Strengths</div>
            """, unsafe_allow_html=True)
            if strengths:
                render_bullets(strengths, "✓")
            else:
                st.markdown('<p style="color:rgba(255,255,255,0.3);font-size:0.85rem;">No strengths detected</p>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_b:
            st.markdown("""
            <div class="section-card">
                <div class="section-title title-weaknesses">⚠️ Weaknesses</div>
            """, unsafe_allow_html=True)
            if weaknesses:
                render_bullets(weaknesses, "✗")
            else:
                st.markdown('<p style="color:rgba(255,255,255,0.3);font-size:0.85rem;">No weaknesses detected</p>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # No-JD info message
        if not has_jd:
            st.markdown("""
            <div class="info-box" style="margin-top:0.5rem;">
                💡 <strong style="color:rgba(255,255,255,0.8);">Add a job description</strong> to unlock your Job Match Score 
                and see which specific keywords are missing from your resume.
            </div>
            """, unsafe_allow_html=True)

    # ── Tab 2: Keywords ──
    with tab2:
        if has_jd:
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("""
                <div class="section-card">
                    <div class="section-title title-keywords">❌ Missing Keywords</div>
                """, unsafe_allow_html=True)
                render_badges(missing_keywords, "badge-missing")
                st.markdown("</div>", unsafe_allow_html=True)

            with col_b:
                st.markdown("""
                <div class="section-card">
                    <div class="section-title title-strengths">✅ Present Keywords</div>
                """, unsafe_allow_html=True)
                render_badges(present_keywords, "badge-present")
                st.markdown("</div>", unsafe_allow_html=True)

            # Keyword coverage bar chart
            if missing_keywords or present_keywords:
                total = len(missing_keywords) + len(present_keywords)
                present_pct = round(len(present_keywords) / total * 100) if total else 0
                missing_pct = 100 - present_pct

                fig_bar = go.Figure(go.Bar(
                    x=[present_pct, missing_pct],
                    y=["Keyword Coverage"],
                    orientation="h",
                    marker_color=["#34d399", "#f87171"],
                    text=[f"{present_pct}% present", f"{missing_pct}% missing"],
                    textposition="inside",
                    textfont={"size": 12, "color": "white"},
                ))
                fig_bar.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font={"color": "white"},
                    height=80,
                    margin=dict(t=5, b=5, l=0, r=0),
                    xaxis={"visible": False},
                    yaxis={"visible": False},
                    barmode="stack",
                    showlegend=False,
                )
                st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
        else:
            st.markdown("""
            <div class="info-box">
                🔍 <strong style="color:rgba(255,255,255,0.8);">Paste a job description</strong> in the sidebar 
                to see which keywords your resume is missing and which ones are already present.
            </div>
            """, unsafe_allow_html=True)

            # Still show present keywords from general analysis
            if present_keywords:
                st.markdown("""
                <div class="section-card" style="margin-top:1rem;">
                    <div class="section-title title-strengths">✅ Keywords Detected in Your Resume</div>
                """, unsafe_allow_html=True)
                render_badges(present_keywords, "badge-present")
                st.markdown("</div>", unsafe_allow_html=True)

    # ── Tab 3: Tips ──
    with tab3:
        st.markdown("""
        <div class="section-card">
            <div class="section-title title-tips">💡 Improvement Tips</div>
        """, unsafe_allow_html=True)
        if improvement_tips:
            for i, tip in enumerate(improvement_tips, 1):
                st.markdown(f"""
                <div class="bullet-item">
                    <span style="color:#a78bfa;font-weight:600;margin-right:0.5rem;">{i:02d}.</span> {tip}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<p style="color:rgba(255,255,255,0.3);font-size:0.85rem;">No tips generated</p>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)

    # ─────────────────────────────────────────
    # DOWNLOAD REPORT
    # ─────────────────────────────────────────
    jd_section = f"\nJOB MATCH SCORE: {match_score}%\n" if has_jd else ""
    missing_kw_text = ", ".join(missing_keywords) if missing_keywords else "None"
    present_kw_text = ", ".join(present_keywords) if present_keywords else "None"
    strengths_text  = "\n".join(f"  • {s}" for s in strengths)
    weaknesses_text = "\n".join(f"  • {w}" for w in weaknesses)
    tips_text       = "\n".join(f"  {i+1:02d}. {t}" for i, t in enumerate(improvement_tips))

    report = f"""ATS RESUME ANALYSIS REPORT
{'='*50}

ATS SCORE: {ats_score}%{jd_section}

STRENGTHS
---------
{strengths_text}

WEAKNESSES
----------
{weaknesses_text}

MISSING KEYWORDS
----------------
{missing_kw_text}

PRESENT KEYWORDS
----------------
{present_kw_text}

IMPROVEMENT TIPS
----------------
{tips_text}

{'='*50}
Generated by ATS Resume Analyzer · Built by Javed
"""

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.download_button(
            label="⬇ Download Full Report",
            data=report,
            file_name="ats_analysis_report.txt",
            mime="text/plain",
            use_container_width=True
        )