import re
import os
from io import BytesIO
import fitz         # PyMuPDF for PDF
import docx         # python-docx for DOCX files
from PIL import Image
import pytesseract  # OCR for images
from career_mapping import SKILL_CAREER_MAP

def extract_text(file_stream, filename):
    """
    Read text from PDF, DOCX, or image file.
    """
    ext = filename.lower().split('.')[-1]
    text = ""
    file_stream.seek(0)
    if ext == "pdf":
        # Use PyMuPDF to extract text from each PDF page
        with fitz.open(stream=file_stream.read(), filetype="pdf") as doc:
            for page in doc:
                text += page.get_text()
    elif ext in ("docx", "doc"):
        # Extract text from Word document
        doc_obj = docx.Document(file_stream)
        text = "\n".join(para.text for para in doc_obj.paragraphs)
    elif ext in ("png", "jpg", "jpeg"):
        # Use OCR to extract text from image
        img = Image.open(file_stream)
        text = pytesseract.image_to_string(img)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    return text

def extract_resume_data(file_stream, filename=None):
    """
    Parse resume file and extract name, email, phone, skills, etc.
    """
    # Handle missing filename argument
    if filename is None:
        if isinstance(file_stream, str):
            filename = file_stream
            file_stream = open(file_stream, "rb")
        elif hasattr(file_stream, 'filename'):
            filename = file_stream.filename
        elif hasattr(file_stream, 'name'):
            filename = file_stream.name
        else:
            raise ValueError("Filename not provided")
    filename = os.path.basename(filename)
    file_stream.seek(0)
    text = extract_text(file_stream, filename)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # --- Name ---
    name = "Not Found"
    if lines:
        first_line = lines[0]
        if re.search(r'\b(cv|resume)\b', first_line, re.IGNORECASE):
            for ln in lines[1:]:
                if ln:
                    name = ln.strip().title()
                    break
        else:
            name = first_line.title().strip()

    # --- Email & Phone ---
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', text)
    email = email_match.group() if email_match else "Not Found"
    phone_match = re.search(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b', text)
    phone = phone_match.group() if phone_match else "Not Found"

    # --- Skills ---
    skill_keywords = list(SKILL_CAREER_MAP.keys())
    if skill_keywords:
        pattern = r'\b(?:' + '|'.join(re.escape(skill) for skill in skill_keywords) + r')\b'
        found_skills = re.findall(pattern, text, flags=re.IGNORECASE)
        skills = list({s.lower() for s in found_skills})
    else:
        skills = []

    # --- Education ---
    degree_keywords = [
        'phd', 'doctorate', 'm.phil', 'msc by research', 'm.tech', 'm.e', 'm.sc', 
        'mcom', 'ma', 'm.arch', 'mpharm', 'llm', 'm.ed', 'master of technology', 
        'master of engineering', 'master of science', 'master of commerce', 'master of arts', 
        'master of architecture', 'master of pharmacy', 'master of law', 'master of education', 
        'mba', 'mca', 'md', 'ms', 'mpt', 'mch', 'mdes', 'mfa', 'm.lib', 'm.voc', 'mstat',
        'b.tech', 'b.e', 'b.sc', 'bcom', 'ba', 'b.arch', 'bpharm', 'llb', 'b.ed', 
        'bachelor of technology', 'bachelor of engineering', 'bachelor of science', 
        'bachelor of commerce', 'bachelor of arts', 'bachelor of architecture', 
        'bachelor of pharmacy', 'bachelor of law', 'bachelor of education',
        'bba', 'bca', 'bhms', 'bams', 'bpt', 'bds', 'bfa', 'bdes', 'b.lib', 'b.voc', 'bstat',
        'diploma', 'pg diploma', 'postgraduate diploma', 'advanced diploma', 'associate degree',
        'graduation', 'undergraduate', 'degree', 'sslc', 'puc'
    ]
    education_lines = []
    for line in text.splitlines():
        for deg in degree_keywords:
            if re.search(rf"\b{re.escape(deg)}\b", line, flags=re.IGNORECASE):
                education_lines.append(line.strip())
                break
    education = '\n'.join(sorted(set(education_lines))) if education_lines else "Not Found"

    # --- Certifications ---
    cert_keywords = ['certification', 'certified', 'course', 'training', 'license', 'workshop']
    cert_lines = []
    for line in text.splitlines():
        for kw in cert_keywords:
            if re.search(rf"\b{re.escape(kw)}\b", line, flags=re.IGNORECASE):
                if not any(re.search(rf"\b{re.escape(deg)}\b", line, flags=re.IGNORECASE) 
                           for deg in degree_keywords):
                    cert_lines.append(line.strip())
                    break
    certifications = '\n'.join(cert_lines) if cert_lines else "Not Found"

    # --- Experience ---
    exp_keywords = ['experience', 'intern', 'worked at', 'company', 'responsibilities', 'roles', 'designation']
    exp_lines = []
    for line in text.splitlines():
        for kw in exp_keywords:
            if re.search(rf"\b{re.escape(kw)}\b", line, flags=re.IGNORECASE):
                exp_lines.append(line.strip())
                break
    experience = '\n'.join(exp_lines) if exp_lines else "Not Found"

    # --- Scoring (optional) ---
    score = 0
    if email != 'Not Found': score += 10
    if phone != 'Not Found': score += 10
    score += min(len(skills), 6) * 5
    if education != 'Not Found': score += 10
    if experience != 'Not Found': score += 10
    if re.search(r"(communication|teamwork|leadership|creative|problem solving|adaptability)", 
                 text, flags=re.IGNORECASE):
        score += 10
    word_count = len(text.split())
    if 500 <= word_count <= 1500: score += 10
    if re.search(r"(education|experience|skills|projects|certification)", text, re.IGNORECASE):
        score += 10
    if word_count < 100: score -= 10
    score = max(0, min(score, 100))

    return {
        'name': name,
        'email': email,
        'phone': phone,
        'skills': skills,
        'education': education,
        'certifications': certifications,
        'experience': experience,
        'score': score
    }


def recommend_career(skills):
    recommended = set()
    for skill in skills:
        if skill in SKILL_CAREER_MAP:
            recommended.add(SKILL_CAREER_MAP[skill])
    return list(recommended) if recommended else ['General Role Based on Resume']
