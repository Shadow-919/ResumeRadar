"""
Experience Analyzer Module

This module provides functions to extract and analyze professional experience
from resumes and job descriptions using dateparser for robust date parsing.
"""

import re
import json
import os
import unicodedata
from datetime import datetime
from dateutil.relativedelta import relativedelta
import dateparser

# Configuration constant for month counting
INCLUSIVE_MONTH_COUNT = True


def extract_jd_required_experience(jd_text):
    """
    Fully extended, semantics-aware JD experience extractor.
    
    Handles:
    - Zero experience phrases (fresh graduate, entry level, etc.)
    - Universal range patterns (0-1, 0 to 2, 1–3, etc.)
    - Single number patterns (3+, minimum 2, at least 5, etc.)
    - Word-based numbers (two years, three years, etc.)
    
    Args:
        jd_text (str): Job description text
        
    Returns:
        tuple: (required_years, required_months)
    """
    jd_lower = jd_text.lower()
    
    # ========================================================================
    # PRIORITY 1: ZERO-EXPERIENCE PHRASES (return 0 immediately)
    # ========================================================================
    zero_experience_phrases = [
        r'\b0\s+years?\b',
        r'\bno\s+experience\s+required\b',
        r'\bfresh\s+graduate\b',
        r'\bfreshers?\s+welcome\b',
        r'\bentry\s+level\b',
        r'\bjunior\s+role\b',
        r'\bbeginner\s+role\b',
        r'\bsome\s+exposure\b',
        r'\bbasic\s+familiarity\b',
        r'\bno\s+prior\s+experience\s+needed\b',
        r'\bno\s+industry\s+experience\s+required\b',
        r'\bfresher\b',
        r'\bno\s+experience\b',
        r'\bentry-level\b',
    ]
    
    for phrase_pattern in zero_experience_phrases:
        if re.search(phrase_pattern, jd_lower):
            return (0, 0)
    
    # ========================================================================
    # PRIORITY 2: UNIVERSAL RANGE HANDLING (return minimum value)
    # ========================================================================
    # Matches: "0 to 1 years", "0-1 year", "0–1 yrs", "1-3", "2 to 5", etc.
    # Returns the MINIMUM because lower bound is the true requirement
    universal_range_pattern = r'(\d+)\s*(?:-|–|—|to|upto|up\s+to)\s*(\d+)\s*(?:yrs?|years?)?'
    
    range_matches = re.findall(universal_range_pattern, jd_lower)
    if range_matches:
        # Extract minimum from all ranges found
        for match in range_matches:
            num1, num2 = int(match[0]), int(match[1])
            min_from_range = min(num1, num2)
            # Return immediately with the minimum from range
            return (min_from_range, 0)
    
    # ========================================================================
    # PRIORITY 3: NUMERIC SINGLE-VALUE PATTERNS
    # ========================================================================
    # Order matters - more specific patterns first
    numeric_patterns = [
        # Specific phrasings
        r'candidate\s+(?:should|must)\s+have\s+(\d+)\s+(?:yrs?|years?)',  # "candidate should have 4 years"
        r'must\s+have\s+(\d+)\s+(?:yrs?|years?)',  # "must have 5 years"
        r'should\s+have\s+(\d+)\s+(?:yrs?|years?)',  # "should have 3 years"
        r'looking\s+for\s+(?:someone\s+with\s+)?(\d+)\s+(?:yrs?|years?)',  # "looking for 6 years"
        r'minimum\s+of\s+(\d+)\s+years?',  # "minimum of 3 years"
        r'at\s+least\s+(\d+)\s+years?',  # "at least 3 years"
        r'minimum\s+(\d+)\s+years?',  # "minimum 2 years"
        r'min\s+(\d+)\s+years?',  # "min 2 years"
        r'more\s+than\s+(\d+)\s+years?',  # "more than 4 years"
        r'over\s+(\d+)\s+years?',  # "over 1 year"
        r'(\d+)\s*\+\s*years?',  # "3+ years"
        r'(\d+)\s*\+\s*yrs?',  # "3+ yrs"
        r'(\d+)\s+years?\s+of\s+experience',  # "3 years of experience"
        r'experience\s+of\s+(\d+)\s+years?',  # "experience of 3 years"
        r'(\d+)\s+years?\s+(?:\w+\s+){0,3}?experience',  # "3 years professional experience"
        r'experience\s*:\s*(\d+)\s+years?',  # "experience: 7 years"
        r'required\s*:\s*(\d+)\s+years?',  # "required: 5 years"
        r'(\d+)\s+yrs?\b',  # "3 yrs" or "5 yr" (broad catch)
    ]
    
    min_years = 0
    
    for pattern in numeric_patterns:
        matches = re.findall(pattern, jd_lower)
        if matches:
            for match in matches:
                if isinstance(match, str) and match.isdigit():
                    min_years = max(min_years, int(match))
    
    if min_years > 0:
        return (min_years, 0)
    
    # ========================================================================
    # PRIORITY 4: WORD-BASED NUMBERS
    # ========================================================================
    word_to_num = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
    }
    
    # Word-based patterns
    word_patterns = [
        r'at\s+least\s+({words})\s+years?',
        r'minimum\s+({words})\s+years?',
        r'({words})\s+years?\s+of\s+experience',
        r'({words})\s+years?\s+experience',
    ]
    
    words_regex = '|'.join(word_to_num.keys())
    
    for pattern_template in word_patterns:
        pattern = pattern_template.format(words=words_regex)
        match = re.search(pattern, jd_lower)
        if match:
            word = match.group(1)
            if word in word_to_num:
                return (word_to_num[word], 0)
    
    # ========================================================================
    # PRIORITY 5: FALLBACK - No experience requirement found
    # ========================================================================
    return (0, 0)


