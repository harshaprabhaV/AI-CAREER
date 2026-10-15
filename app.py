
import base64
from pathlib import Path

import requests
import streamlit as st

# =========================================================
# CONFIGURATION
# =========================================================
API_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 180

st.set_page_config(
    page_title="AI Career Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =========================================================
# BACKGROUND IMAGE
# Put background.jpg in the same folder as app.py
# =========================================================
BG_PATH = Path(__file__).parent / "background.jpg"

if BG_PATH.exists():
    encoded_image = base64.b64encode(
        BG_PATH.read_bytes()
    ).decode("utf-8")

    background_style = f"""
        background-image:
            linear-gradient(
                rgba(10, 9, 8, 0.78),
                rgba(10, 9, 8, 0.86)
            ),
            url("data:image/jpeg;base64,{encoded_image}");
    """
else:
    background_style = """
        background:
            radial-gradient(
                circle at top right,
                rgba(115, 88, 55, 0.20),
                transparent 40%
            ),
            #100F0D;
    """

# =========================================================
# DARK + CREAM THEME
# =========================================================
st.markdown(
    f"""
    <style>
    :root {{
        --cream: #F5E8CC;
        --muted-cream: #D6C7AC;
        --gold: #D6B77A;
        --glass: rgba(18, 16, 14, 0.76);
    }}

    .stApp {{
        {background_style}
        background-position: center;
        background-size: cover;
        background-attachment: fixed;
        color: var(--cream);
    }}

    header, footer {{
        visibility: hidden;
    }}

    [data-testid="stSidebar"] {{
        background: rgba(15, 13, 11, 0.95);
    }}

    .block-container {{
        max-width: 1500px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }}

    h1, h2, h3, h4, p, label, li,
    .stMarkdown,
    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"] {{
        color: var(--cream) !important;
    }}

    .hero-title {{
        color: var(--gold);
        font-size: clamp(32px, 4vw, 48px);
        font-weight: 850;
        letter-spacing: -1px;
        margin-bottom: 4px;
    }}

    .hero-description {{
        color: var(--muted-cream);
        font-size: 17px;
        line-height: 1.8;
        margin-bottom: 18px;
    }}

    .section-label {{
        color: var(--gold);
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 3px;
        text-transform: uppercase;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stMetric"] {{
        background: var(--glass);
        border: 1px solid rgba(214, 183, 122, 0.22);
        border-radius: 18px;
        padding: 15px;
        backdrop-filter: blur(12px);
    }}

    div[data-testid="stMetric"] {{
        min-height: 115px;
    }}

    .stButton > button {{
        min-height: 52px;
        border-radius: 12px;
        border: 1px solid rgba(214, 183, 122, 0.40);
        background: rgba(26, 23, 19, 0.88);
        color: var(--cream) !important;
        font-size: 15px;
        font-weight: 700;
        transition: all 0.2s ease;
    }}

    .stButton > button:hover {{
        background: rgba(214, 183, 122, 0.20);
        border-color: var(--gold);
        transform: translateY(-2px);
    }}

    .stButton > button:focus {{
        border-color: var(--gold);
        color: var(--cream) !important;
    }}

    div[data-testid="stFileUploader"],
    div[data-testid="stTextInput"],
    div[data-testid="stTextArea"],
    div[data-testid="stSelectbox"] {{
        background: rgba(20, 18, 16, 0.55);
        border-radius: 12px;
    }}

    input, textarea {{
        color: var(--cream) !important;
    }}

    [data-testid="stCaptionContainer"] {{
        color: var(--muted-cream) !important;
    }}

    [data-testid="stAlert"] {{
        background: rgba(25, 22, 18, 0.88);
        border-radius: 12px;
    }}

    hr {{
        border-color: rgba(214, 183, 122, 0.24);
    }}

    [data-testid="stDataFrame"] {{
        background: rgba(18, 16, 14, 0.8);
        border-radius: 12px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# =========================================================
# SESSION STATE
# =========================================================
defaults = {
    "page": "Home",
    "resume_uploaded": False,
    "resume_data": None,
    "jobs": None,
}

for key, default_value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

# =========================================================
# NAVIGATION
# No radio buttons; larger horizontal navbar
# =========================================================
st.markdown(
    """
    <div class="section-label">YOUR PERSONAL CAREER PLATFORM</div>
    <div class="hero-title">AI Career Assistant</div>
    <div class="hero-description">
        Discover opportunities. Build skills. Shape your future.
    </div>
    """,
    unsafe_allow_html=True
)

pages = [
    ("🏠", "Home"),
    ("📄", "Resume"),
    ("💼", "Jobs"),
    ("🧠", "Skills"),
    ("📚", "Roadmap"),
    ("🎤", "Interview"),
    ("✨", "Advisor"),
]

nav_columns = st.columns(7)

for column, (emoji, page_name) in zip(nav_columns, pages):
    with column:
        button_label = f"{emoji}  {page_name}"

        if st.session_state.page == page_name:
            button_label = f"✦ {button_label}"

        if st.button(
            button_label,
            key=f"nav_{page_name}",
            use_container_width=True
        ):
            st.session_state.page = page_name
            st.rerun()

selected = st.session_state.page
st.divider()

# =========================================================
# API HELPERS
# =========================================================
def api_error(response):
    try:
        detail = response.json().get(
            "detail",
            response.text
        )
    except (ValueError, AttributeError):
        detail = response.text

    st.error(
        f"API error ({response.status_code}): {detail}"
    )


def require_resume():
    if not st.session_state.resume_uploaded:
        st.warning(
            "Please upload and analyze your resume "
            "from the Resume page first."
        )
        return False

    return True


def api_get(endpoint, timeout=REQUEST_TIMEOUT):
    try:
        response = requests.get(
            f"{API_URL}/{endpoint}",
            timeout=timeout
        )

        if response.ok:
            return response.json()

        api_error(response)

    except requests.RequestException as exc:
        st.error(f"Backend connection failed: {exc}")

    return None


def api_post(endpoint, payload, timeout=REQUEST_TIMEOUT):
    try:
        response = requests.post(
            f"{API_URL}/{endpoint}",
            json=payload,
            timeout=timeout
        )

        if response.ok:
            return response.json()

        api_error(response)

    except requests.RequestException as exc:
        st.error(f"Backend connection failed: {exc}")

    return None


# =========================================================
# HOME
# =========================================================
if selected == "Home":

    st.markdown(
        """
        <div class="hero-title">Build Your AI Career</div>
        <div class="hero-description">
            Your resume is the starting point.
            Find matching jobs, identify skill gaps,
            and plan your next career move.
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Resume Analysis", "PDF")
        st.caption("Extract skills from your resume.")

    with col2:
        st.metric("Job Matching", "Personalized")
        st.caption("Explore jobs from your local dataset.")

    with col3:
        st.metric("Career Roadmap", "90 Days")
        st.caption("Build a structured learning plan.")

    st.write("")

    left, right = st.columns([1.5, 1])

    with left:
        with st.container(border=True):
            st.subheader("Your career workspace")
            st.write(
                "Upload your resume to explore your current "
                "skills and career opportunities."
            )

            if st.session_state.resume_uploaded:
                st.success("Your resume has been analyzed.")
                if st.button(
                    "View Resume",
                    use_container_width=True
                ):
                    st.session_state.page = "Resume"
                    st.rerun()
            else:
                if st.button(
                    "Get Started →",
                    use_container_width=True
                ):
                    st.session_state.page = "Resume"
                    st.rerun()

    with right:
        with st.container(border=True):
            st.subheader("System status")

            try:
                response = requests.get(
                    f"{API_URL}/health",
                    timeout=5
                )

                if response.ok:
                    st.success("Backend connected")
                else:
                    st.warning(
                        f"Backend returned status "
                        f"{response.status_code}"
                    )

            except requests.RequestException:
                st.error("Backend is offline")
                st.caption(
                    "Start it using: "
                    "uvicorn main:app --reload --port 8000"
                )

# =========================================================
# RESUME ANALYSIS
# =========================================================
elif selected == "Resume":

    st.subheader("📄 Resume Analysis")
    st.write(
        "Upload your PDF resume to extract your skills "
        "and begin your career analysis."
    )

    uploaded_file = st.file_uploader(
        "Upload your resume",
        type=["pdf"],
        key="resume_uploader"
    )

    if uploaded_file and st.button(
        "🚀 Analyze Resume",
        use_container_width=True
    ):
        try:
            with st.spinner("Analyzing your resume..."):
                response = requests.post(
                    f"{API_URL}/upload-resume",
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/pdf"
                        )
                    },
                    timeout=REQUEST_TIMEOUT
                )

            if response.ok:
                st.session_state.resume_data = response.json()
                st.session_state.resume_uploaded = True
                st.session_state.jobs = None

                st.success(
                    "Resume uploaded and analyzed successfully!"
                )
            else:
                api_error(response)

        except requests.RequestException as exc:
            st.error(
                f"Cannot connect to backend: {exc}. "
                "Start FastAPI in another terminal."
            )

    data = st.session_state.resume_data

    if data:
        st.divider()
        st.subheader("Resume summary")

        st.write(
            f"**File:** {data.get('filename', 'Resume')}"
        )
        st.write(
            f"**Characters extracted:** "
            f"{data.get('characters', 0)}"
        )

        skills = data.get("skills", [])

        st.write(
            "**Detected skills:** "
            + (", ".join(skills) if skills else "No skills detected")
        )

        if skills:
            st.subheader("Your skills")
            st.write(" · ".join(skills))

        with st.expander("Preview extracted resume text"):
            st.text(data.get("resume_text", ""))

