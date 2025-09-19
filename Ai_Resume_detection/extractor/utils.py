import os
import re
import json
import spacy
import docx
from pathlib import Path
from docx import Document
from PyPDF2 import PdfReader
from datetime import datetime
from django.conf import settings

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")


# ------------------- Extract Text -------------------
def extract_text_from_docx(file):
    try:
        doc = Document(file)
        return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
    except Exception:
        return ""


def extract_text_from_pdf(file):
    text = ""
    try:
        pdf = PdfReader(file)
        for page in pdf.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
    except Exception:
        return ""
    return text


# ------------------- Date Parsing Helper -------------------
def parse_date(date_str):
    """Convert resume date string to datetime object"""
    date_str = date_str.strip().lower().replace("present", datetime.now().strftime("%b %Y"))

    # Common formats: Jan 2020, March 2019, 2021
    formats = ["%b %Y", "%B %Y", "%Y"]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def calculate_experience(text):
    """
    Find date ranges in resume and calculate total years of experience.
    Example: Jan 2020 - Mar 2022
    """
    date_pattern = r"([A-Za-z]{3,9}\s\d{4}|\d{4})\s*[-–]\s*(Present|[A-Za-z]{3,9}\s\d{4}|\d{4})"
    matches = re.findall(date_pattern, text, flags=re.IGNORECASE)

    total_months = 0
    for start, end in matches:
        start_date = parse_date(start)
        end_date = parse_date(end)
        if start_date and end_date:
            months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
            if months > 0:
                total_months += months

    if total_months == 0:
        return "Fresher (No prior work experience found)"

    years, months = divmod(total_months, 12)
    return f"{years} years {months} months" if years else f"{months} months"


# ------------------- Summary Extraction -------------------
def extract_summary(text):
    summary_keywords = ["summary", "objective", "profile"]
    for keyword in summary_keywords:
        pattern = re.compile(
            rf"{keyword}[:\-]?\s*(.+?)(?=\n[A-Z])",
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(text)
        if match:
            return match.group(1).strip()

    doc = nlp(text)
    sentences = list(doc.sents)
    return " ".join([sent.text for sent in sentences[:3]]) if sentences else "No summary found"


# ------------------- Experience Extraction -------------------
def extract_experience(text):
    exp_keywords = ["experience", "work experience", "employment history", "professional experience"]

    for keyword in exp_keywords:
        pattern = re.compile(
            rf"{keyword}[:\-]?\s*(.+?)(?=\n[A-Z])",
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(text)
        if match:
            return match.group(1).strip()

    doc = nlp(text)
    companies = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
    if companies:
        return f"Companies: {', '.join(companies[:3])}"

    return "Fresher"

#<------------------Education information------------------>
def extract_education(text):
    education_keywords = ["education", "academic background", "qualifications", "educational qualifications"]
    for keyword in education_keywords:
        pattern = re.compile(
            rf"{keyword}[:\-]?\s*(.+?)(?=\n[A-Z])",
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return None

#<-------------------Projects------------------->
def extract_projects(text):
    project_keywords = ["projects", "project experience", "notable projects"]
    for keyword in project_keywords:
        pattern = re.compile(
            rf"{keyword}[:\-]?\s*(.+?)(?=\n[A-Z])",
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return None

    


# ------------------- Skills Extraction -------------------
def extract_skills(text):
    skills_file = settings.BASE_DIR / "skills" / "skills.json"
    try:
        with open(skills_file, "r") as f:
            skills = json.load(f).get("skills", [])
    except FileNotFoundError:
        return []

    text = text.lower()
    extracted = []
    for skill in skills:
        if re.search(rf"\b{re.escape(skill.lower())}\b", text):
            extracted.append(skill)

    return list(set(extracted))

#<----------achivement---------->

def extract_achievements(texts):
    achievement_keywords = ["achievements", "certifications", "awards", "recognitions", "honors"]
    results = []

    for keyword in achievement_keywords:
        # Match the section until the next heading (newline + capitalized word) or end of text
        pattern = re.compile(
            rf"{keyword}[:\-]?\s*(.+?)(?=\n[A-Z]|\Z)",
            re.IGNORECASE | re.DOTALL
        )
        match = pattern.search(texts)
        if match:
            results.append(match.group(1).strip())

    return results if results else None

#<----------github links---------->

def extract_github_links(text):
    # Find all GitHub links in the text
    github_pattern = r"https?://github\.com/[^\s]+"
    links = re.findall(github_pattern, text)
    return ", ".join(links) if links else ""
        

# ---------- Main Extractor ----------
def extract_resume_data(file, file_type="pdf"):
    # 1. Extract text
    if file_type == "docx":
        text = extract_text_from_docx(file)
    elif file_type == "pdf":
        text = extract_text_from_pdf(file)
    else:
        return {"error": "Unsupported file format"}

    # 2. Extract fields
    data = {
        "summary": extract_summary(text),
        "experience": extract_experience(text),
        "skills": extract_skills(text),
        "total_experience": calculate_experience(text),
        "achievements": extract_achievements(text),
        "education": extract_education(text),
        "projects": extract_projects(text),
        "github_links": extract_github_links(text),
        
    }
    return data
#<-------------------ats checker------------------->
def ats_checker(resume_text, job_description):
    resume_text = resume_text.lower()
    job_description = job_description.lower()

     # Extract keywords (simple split by non-words, can be improved using NLP)
    jd_keywords = set(re.findall(r'\b[a-zA-Z]+\b', job_description))
    resume_keywords = set(re.findall(r'\b[a-zA-Z]+\b', resume_text))

    if not jd_keywords:
        return {"error": "No keywords found in job description."}

    matched_keywords = jd_keywords.intersection(resume_keywords)
    match_count = len(matched_keywords)
    total_jd_keywords = len(jd_keywords)
    match_percentage = (match_count / total_jd_keywords) * 100 if total_jd_keywords > 0 else 0

    return {
        "total_jd_keywords": total_jd_keywords,
        "matched_keywords": list(matched_keywords),
        "match_count": match_count,
        "match_percentage": round(match_percentage, 2),
    }
# <------------------- End of File ------------------->