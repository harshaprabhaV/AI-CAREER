import os
import re
from pathlib import Path
from typing import Any

import fitz
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="AI Career Assistant API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
JOB_CSV_CANDIDATES = [
    DATA_DIR / "LinkedIn_RDB_three.csv",
    BASE_DIR / "LinkedIn_RDB_three.csv",
    BASE_DIR.parent / "LinkedIn_RDB_three.csv",
]
resume_text_store = ""
resume_filename_store = ""
resume_skills_store: list[str] = []

SKILLS = [
    "Python", "Java", "SQL", "Machine Learning", "Deep Learning", "NLP",
    "Computer Vision", "PyTorch", "TensorFlow", "scikit-learn", "Pandas",
    "NumPy", "Matplotlib", "Seaborn", "Transformers", "BERT", "Mamba",
    "LLM", "Generative AI", "RAG", "LangChain", "LangGraph", "FAISS",
    "FastAPI", "Streamlit", "React.js", "JavaScript", "HTML", "CSS",
    "Node.js", "Express.js", "MongoDB", "MySQL", "Docker", "AWS", "Azure",
    "Statistics", "Data Science", "Data Engineering"
]

def extract_skills(text: str) -> list[str]:
    lower = text.lower()
    found = []
    for skill in SKILLS:
        # Allow simple variations for common skill spellings.
        pattern = re.escape(skill.lower())
        if re.search(pattern, lower):
            found.append(skill)
    return sorted(set(found), key=str.lower)