# =========================================================
# JOB RECOMMENDATIONS
# =========================================================
elif selected == "Jobs":

    st.subheader("💼 Matching Job Opportunities")

    if require_resume():

        if st.button(
            "🔎 Find Matching Jobs",
            use_container_width=True
        ):
            with st.spinner("Finding matching jobs..."):
                result = api_get("jobs")

            if result is not None:
                st.session_state.jobs = result.get("jobs", [])

                if not st.session_state.jobs:
                    st.info(
                        result.get(
                            "message",
                            "No matching jobs found."
                        )
                    )

        jobs = st.session_state.jobs

        if jobs is None:
            st.info(
                "Click **Find Matching Jobs** to load recommendations."
            )

        elif not jobs:
            st.info("No job recommendations are available yet.")

        else:
            st.write(f"Found **{len(jobs)}** job recommendations.")

            for index, job in enumerate(jobs, start=1):
                with st.container(border=True):

                    st.subheader(
                        f"{index}. {job.get('title', 'Unknown role')}"
                    )

                    st.write(
                        f"**Company:** "
                        f"{job.get('company', 'Not specified')}"
                    )

                    st.write(
                        f"**Location:** "
                        f"{job.get('job_location', 'Not specified')}"
                    )

                    st.write(
                        f"**Level:** "
                        f"{job.get('level', 'Not specified')}"
                    )

                    score = job.get("final_match_score", 0)

                    try:
                        st.metric(
                            "Match score",
                            f"{float(score):.1f}%"
                        )
                    except (ValueError, TypeError):
                        st.metric("Match score", str(score))

                    matched_skills = job.get("matched_skills", [])

                    if matched_skills:
                        st.write(
                            "**Matching skills:** "
                            + ", ".join(matched_skills)
                        )

                    description = job.get("description")

                    if description:
                        with st.expander("View job description"):
                            st.write(description)

