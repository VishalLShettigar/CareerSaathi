import re
import os
from io import BytesIO
import fitz         # PyMuPDF for PDF
import docx         # python-docx for DOCX files
from PIL import Image
import pytesseract  # OCR for images
from career_mapping import SKILL_CAREER_MAP
from pyresparser import ResumeParser

import spacy
nlp = spacy.load("en_core_web_sm")

# --- Function to extract text from file ---
def extract_text(file_stream, filename):
    ext = filename.lower().split('.')[-1]
    text = ""
    file_stream.seek(0)
    if ext == "pdf":
        with fitz.open(stream=file_stream.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
    elif ext in ("docx", "doc"):
        doc_obj = docx.Document(file_stream)
        text = "\n".join(para.text for para in doc_obj.paragraphs)
    elif ext in ("png", "jpg", "jpeg"):
        img = Image.open(file_stream)
        text = pytesseract.image_to_string(img)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    return text

# --- Function to extract sections from text based on headers ---
MAJOR_HEADERS = re.compile(
    r'(?i)^(education|experience|certifications|internship|training|projects|skills|technical|languages|personal)\b'
)

def extract_section(lines, start_keywords):
    start_re = re.compile(r'(?i)^(?:' + '|'.join(re.escape(k) for k in start_keywords) + r')\b')
    collecting = False
    block = []
    for l in lines:
        if collecting:
            if MAJOR_HEADERS.search(l):
                break
            if len(l) < 180:
                block.append(l)
        elif start_re.search(l):
            collecting = True
    # remove duplicates while keeping order
    seen, clean = set(), []
    for b in block:
        if b not in seen:
            seen.add(b)
            clean.append(b)
    return "\n".join(clean).strip() if clean else "Not Found"

def extract_resume_data(file_stream, filename=None):
    """
    Parse resume and return clean sections:
    name, email, phone, skills, education, certifications, experience, score
    Supports PDF, DOCX, and images.
    """
    # --- Input handling ---
    if filename is None:
        if isinstance(file_stream, str):
            filename = file_stream
            file_stream = open(file_stream, "rb")
        elif hasattr(file_stream, "filename"):
            filename = file_stream.filename
        elif hasattr(file_stream, "name"):
            filename = file_stream.name
        else:
            raise ValueError("Filename not provided")

    filename = os.path.basename(filename)
    file_stream.seek(0)

    # --- Extract text using custom method ---
    text = extract_text(file_stream, filename)
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # --- Parse using pyresparser ---
    try:
        temp_path = f"/tmp/{filename}"
        with open(temp_path, "wb") as f:
            file_stream.seek(0)
            f.write(file_stream.read())
        parsed_data = ResumeParser(temp_path).get_extracted_data()
    except Exception:
        parsed_data = {}

    # --- Extract fields with fallback ---
    name = parsed_data.get("name") or (lines[0].title() if lines else "Not Found")

    email = parsed_data.get("email") or re.search(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', text)
    email = email.group() if isinstance(email, re.Match) else email or "Not Found"

    phone = parsed_data.get("mobile_number") or re.search(
        r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b', text)
    phone = phone.group() if isinstance(phone, re.Match) else phone or "Not Found"

    # --- Skills ---
    skills = parsed_data.get("skills") or []
    if not skills:
        skill_keywords = list(SKILL_CAREER_MAP.keys())
        pattern = r'\b(?:' + '|'.join(re.escape(k) for k in skill_keywords) + r')\b'
        found = re.findall(pattern, text, re.I)
        skills = list({s.lower() for s in found})

    # --- Education ---
    education = parsed_data.get("education") or extract_section(lines, ["education", "education background"])

    # --- Experience ---
    experience = parsed_data.get("experience") or extract_section(lines, ["experience", "internship", "work experience"])

    # --- Certifications ---
    certifications = extract_section(lines, ["certifications", "training", "courses"])
    if certifications == "Not Found":
        certifications = parsed_data.get("certifications") or "Not Found"

    # --- Resume Score ---
    score = 0
    if email != "Not Found": score += 10
    if phone != "Not Found": score += 10
    score += min(len(skills), 6) * 5
    if education != "Not Found": score += 10
    if experience != "Not Found": score += 10
    if re.search(r"(communication|teamwork|leadership|problem solving|adaptability)", text, re.I):
        score += 10
    words = len(text.split())
    if 500 <= words <= 1500: score += 10
    if re.search(r"(education|experience|skills|projects|certification)", text, re.I):
        score += 10
    if words < 100: score -= 10
    score = max(0, min(score, 100))

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "skills": skills,
        "education": education,
        "certifications": certifications,
        "experience": experience,
        "score": score
    }

def recommend_career(skills):
    recommended = set()
    for skill in skills:
        if skill in SKILL_CAREER_MAP:
            recommended.add(SKILL_CAREER_MAP[skill])
    return list(recommended) if recommended else ['General Role Based on Resume']