def _keyword_to_pattern(keyword):
    """
    Convert a section keyword into a strict whole-line regex pattern.
    
    Args:
        keyword (str): Section keyword
        
    Returns:
        re.Pattern: Compiled regex pattern
    """
    kw = keyword.lower().strip()
    escaped = re.escape(kw)
    escaped = escaped.replace(r'\ ', r'[\s\-|/:]+')
    pattern = r'(^|\n)\s*' + escaped + r'\s*[:\-–—&]?\s*(\n|$)'
    return re.compile(pattern, re.IGNORECASE)


def extract_experience_section(resume_text):
    """
    Extract the Experience section from resume text.
    
    Args:
        resume_text (str): Full resume text
        
    Returns:
        str: Experience section text only
    """
    sections_path = os.path.join(os.path.dirname(__file__), '..', 'analysis_data', 'sections.json')
    try:
        with open(sections_path, 'r', encoding='utf-8') as f:
            sections_data = json.load(f)
    except FileNotFoundError:
        sections_path = os.path.join('analysis_data', 'sections.json')
        with open(sections_path, 'r', encoding='utf-8') as f:
            sections_data = json.load(f)
    
    experience_keywords = sections_data['sections']['Experience']['keywords']
    experience_keywords = sorted(experience_keywords, key=len, reverse=True)
    
    experience_start = None
    experience_match_end = None
    
    for keyword in experience_keywords:
        pattern = _keyword_to_pattern(keyword)
        match = pattern.search(resume_text)
        if match:
            experience_start = match.start()
            if resume_text[experience_start] == '\n':
                experience_start += 1
            experience_match_end = match.end()
            break
    
    if experience_start is None:
        return ""
    
    newline_pos = resume_text.find('\n', experience_match_end)
    search_start_pos = newline_pos + 1 if newline_pos != -1 else experience_match_end
    
    all_section_keywords = []
    for section_name, section_info in sections_data['sections'].items():
        if section_name != 'Experience':
            all_section_keywords.extend(section_info['keywords'])
    
    all_section_keywords = sorted(all_section_keywords, key=len, reverse=True)
    
    next_section_start = None
    remaining_text = resume_text[search_start_pos:]
    
    for keyword in all_section_keywords:
        pattern = _keyword_to_pattern(keyword)
        match = pattern.search(remaining_text)
        if match:
            match_pos = match.start()
            if remaining_text[match_pos] == '\n':
                match_pos += 1
            if next_section_start is None or match_pos < next_section_start:
                next_section_start = match_pos
    
    if next_section_start is not None:
        end_pos = search_start_pos + next_section_start
        experience_text = resume_text[experience_start:end_pos]
    else:
        experience_text = resume_text[experience_start:]
    
    return experience_text