# =========================================================
# SKILL ANALYSIS
# =========================================================
elif selected == "Skills":

    st.subheader("🧠 Skills Analysis")

    if require_resume():

        with st.spinner("Loading your skill analysis..."):
            data = api_get("skills", timeout=30)

        if data is not None:

            st.metric(
                "Detected skills",
                data.get("total_skills", 0)
            )

            detected = data.get("detected_skills", [])
            suggested = data.get("suggested_core_skills", [])

            st.write("### Your current skills")

            if detected:
                st.write(" · ".join(detected))
            else:
                st.info("No skills detected yet.")

            st.write("### Skills to review")

            if suggested:
                for skill in suggested:
                    st.markdown(f"- {skill}")
            else:
                st.info("No additional skill suggestions available.")

            note = data.get("note", "")

            if note:
                st.caption(note)

# =========================================================
# CAREER ROADMAP
# =========================================================
elif selected == "Roadmap":

    st.subheader("📚 Your Career Roadmap")

    if require_resume():

        with st.spinner("Building your roadmap..."):
            roadmap = api_get("roadmap", timeout=30)

        if roadmap is not None:

            if not roadmap:
                st.info("No roadmap is available yet.")

            for phase, details in roadmap.items():

                with st.container(border=True):
                    st.header(
                        phase.replace("_", " ").title()
                    )

                    st.write(
                        "**Focus:** "
                        + details.get("focus", "Not specified")
                    )

                    st.write("**Skills to learn**")

                    skills = details.get("skills", [])

                    if skills:
                        for skill in skills:
                            st.markdown(f"- {skill}")
                    else:
                        st.write("No skills listed.")

                    st.write("**Suggested projects**")

                    projects = details.get("projects", [])

                    if projects:
                        for project in projects:
                            st.markdown(f"- {project}")
                    else:
                        st.write("No projects listed.")

                    st.write(
                        "**Expected outcome:** "
                        + details.get("outcome", "Not specified")
                    )

