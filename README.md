AI Career Assistant

An AI-powered application that helps users analyze resumes, discover matching jobs, identify skill gaps, build career roadmaps, practise interviews, and receive career guidance.

Features:
- PDF Resume Analysis
- Job Recommendations
- Skill Gap Analysis
- Personalized Career Roadmap
- Mock Interview Feedback
- Career Advisor
- Dark Theme with Background Image
- Transparent Glass-Style UI

Technologies:
Python, Streamlit, FastAPI, Pandas, PyMuPDF, Requests

Project Files:
app.py
main.py
requirements.txt
background.jpg
data/LinkedIn_RDB_three.csv

Setup:
Install dependencies and run the backend and frontend locally.

Application Workflow:
Upload Resume → Analyze Skills → Find Jobs → Identify Skill Gaps → Follow Career Roadmap → Practise Interviews.

Project Status:
Local Development Version.

AI Career Assistant — Analyze your skills. Discover opportunities. Build your future.
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
streamlit run app.py