def parse_date_string(date_str):
    """
    Parse a date string into a datetime object using dateparser with robust pre-processing.
    
    Args:
        date_str (str): Date string in various formats
        
    Returns:
        datetime or None: Parsed date or None if parsing fails
    """
    if not date_str:
        return None
    
    date_str = date_str.strip()
    date_str_lower = date_str.lower()
    
    # Handle "Present", "Current", "Now" and variations
    present_keywords = [
        'present', 'current', 'now', 'ongoing',
        'till date', 'tilldate', 'till now', 'tillnow',
        'to date', 'todate', 'currently working',
        'current role', 'current position', 'continuing',
        'up to date', 'uptodate'
    ]
    
    normalized = re.sub(r'\s+', '', date_str_lower)
    for keyword in present_keywords:
        if date_str_lower == keyword or normalized == keyword.replace(' ', ''):
            return datetime.now()
    
    # ROBUST CANONICALIZATION PIPELINE
    
    # Step a) Normalize unicode punctuation
    date_str = date_str.replace('\u2019', "'")
    date_str = re.sub(r'\s+', ' ', date_str.strip())
    
    # Step b) OCR-safe year fixes
    # Fix: 2O21 -> 2021, 2o21 -> 2021 (letter O/o after 2)
    date_str = re.sub(r'\b2[Oo](\d{2})\b', r'20\1', date_str, flags=re.IGNORECASE)
    
    # Fix: 2o2o -> 2020, 2O2O -> 2020 (multiple O/o in year)
    date_str = re.sub(r'\b2[Oo]2[Oo]\b', r'2020', date_str, flags=re.IGNORECASE)
    date_str = re.sub(r'\b2[Oo]2(\d)\b', r'202\1', date_str, flags=re.IGNORECASE)
    
    # Fix: 20O1 -> 2001, 20o1 -> 2001, 19O9 -> 1909 (letter O/o in middle)
    date_str = re.sub(r'\b([12]\d)[Oo](\d)\b', r'\g<1>0\2', date_str, flags=re.IGNORECASE)
    
    # Fix: 202l -> 2021, 202i -> 2021, 202I -> 2021 (letter l/i/I at end)
    date_str = re.sub(r'\b([12]\d{2})[lIi]\b', r'\g<1>1', date_str, flags=re.IGNORECASE)
    
    # Fix: 20l1 -> 2011, 20i1 -> 2011, 20I1 -> 2011 (letter l/i/I in third position)
    date_str = re.sub(r'\b([12]\d)[lIi](\d)\b', r'\g<1>1\2', date_str, flags=re.IGNORECASE)
    
    # Step c) Apostrophe-year normalization
    date_str = re.sub(r"\b([a-zA-Z]{3,9})[']\s*(\d{2})\b", r'\1 20\2', date_str, flags=re.IGNORECASE)
    
    # Step d) Compact month+year normalization
    date_str = re.sub(r'\b([a-zA-Z]{3,9})(\d{2})\b', r'\1 20\2', date_str, flags=re.IGNORECASE)
    date_str = re.sub(r'\b([A-Za-z]{3,9})(\d{4})\b', r'\1 \2', date_str)
    
    # Step e) Normalize dotted months
    date_str = re.sub(r'([A-Za-z]+)\.\s*(\d{4})', r'\1 \2', date_str)
    date_str = re.sub(r'([A-Za-z]+)\.\s*(\d{2})\b', r'\1 \2', date_str)
    
    # Step f) Special case for pure year tokens (YYYY)
    # Interpret as January 1st for consistent inclusive counting
    pure_year = re.fullmatch(r"[0-9OoIl]{4}", date_str)
    if pure_year:
        # Canonicalize OCR letters into digits
        y = date_str
        y = re.sub(r"[Oo]", "0", y, flags=re.IGNORECASE)
        y = re.sub(r"[lI]", "1", y)
        year = int(y)
        if 1950 <= year <= 2100:
            # Interpret as January 1st of that year
            return datetime(year, 1, 1)
    
    # Step g) Try dateparser
    settings = {
        'PREFER_DAY_OF_MONTH': 'first',
        'PREFER_DATES_FROM': 'past',
        'RETURN_AS_TIMEZONE_AWARE': False,
        'DATE_ORDER': 'MDY',
        'STRICT_PARSING': False,
        'RELATIVE_BASE': datetime.now()
    }
    
    try:
        parsed_date = dateparser.parse(date_str, settings=settings)
        if parsed_date:
            return datetime(parsed_date.year, parsed_date.month, 1)
    except Exception:
        pass
    
    # FALLBACK: Month + 2-digit year
    month_2digit = re.search(r'\b([A-Za-z]{3,9})\s+(\d{2})\b', date_str)
    if month_2digit:
        month_name = month_2digit.group(1)
        year_2d = int(month_2digit.group(2))
        year_4d = 2000 + year_2d
        fallback_str = f"{month_name} {year_4d}"
        try:
            parsed_date = dateparser.parse(fallback_str, settings=settings)
            if parsed_date:
                return datetime(parsed_date.year, parsed_date.month, 1)
        except Exception:
            pass
    
    # FALLBACK 1: 4-digit year only
    year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
    if year_match:
        year = int(year_match.group(0))
        return datetime(year, 1, 1)
    
    # FALLBACK 2: 2-digit year
    two_digit_year = re.search(r'\b(\d{2})\b', date_str)
    if two_digit_year:
        year_2d = int(two_digit_year.group(1))
        year = 2000 + year_2d if year_2d < 100 else year_2d
        if 1950 <= year <= 2100:
            return datetime(year, 1, 1)
    
    return None


