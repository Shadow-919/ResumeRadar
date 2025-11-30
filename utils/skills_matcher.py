"""
Improved Skills Matcher Module
Handles:
- Versioned skills (html/html5, css/css3)
- Framework variants (react/react.js/reactjs)
- Cloud synonyms (aws/amazon web services)
- API synonyms (rest/rest api/restful api)
- Multi-variant skill normalization
- Abbreviation expansion
"""

import json
import os
import re


# ===========================
# 1. LOAD SKILLS DATABASE
# ===========================

def load_skills_database():
    skills_file_path = os.path.join('analysis_data', 'skills.json')
    with open(skills_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['skills']


def load_soft_skills():
    soft_skills_path = os.path.join('analysis_data', 'soft_skills.json')
    with open(soft_skills_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return set(data['soft_skills'])


# ===========================
# 2. NORMALIZATION MAP
# ===========================

CANONICAL_MAP = {

    # HTML / CSS versions
    "html": "html",
    "html5": "html",
    "css": "css",
    "css3": "css",

    # JavaScript frameworks
    "react": "react",
    "react.js": "react",
    "reactjs": "react",

    "angular": "angular",
    "angular.js": "angularjs",  # if needed in future

    "vue": "vue",
    "vue.js": "vue",
    "vuejs": "vue",

    "next": "next.js",
    "nextjs": "next.js",
    "next.js": "next.js",

    "nuxt": "nuxt.js",
    "nuxtjs": "nuxt.js",
    "nuxt.js": "nuxt.js",

    "nest": "nest.js",
    "nestjs": "nest.js",
    "nest.js": "nest.js",

    # Node variants
    "node": "node.js",
    "nodejs": "node.js",
    "node.js": "node.js",

    # Express variants
    "express": "express.js",
    "express.js": "express.js",
    "expressjs": "express.js",

    # Cloud platforms
    "aws": "amazon web services",
    "amazon web services": "amazon web services",

    "azure": "microsoft azure",
    "microsoft azure": "microsoft azure",

    "gcp": "google cloud platform",
    "google cloud platform": "google cloud platform",

    # API variants
    "rest": "rest api",
    "restful api": "rest api",
    "rest api": "rest api",

    # OOP
    "oop": "object-oriented programming",

    # SQL variants
    "sql server": "microsoft sql server",

    # ML / DL / NLP short forms
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "ds": "data science",

    # TensorFlow / PyTorch variants
    "tf": "tensorflow",
    "torch": "pytorch",

    # .NET naming
    ".net": ".net",
    "dotnet": ".net",
    "asp.net": "asp.net",
}


def canonicalize(skill: str) -> str:
    """
    Convert skill to canonical normalized form.
    If no mapping exists, return skill as-is (lowercase).
    """
    s = skill.lower().strip()
    return CANONICAL_MAP.get(s, s)


# ===========================
# 3. PATTERN BUILDER
# ===========================

def _skill_to_pattern(skill: str) -> re.Pattern:
    """Flexible regex to detect multi-word skills & variants."""
    s = skill.lower().strip()

    words = s.split()
    if len(words) == 1:
        escaped = re.escape(s)
        pattern = r'\b' + escaped + r'\b'
    else:
        escaped = re.escape(s)
        escaped = escaped.replace(r'\ ', r'[\s\-_/|]+')
        pattern = r'(?<!\w)' + escaped + r'(?!\w)'

    return re.compile(pattern, re.IGNORECASE)


# ===========================
# 4. Abbreviation Detection
# ===========================

ABBREVIATION_MAP = {
    "ml": "machine learning",
    "dl": "deep learning",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "ai": "artificial intelligence",
    "oop": "object-oriented programming",
    "qa": "quality assurance",
    "pm": "product management",
    "ds": "data science",
    "tf": "tensorflow",
    "sklearn": "scikit-learn",
}


def _extract_abbreviation_skills(text_lower, skills_database):
    found = []
    tokens = set(re.findall(r'\b[a-zA-Z0-9\.\+]{2,15}\b', text_lower))

    for abbr, canonical in ABBREVIATION_MAP.items():
        if abbr in (t.lower() for t in tokens):
            if canonical in skills_database:
                found.append(canonical)
    return found


# ===========================
# 5. Extract Skills with Normalization
# ===========================

def extract_skills_from_text(text, skills_database):
    found_raw = []
    text_lower = text.lower()

    for skill in skills_database:
        pattern = _skill_to_pattern(skill)
        if pattern.search(text_lower):
            found_raw.append(skill)

    # Include abbreviations
    abbreviations = _extract_abbreviation_skills(text_lower, skills_database)
    for sk in abbreviations:
        found_raw.append(sk)

    # Normalize all skills using canonical map
    normalized = []
    for sk in found_raw:
        c = canonicalize(sk)
        if c not in normalized:
            normalized.append(c)

    return normalized


# ===========================
# 6. Main Analyzer
# ===========================

def analyze_skills_match(resume_text, job_description_text):
    skills_database = load_skills_database()

    # Normalize skill database for comparison
    normalized_skill_db = list({canonicalize(s) for s in skills_database})

    jd_raw = extract_skills_from_text(job_description_text, skills_database)
    resume_raw = extract_skills_from_text(resume_text, skills_database)

    # Normalize extracted skills
    jd = [canonicalize(s) for s in jd_raw]
    resume = [canonicalize(s) for s in resume_raw]

    # Unique sets
    jd = list(dict.fromkeys(jd))
    resume = list(dict.fromkeys(resume))

    matched = [s for s in jd if s in resume]
    missing = [s for s in jd if s not in resume]

    soft_list = load_soft_skills()

    technical_matched = [s for s in matched if s not in soft_list]
    soft_matched = [s for s in matched if s in soft_list]

    technical_missing = [s for s in missing if s not in soft_list]
    soft_missing = [s for s in missing if s in soft_list]

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "total_jd_skills": len(jd),
        "total_candidate_skills": len(resume),
        "technical_matched": technical_matched,
        "technical_missing": technical_missing,
        "soft_matched": soft_matched,
        "soft_missing": soft_missing
    }
