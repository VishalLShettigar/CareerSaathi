import re
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from docx import Document
import language_tool_python

# Example skill-to-career mapping
SKILL_CAREER_MAP = {
    'python': ['Data Scientist', 'Software Engineer'],
    'java': ['Java Developer', 'Software Engineer'],
    'sql': ['Database Administrator', 'Data Analyst'],
    'excel': ['Data Analyst', 'Business Analyst'],
    'aws': ['Cloud Engineer', 'DevOps Engineer'],
    # ... add more mappings as needed
}

def extract_text(filepath):
    """Extract raw text from PDF, DOCX, or image file."""
    text = ""
    if filepath.lower().endswith('.pdf'):
        doc = fitz.open(filepath)
        for page in doc:
            page_text = page.get_text("text")
            if page_text.strip():
                text += page_text + "\n"
            else:
                # If no text (scanned PDF), do OCR per page
                pix = page.get_pixmap()
                img = pix.get_pil_image()
                text += pytesseract.image_to_string(img) + "\n"
    elif filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp')):
        # OCR on image file
        try:
            text = pytesseract.image_to_string(filepath)
        except Exception:
            # If path string fails, open via PIL
            from PIL import Image
            img = Image.open(filepath)
            text = pytesseract.image_to_string(img)
    elif filepath.lower().endswith('.docx'):
        doc = Document(filepath)
        text = '\n'.join(para.text for para in doc.paragraphs)
    else:
        raise ValueError("Unsupported file type.")
    return text

def extract_email(text):
    pattern = r"\S+@\S+\.\S+"
    matches = re.findall(pattern, text)
    return matches[0] if matches else None

def extract_phone(text):
    # Regex: optional +, then 8-15 digits (international numbers):contentReference[oaicite:22]{index=22}.
    pattern = r"\+?[1-9][0-9]{7,14}"
    matches = re.findall(pattern, text)
    return matches[0] if matches else None

def extract_name(text):
    # Heuristic: first non-empty line is the name (or line starting with "Name:")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if line.lower().startswith("name"):
            parts = line.split(':', 1)
            if len(parts) > 1:
                return parts[1].strip()
        # If line looks like a full name (two capitalized words), take it
        if re.match(r"^[A-Z][a-z]+ [A-Z][a-z]+", line):
            return line.strip()
    return lines[0] if lines else None

def extract_skills(text):
    skills = []
    # Find "Skills" section (case-insensitive)
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if 'skills' in line.lower():
            # Collect following lines until a blank or next section
            for skill_line in lines[i+1:]:
                if not skill_line.strip() or skill_line.endswith(':'):
                    break
                skills.extend([s.strip() for s in re.split(r'[,\u2022]', skill_line) if s.strip()])
            break
    return skills

def extract_education(text):
    degrees_found = []
    lines = text.splitlines()
    degree_keywords = ['ph.d', 'phd', 'doctor', 'master', 'mba', 'msc', 'ms', 'bachelor', 'bs', 'ba', 'associates', 'associate']
    # Identify Education section
    for i, line in enumerate(lines):
        if 'education' in line.lower():
            for edu_line in lines[i+1:]:
                if not edu_line.strip() or edu_line.endswith(':'):
                    break
                edu_line_lower = edu_line.lower()
                for keyword in degree_keywords:
                    if re.search(r'\b' + keyword + r'\b', edu_line_lower):
                        degrees_found.append(edu_line.strip())
                        break
            break
    # Order degrees: highest level first:contentReference[oaicite:23]{index=23}
    order = ['phd', 'doctor', 'master', 'mba', 'msc', 'ms', 'bachelor', 'ba', 'bs', 'associate']
    def degree_rank(deg):
        for idx, key in enumerate(order):
            if key in deg.lower():
                return idx
        return len(order)
    degrees_sorted = sorted(degrees_found, key=degree_rank)
    return degrees_sorted

def extract_certifications(text):
    certs = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if 'certificat' in line.lower():
            for cert_line in lines[i+1:]:
                if not cert_line.strip() or cert_line.endswith(':'):
                    break
                certs.append(cert_line.strip())
            break
    return certs

def extract_experience(text):
    titles = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if 'experience' in line.lower():
            for exp_line in lines[i+1:]:
                if not exp_line.strip() or exp_line.endswith(':'):
                    break
                # Take up to first 8 words of the line
                words = exp_line.split()
                title = ' '.join(words[:8])
                titles.append(title.strip())
            break
    return titles

def grammar_score(text):
    tool = language_tool_python.LanguageTool('en-US')
    matches = tool.check(text)
    errors = len(matches)
    # Simple score: percentage of error-free words (e.g., 100*(1 - errors/word_count))
    word_count = len(text.split())
    score = 100.0 * max(0, (word_count - errors)) / max(1, word_count)
    return errors, score

def recommend_careers(skills):
    recs = set()
    for skill in skills:
        key = skill.lower()
        if key in SKILL_CAREER_MAP:
            recs.update(SKILL_CAREER_MAP[key])
    return list(recs)

def main(filepath):
    text = extract_text(filepath)
    name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone(text)
    skills = extract_skills(text)
    education = extract_education(text)
    certifications = extract_certifications(text)
    experience = extract_experience(text)
    errors, score = grammar_score(text)
    recommendations = recommend_careers(skills)

    # Print results
    print(f"Name: {name}")
    print(f"Phone: {phone}")
    print(f"Email: {email}")
    print(f"Skills: {', '.join(skills)}")
    print("Education:", "; ".join(education))
    print("Certifications:", "; ".join(certifications))
    print("Experience:", "; ".join(experience))
    print(f"Grammar Errors: {errors} (Score: {score:.1f}%)")
    if recommendations:
        print("Recommended Careers:", ", ".join(recommendations))

# Example usage (uncomment and set path to run):
main("Vishal__Shettigar__CV.pdf")