def load_jobs() -> pd.DataFrame:
    for path in JOB_CSV_CANDIDATES:
        if path.exists():
            try:
                df = pd.read_csv(path, encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(path, encoding="latin-1")
            df.columns = [str(c).strip() for c in df.columns]
            return df
    return pd.DataFrame()

def col_value(row: pd.Series, names: list[str], default: str = "") -> str:
    for name in names:
        if name in row.index and pd.notna(row[name]):
            value = str(row[name]).strip()
            if value and value.lower() != "nan":
                return value
    return default

def score_job(row: pd.Series, resume_text: str, resume_skills: list[str]) -> dict[str, Any]:
    title = col_value(row, ["title", "job_title"], "Unknown role")
    description = col_value(row, ["description", "job_description"], "")
    domain = col_value(row, ["job_domain", "domain"], "")
    location = col_value(row, ["job_location", "location"], "Not specified")
    work_type = col_value(row, ["work_type", "employment_type"], "Not specified")
    level = col_value(row, ["level", "seniority"], "Not specified")
    job_text = f"{title} {description} {domain}".lower()

    matched = [skill for skill in resume_skills if skill.lower() in job_text]
    skill_score = (len(matched) / max(1, len(set(resume_skills)))) * 100
    resume_words = set(re.findall(r"[a-zA-Z+#.]{2,}", resume_text.lower()))
    job_words = set(re.findall(r"[a-zA-Z+#.]{2,}", job_text))
    overlap = len(resume_words & job_words) / max(1, len(job_words))
    semantic_proxy = min(100.0, overlap * 250)
    combined = 0.65 * semantic_proxy + 0.35 * skill_score

    return {
        "title": title,
        "company": col_value(row, ["company", "company_name"], "Company information unavailable"),
        "job_location": location,
        "work_type": work_type,
        "level": level,
        "job_domain": domain,
        "semantic_score": round(semantic_proxy, 2),
        "skill_match_score": round(skill_score, 2),
        "final_match_score": round(combined, 2),
        "match_score": round(combined, 2),
        "matched_skills": matched,
        "description": description[:1200],
    }

class AnswerRequest(BaseModel):
    answer: str

class QuestionRequest(BaseModel):
    question: str

@app.get("/")
def root():
    return {"message": "AI Career Assistant API is running", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok", "resume_loaded": bool(resume_text_store)}

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    global resume_text_store, resume_filename_store, resume_skills_store
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Please upload a PDF resume.")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    try:
        with fitz.open(stream=raw, filetype="pdf") as doc:
            text = "\n".join(page.get_text() for page in doc).strip()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read PDF: {exc}")
    if not text:
        raise HTTPException(status_code=422, detail="No selectable text found in this PDF. Try a text-based PDF.")
    resume_text_store = text
    resume_filename_store = file.filename
    resume_skills_store = extract_skills(text)
    return {
        "filename": resume_filename_store,
        "resume_text": resume_text_store,
        "skills": resume_skills_store,
        "characters": len(resume_text_store),
        "message": "Resume uploaded and text extracted."
    }

@app.get("/jobs")
def jobs():
    if not resume_text_store:
        raise HTTPException(status_code=400, detail="Upload a resume first.")
    df = load_jobs()
    if df.empty:
        return {
            "jobs": [],
            "message": "Job CSV not found. Place LinkedIn_RDB_three.csv in backend/data/."
        }
    results = [score_job(row, resume_text_store, resume_skills_store) for _, row in df.iterrows()]
    results.sort(key=lambda x: x["final_match_score"], reverse=True)
    return {"jobs": results[:50], "total_available": len(results)}

@app.get("/skills")
def skills():
    if not resume_text_store:
        raise HTTPException(status_code=400, detail="Upload a resume first.")
    return {
        "detected_skills": resume_skills_store,
        "total_skills": len(resume_skills_store),
        "suggested_core_skills": [
            skill for skill in ["SQL", "scikit-learn", "PyTorch", "FastAPI", "Docker"]
            if skill not in resume_skills_store
        ],
        "note": "Skills are detected from text matches, not a full LLM assessment."
    }

@app.get("/roadmap")
def roadmap():
    if not resume_text_store:
        raise HTTPException(status_code=400, detail="Upload a resume first.")
    missing = [s for s in ["SQL", "scikit-learn", "PyTorch", "FastAPI", "Docker"] if s not in resume_skills_store]
    return {
        "days_1_30": {
            "focus": "Strengthen foundations and fill the highest-priority gaps.",
            "skills": missing[:3] or ["Model evaluation", "Git", "SQL practice"],
            "projects": ["Build an end-to-end ML classification project"],
            "outcome": "A reproducible ML project with evaluation metrics."
        },
        "days_31_60": {
            "focus": "Build and serve a model through an API.",
            "skills": ["FastAPI", "Testing", "Model evaluation"],
            "projects": ["Deploy an ML model locally with FastAPI and Streamlit"],
            "outcome": "A working local ML application."
        },
        "days_61_90": {
            "focus": "Prepare a portfolio-ready project.",
            "skills": ["Docker", "Git", "Documentation"],
            "projects": ["Package, test, document, and publish one AI/ML project"],
            "outcome": "A portfolio project ready to demonstrate in interviews."
        }
    }

@app.post("/interview/evaluate")
def evaluate_interview(payload: AnswerRequest):
    answer = payload.answer.strip()
    if not answer:
        raise HTTPException(status_code=400, detail="Answer cannot be empty.")
    word_count = len(answer.split())
    return {
        "word_count": word_count,
        "feedback": "This local starter endpoint checks answer completeness only; connect your LLM pipeline for AI-generated evaluation.",
        "suggestions": [
            "Structure your answer using Situation, Task, Action, Result when relevant.",
            "Mention specific technical decisions and measurable outcomes.",
            "Explain your own contribution clearly."
        ],
        "status": "basic_local_feedback"
    }

@app.post("/career-advisor")
def career_advisor(payload: QuestionRequest):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    if not resume_text_store:
        raise HTTPException(status_code=400, detail="Upload a resume first.")
    return {
        "answer": (
            f"Based on the skills detected in your resume ({', '.join(resume_skills_store) or 'no known skills detected'}), "
            "choose one target role, compare 5–10 real job descriptions, and build projects that demonstrate the missing requirements. "
            "This is starter guidance; connect your Qwen/RAG pipeline for personalized LLM answers."
        ),
        "question": question,
        "status": "basic_local_guidance"
    }