# =========================================================
# MOCK INTERVIEW
# =========================================================
elif selected == "Interview":

    st.subheader("🎤 Mock Interview")
    st.write(
        "Submit your answer to receive feedback from "
        "the configured backend."
    )

    question = st.text_input(
        "Interview question",
        placeholder="Tell me about a project you worked on."
    )

    difficulty = st.selectbox(
        "Difficulty",
        ["Easy", "Medium", "Hard"],
        index=1
    )

    answer = st.text_area(
        "Your answer",
        height=200,
        placeholder="Write your answer here..."
    )

    if st.button(
        "Evaluate Answer",
        use_container_width=True
    ):

        if not answer.strip():
            st.warning("Please enter your answer first.")

        else:
            payload = {
                "question": question.strip(),
                "answer": answer.strip(),
                "difficulty": difficulty
            }

            with st.spinner("Evaluating your answer..."):
                result = api_post(
                    "interview/evaluate",
                    payload,
                    timeout=60
                )

            if result is not None:

                st.divider()
                st.subheader("Interview feedback")

                if "score" in result:
                    st.metric(
                        "Score",
                        str(result["score"])
                    )

                if "word_count" in result:
                    st.metric(
                        "Word count",
                        str(result["word_count"])
                    )

                st.write(
                    result.get(
                        "feedback",
                        "No feedback returned."
                    )
                )

                suggestions = result.get("suggestions", [])

                if suggestions:
                    st.write("### Suggestions")

                    for suggestion in suggestions:
                        st.markdown(f"- {suggestion}")

                if result.get("next_action"):
                    st.caption(
                        f"Next action: {result['next_action']}"
                    )

# =========================================================
# CAREER ADVISOR
# =========================================================
elif selected == "Advisor":

    st.subheader("✨ Career Advisor")
    st.write(
        "Ask questions about skills, job preparation, "
        "projects, and your career direction."
    )

    if require_resume():

        question = st.text_area(
            "Your career question",
            height=120,
            placeholder=(
                "What skills should I learn next "
                "for a machine learning role?"
            )
        )

        if st.button(
            "Get Career Guidance",
            use_container_width=True
        ):

            if not question.strip():
                st.warning("Please enter a question.")

            else:
                with st.spinner("Preparing your guidance..."):
                    result = api_post(
                        "career-advisor",
                        {"question": question.strip()},
                        timeout=60
                    )

                if result is not None:
                    st.divider()
                    st.subheader("Your guidance")

                    st.markdown(
                        result.get(
                            "answer",
                            "No answer returned by the backend."
                        )
                    )

# =========================================================
# FOOTER
# =========================================================
st.divider()

st.markdown(
    """
    <div style="
        text-align:center;
        color:#D6C7AC;
        font-size:12px;
        padding:10px;
    ">
        AI Career Assistant · Local Development
    </div>
    """,
    unsafe_allow_html=True
)