def extract_date_ranges(text):
    """
    Extract date ranges using unified extraction strategy.
    
    Uses a single universal date token regex and passes raw tokens directly to
    parse_date_string() without manual format detection or reconstruction.
    
    Args:
        text (str): Experience section text
        
    Returns:
        list: List of date range tuples [(start_date, end_date), ...]
    """
    # Normalize whitespace
    text = ''.join(' ' if unicodedata.category(c) == 'Zs' else c for c in text)
    text = re.sub(r'\s+', ' ', text)
    
    # Universal date token regex - matches ANY date format (OCR-aware)
    # Allows O/o/I/i/l in year positions to match OCR errors like 2O21, 202l
    DATE = r"[A-Za-z]{3,9}\.?\s*[''\u2019]?\s*[0-9OoIl]{2,4}|\d{1,2}[/\-\.][0-9OoIl]{4}|[0-9OoIl]{4}[/\-\.]\d{1,2}|[0-9OoIl]{4}"
    
    # Universal separator pattern
    SEP = r"(?:\s*(?:-|–|—|―|‒|−|\u2010|\u2011|\u2012|\u2013|\u2014|\u2212|to|till|until|up\s+to|→|~)\s*)"
    
    # Present/current keywords
    PRESENT = r"(?:present|current|now|till\s+date|to\s+date|ongoing|continuing)"
    
    # Universal date-range pattern
    pattern = rf"({DATE}){SEP}({DATE}|{PRESENT})"
    
    date_ranges = []
    seen_ranges = set()
    
    matches = re.finditer(pattern, text, re.IGNORECASE)
    
    for match in matches:
        # Extract raw tokens - DO NOT reconstruct manually
        start_raw = match.group(1).strip()
        end_raw = match.group(2).strip()
        
        # Pass raw tokens directly to parse_date_string()
        try:
            start_date = parse_date_string(start_raw)
            end_date = parse_date_string(end_raw)
            
            if start_date and end_date:
                if end_date >= start_date:
                    range_key = (start_date.year, start_date.month, end_date.year, end_date.month)
                    if range_key not in seen_ranges:
                        seen_ranges.add(range_key)
                        date_ranges.append((start_date, end_date))
        except Exception:
            continue
    
    return date_ranges


def calculate_total_months(date_ranges):
    """
    Calculate total months of experience using inclusive counting.
    
    Args:
        date_ranges (list): List of (start_date, end_date) tuples
        
    Returns:
        tuple: (total_years, total_months, experience_ranges)
    """
    total_months = 0
    experience_ranges = []
    
    for start_date, end_date in date_ranges:
        delta = relativedelta(end_date, start_date)
        
        if INCLUSIVE_MONTH_COUNT:
            months = delta.years * 12 + delta.months + 1
        else:
            months = delta.years * 12 + delta.months
        
        if months < 1:
            months = 1
        
        total_months += months
        
        start_str = start_date.strftime('%b %Y')
        
        now = datetime.now()
        if abs((end_date - now).days) <= 1:
            end_str = 'Present'
        else:
            end_str = end_date.strftime('%b %Y')
        
        experience_ranges.append({
            'start': start_str,
            'end': end_str,
            'months': months
        })
    
    years = total_months // 12
    months = total_months % 12
    
    return (years, months, experience_ranges)


def analyze_experience(resume_text, jd_text):
    """
    Analyze experience match between resume and job description
    
    Args:
        resume_text (str): Resume text content
        jd_text (str): Job description text content
        
    Returns:
        dict: Dictionary with experience analysis results
    """
    try:
        jd_required_years, jd_required_months = extract_jd_required_experience(jd_text)
        experience_section = extract_experience_section(resume_text)
        
        experience_section = ''.join(' ' if unicodedata.category(c) == 'Zs' else c for c in experience_section)
        experience_section = re.sub(r'\s+', ' ', experience_section)
        
        date_ranges = extract_date_ranges(experience_section)
        
        if date_ranges:
            total_years, total_months, experience_ranges = calculate_total_months(date_ranges)
        else:
            total_years, total_months, experience_ranges = 0, 0, []
        
        resume_total_months = total_years * 12 + total_months
        jd_total_months = jd_required_years * 12 + jd_required_months
        meets_requirement = resume_total_months >= jd_total_months
        
        return {
            'total_experience_years': total_years,
            'total_experience_months': total_months,
            'jd_required_years': jd_required_years,
            'jd_required_months': jd_required_months,
            'meets_requirement': meets_requirement,
            'experience_ranges': experience_ranges
        }
    except Exception as e:
        return {
            'total_experience_years': 0,
            'total_experience_months': 0,
            'jd_required_years': 0,
            'jd_required_months': 0,
            'meets_requirement': False,
            'experience_ranges': []
        }
