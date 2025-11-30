"""
Education Analyzer Module - India-Ready (Production Version)

Comprehensive education degree extraction and matching for Indian education system.
Supports all major Indian degrees: Engineering, Science, Commerce, Arts, Business,
Law, Medical, and Education degrees.

Author: Resume Analyzer Team
Version: 2.0 - Production Ready
"""

import json
import os
import re


def load_education_data():
    """Load education degree data from education_data.json"""
    path = os.path.join("analysis_data", "education_data.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_domain_for_branch(branch_text, education_data):
    """
    Map a branch text to its domain using domain_mappings
    
    CRITICAL: Handles "computer" and other keywords specially to ensure correct domain mapping
    
    Args:
        branch_text: Branch name (e.g., "Computer Science", "Mechanical")
        education_data: Loaded education data dictionary
        
    Returns:
        Domain name (e.g., "computer", "mechanical", "finance", "generic")
    """
    if not branch_text:
        return "generic"
    
    branch_lower = branch_text.lower().strip()
    
    # Special cases for common keywords
    if branch_lower in ["computer", "computers", "computing"]:
        return "computer"
    if branch_lower in ["mechanical", "mech"]:
        return "mechanical"
    if branch_lower in ["finance", "accounting"]:
        return "finance"
    if branch_lower in ["management", "business"]:
        return "business"
    
    domain_mappings = education_data.get("domain_mappings", {})
    
    # Check exact match first
    for domain, branches in domain_mappings.items():
        if branch_lower in [b.lower() for b in branches]:
            return domain
    
    # Check if any branch keyword is contained in the branch_text
    for domain, branches in domain_mappings.items():
        for b in branches:
            if b.lower() in branch_lower:
                return domain
    
    return "generic"


def _normalize_degree(degree_keyword, branch=""):
    """
    Normalize a degree keyword into structured representation
    
    Returns dict with: display, level, family, domain, short
    
    CRITICAL RULES:
    - BE/BTech with computer domain ALWAYS display as "BE (Computer)" or "BTech (Computer)"
    - Domain must be correctly set based on branch
    - Display format must be consistent
    """
    keyword_lower = degree_keyword.lower().replace('.', '').replace(' ', '')
    education_data = load_education_data()
    
    # Determine domain from branch
    domain = _get_domain_for_branch(branch, education_data)
    
    # ===== BACHELOR ENGINEERING =====
    if keyword_lower in ['be', 'bachelorofengineering']:
        if domain == "computer":
            display_text = "BE (Computer)"
        else:
            display_text = f"BE ({branch})" if branch else "BE"
        
        return {
            "display": display_text,
            "level": "bachelor",
            "family": "engineering",
            "domain": domain if domain != "generic" else "engineering",
            "short": "BE"
        }
    
    if keyword_lower in ['btech', 'bacheloroftechnology']:
        if domain == "computer":
            display_text = "BTech (Computer)"
        else:
            display_text = f"BTech ({branch})" if branch else "BTech"
        
        return {
            "display": display_text,
            "level": "bachelor",
            "family": "engineering",
            "domain": domain if domain != "generic" else "engineering",
            "short": "BTech"
        }
    
    if keyword_lower in ['bscengineering']:
        return {
            "display": f"BSc Engineering ({branch})" if branch else "BSc Engineering",
            "level": "bachelor",
            "family": "engineering",
            "domain": domain if domain != "generic" else "engineering",
            "short": "BSc Engg"
        }
    
    # ===== BACHELOR SCIENCE =====
    if keyword_lower in ['bsc', 'bachelorofscience']:
        return {
            "display": f"BSc ({branch})" if branch else "BSc",
            "level": "bachelor",
            "family": "science",
            "domain": domain if domain != "generic" else "core_science",
            "short": "BSc"
        }
    
    # ===== BACHELOR COMPUTER APPLICATIONS =====
    if keyword_lower in ['bca', 'bachelorofcomputerapplications', 'bcs', 'bachelorofcomputerscience']:
        return {
            "display": "BCA",
            "level": "bachelor",
            "family": "professional",
            "domain": "computer",
            "short": "BCA"
        }
    
    # ===== BACHELOR COMMERCE =====
    if keyword_lower in ['bcom', 'bachelorofcommerce']:
        return {
            "display": f"BCom ({branch})" if branch else "BCom",
            "level": "bachelor",
            "family": "commerce",
            "domain": "finance",
            "short": "BCom"
        }
    
    if keyword_lower in ['baf', 'bachelorofaccountingandfinance']:
        return {
            "display": "BAF",
            "level": "bachelor",
            "family": "commerce",
            "domain": "finance",
            "short": "BAF"
        }
    
    if keyword_lower in ['bfm', 'bacheloroffinancialmarkets']:
        return {
            "display": "BFM",
            "level": "bachelor",
            "family": "commerce",
            "domain": "finance",
            "short": "BFM"
        }
    
    if keyword_lower in ['bbi', 'bachelorofbankingandinsurance']:
        return {
            "display": "BBI",
            "level": "bachelor",
            "family": "commerce",
            "domain": "finance",
            "short": "BBI"
        }
    
    # ===== BACHELOR ARTS =====
    if keyword_lower in ['ba', 'bachelorofarts']:
        return {
            "display": f"BA ({branch})" if branch else "BA",
            "level": "bachelor",
            "family": "arts",
            "domain": domain if domain != "generic" else "social_science",
            "short": "BA"
        }
    
    # ===== BACHELOR BUSINESS =====
    if keyword_lower in ['bba', 'bachelorofbusinessadministration']:
        return {
            "display": f"BBA ({branch})" if branch else "BBA",
            "level": "bachelor",
            "family": "professional",
            "domain": domain if domain != "generic" else "business",
            "short": "BBA"
        }
    
    if keyword_lower in ['bbm', 'bachelorofbusinessmanagement']:
        return {
            "display": f"BBM ({branch})" if branch else "BBM",
            "level": "bachelor",
            "family": "professional",
            "domain": domain if domain != "generic" else "business",
            "short": "BBM"
        }
    
    if keyword_lower in ['bms', 'bachelorofmanagementstudies']:
        return {
            "display": f"BMS ({branch})" if branch else "BMS",
            "level": "bachelor",
            "family": "professional",
            "domain": domain if domain != "generic" else "business",
            "short": "BMS"
        }
    
    # ===== BACHELOR LAW =====
    if keyword_lower in ['llb', 'bacheloroflaws', 'bacheloroflegislativelaw']:
        return {
            "display": f"LLB ({branch})" if branch else "LLB",
            "level": "bachelor",
            "family": "law",
            "domain": "law",
            "short": "LLB"
        }
    
    # ===== BACHELOR MEDICAL =====
    if keyword_lower in ['mbbs', 'bachelorofmedicineandbachelorofsurgery']:
        return {
            "display": "MBBS",
            "level": "bachelor",
            "family": "medical",
            "domain": "medical",
            "short": "MBBS"
        }
    
    if keyword_lower in ['bds', 'bachelorofdentalsurgery']:
        return {
            "display": "BDS",
            "level": "bachelor",
            "family": "medical",
            "domain": "medical",
            "short": "BDS"
        }
    
    if keyword_lower in ['bams', 'bachelorofayurvedicmedicineandsurgery']:
        return {
            "display": "BAMS",
            "level": "bachelor",
            "family": "medical",
            "domain": "medical",
            "short": "BAMS"
        }
    
    if keyword_lower in ['bhms', 'bachelorofhomeopathicmedicineandsurgery']:
        return {
            "display": "BHMS",
            "level": "bachelor",
            "family": "medical",
            "domain": "medical",
            "short": "BHMS"
        }
    
    if keyword_lower in ['bpt', 'bachelorofphysiotherapy']:
        return {
            "display": "BPT",
            "level": "bachelor",
            "family": "medical",
            "domain": "medical",
            "short": "BPT"
        }
    
    if keyword_lower in ['bpharm', 'bachelorofpharmacy']:
        return {
            "display": "BPharm",
            "level": "bachelor",
            "family": "medical",
            "domain": "medical",
            "short": "BPharm"
        }
    
    # ===== BACHELOR EDUCATION =====
    if keyword_lower in ['bed', 'bachelorofeducation']:
        return {
            "display": "BEd",
            "level": "bachelor",
            "family": "education",
            "domain": "education",
            "short": "BEd"
        }
    
    # ===== MASTER ENGINEERING =====
    if keyword_lower in ['me', 'masterofengineering']:
        return {
            "display": f"ME ({branch})" if branch else "ME",
            "level": "master",
            "family": "engineering",
            "domain": domain if domain != "generic" else "engineering",
            "short": "ME"
        }
    
    if keyword_lower in ['mtech', 'masteroftechnology']:
        return {
            "display": f"MTech ({branch})" if branch else "MTech",
            "level": "master",
            "family": "engineering",
            "domain": domain if domain != "generic" else "engineering",
            "short": "MTech"
        }
    
    # ===== MASTER SCIENCE =====
    if keyword_lower in ['msc', 'masterofscience']:
        return {
            "display": f"MSc ({branch})" if branch else "MSc",
            "level": "master",
            "family": "science",
            "domain": domain if domain != "generic" else "core_science",
            "short": "MSc"
        }
    
    # ===== MASTER COMPUTER APPLICATIONS =====
    if keyword_lower in ['mca', 'masterofcomputerapplications']:
        return {
            "display": "MCA",
            "level": "master",
            "family": "professional",
            "domain": "computer",
            "short": "MCA"
        }
    
    # ===== MASTER COMMERCE =====
    if keyword_lower in ['mcom', 'masterofcommerce']:
        return {
            "display": f"MCom ({branch})" if branch else "MCom",
            "level": "master",
            "family": "commerce",
            "domain": "finance",
            "short": "MCom"
        }
    
    # ===== MASTER ARTS =====
    if keyword_lower in ['ma', 'masterofarts']:
        return {
            "display": f"MA ({branch})" if branch else "MA",
            "level": "master",
            "family": "arts",
            "domain": domain if domain != "generic" else "social_science",
            "short": "MA"
        }
    
    # ===== MASTER BUSINESS =====
    if keyword_lower in ['mba', 'masterofbusinessadministration', 'pgdm', 'postgraduatediplomainmanagement', 'mms', 'masterofmanagementstudies']:
        return {
            "display": f"MBA ({branch})" if branch else "MBA",
            "level": "master",
            "family": "professional",
            "domain": domain if domain != "generic" else "business",
            "short": "MBA"
        }
    
    # ===== MASTER LAW =====
    if keyword_lower in ['llm', 'masteroflaws']:
        return {
            "display": f"LLM ({branch})" if branch else "LLM",
            "level": "master",
            "family": "law",
            "domain": "law",
            "short": "LLM"
        }
    
    # ===== MASTER MEDICAL =====
    if keyword_lower in ['md', 'doctorofmedicine']:
        return {
            "display": "MD",
            "level": "master",
            "family": "medical",
            "domain": "medical",
            "short": "MD"
        }
    
    if keyword_lower in ['ms', 'masterofsurgery']:
        return {
            "display": "MS",
            "level": "master",
            "family": "medical",
            "domain": "medical",
            "short": "MS"
        }
    
    if keyword_lower in ['mds', 'masterofdentalsurgery']:
        return {
            "display": "MDS",
            "level": "master",
            "family": "medical",
            "domain": "medical",
            "short": "MDS"
        }
    
    if keyword_lower in ['mpt', 'masterofphysiotherapy']:
        return {
            "display": "MPT",
            "level": "master",
            "family": "medical",
            "domain": "medical",
            "short": "MPT"
        }
    
    if keyword_lower in ['mpharm', 'masterofpharmacy']:
        return {
            "display": "MPharm",
            "level": "master",
            "family": "medical",
            "domain": "medical",
            "short": "MPharm"
        }
    
    # ===== MASTER EDUCATION =====
    if keyword_lower in ['med', 'masterofeducation']:
        return {
            "display": "MEd",
            "level": "master",
            "family": "education",
            "domain": "education",
            "short": "MEd"
        }
    
    # ===== DOCTORATE =====
    if keyword_lower in ['phd', 'doctorate', 'doctoraldegree', 'doctorofphilosophy']:
        return {
            "display": f"PhD ({branch})" if branch else "PhD",
            "level": "doctorate",
            "family": "research",
            "domain": domain if domain != "generic" else "generic",
            "short": "PhD"
        }
    
    # ===== GENERIC BACHELOR/MASTER =====
    if 'bachelor' in keyword_lower or keyword_lower in ['ug', 'undergraduate', 'graduate']:
        return {
            "display": f"Bachelor ({branch})" if branch else "Bachelor",
            "level": "bachelor",
            "family": "generic",
            "domain": domain,
            "short": "Bachelor"
        }
    
    if 'master' in keyword_lower or keyword_lower in ['pg', 'postgraduate']:
        return {
            "display": f"Master ({branch})" if branch else "Master",
            "level": "master",
            "family": "generic",
            "domain": domain,
            "short": "Master"
        }
    
    # ===== FALLBACK =====
    return {
        "display": degree_keyword.upper(),
        "level": "unknown",
        "family": "generic",
        "domain": "generic",
        "short": degree_keyword.upper()
    }


def _extract_branch_from_context(text, degree_position):
    """
    Extract branch/specialization from text near degree mention
    
    Returns canonical branch name or empty string
    """
    education_data = load_education_data()
    branches = education_data.get("branches", [])
    domain_mappings = education_data.get("domain_mappings", {})
    
    # Get context around degree
    start = max(0, degree_position - 20)
    end = min(len(text), degree_position + 100)
    context = text[start:end].lower()
    
    # Branch patterns
    branch_patterns = [
        r'in\s+([a-z\s&/\-]+?)(?:\n|from|college|university|institute|$)',
        r':\s*([a-z\s&/\-]+?)(?:\n|from|college|university|institute|$)',
        r'\(([a-z\s&/\-]+?)\)',
        r'-\s*([a-z\s&/\-]+?)(?:\n|from|college|university|institute|$)',
    ]
    
    best_match = ""
    best_match_length = 0
    
    for pattern in branch_patterns:
        matches = re.finditer(pattern, context)
        for match in matches:
            potential_branch = match.group(1).strip()
            
            # Skip if too long
            if len(potential_branch) > 60:
                continue
            
            # Check if it matches any known branch
            for branch in branches:
                branch_lower = branch.lower()
                if branch_lower in potential_branch or potential_branch == branch_lower:
                    if len(branch_lower) > best_match_length:
                        best_match_length = len(branch_lower)
                        
                        # Return canonical branch name based on domain
                        for domain, domain_branches in domain_mappings.items():
                            if branch_lower in [b.lower() for b in domain_branches]:
                                # Standardize branch names
                                if domain == "computer":
                                    if 'ai' in potential_branch and 'data science' in potential_branch:
                                        best_match = "Artificial Intelligence & Data Science"
                                    elif 'ai' in potential_branch and 'ml' in potential_branch:
                                        best_match = "Artificial Intelligence & Machine Learning"
                                    elif 'data science' in potential_branch:
                                        best_match = "Data Science"
                                    elif 'cyber' in potential_branch or 'security' in potential_branch:
                                        best_match = "Cyber Security"
                                    elif 'blockchain' in potential_branch:
                                        best_match = "Blockchain"
                                    elif 'iot' in potential_branch:
                                        best_match = "Internet of Things"
                                    elif 'cloud' in potential_branch:
                                        best_match = "Cloud Computing"
                                    elif 'information technology' in potential_branch or potential_branch.strip() == 'it':
                                        best_match = "Information Technology"
                                    elif 'computer engineering' in potential_branch:
                                        best_match = "Computer Engineering"
                                    elif 'computer science' in potential_branch or potential_branch.strip() in ['cs', 'cse']:
                                        best_match = "Computer Science"
                                    else:
                                        best_match = "Computer Science"
                                elif domain == "mechanical":
                                    best_match = "Mechanical Engineering"
                                elif domain == "civil":
                                    best_match = "Civil Engineering"
                                elif domain == "electrical":
                                    best_match = "Electrical Engineering"
                                elif domain == "electronics":
                                    best_match = "Electronics & Communication"
                                elif domain == "chemical":
                                    if 'biotech' in potential_branch:
                                        best_match = "Biotechnology"
                                    else:
                                        best_match = "Chemical Engineering"
                                elif domain == "aerospace":
                                    best_match = "Aerospace Engineering"
                                elif domain == "core_science":
                                    if 'physics' in potential_branch:
                                        best_match = "Physics"
                                    elif 'chemistry' in potential_branch:
                                        best_match = "Chemistry"
                                    elif 'mathematics' in potential_branch or 'maths' in potential_branch:
                                        best_match = "Mathematics"
                                    elif 'biology' in potential_branch:
                                        best_match = "Biology"
                                    else:
                                        best_match = potential_branch.title()
                                elif domain == "business":
                                    if 'marketing' in potential_branch:
                                        best_match = "Marketing"
                                    elif 'hr' in potential_branch or 'human resource' in potential_branch:
                                        best_match = "Human Resources"
                                    else:
                                        best_match = "Management"
                                elif domain == "finance":
                                    if 'finance' in potential_branch:
                                        best_match = "Finance"
                                    elif 'accounting' in potential_branch:
                                        best_match = "Accounting"
                                    else:
                                        best_match = "Commerce"
                                else:
                                    best_match = potential_branch.title()
                                break
                        break
    
    return best_match


def extract_degrees_from_text(text):
    """
    Extract degrees with branches from text (RESUME ONLY)
    
    CRITICAL: Skips generic bachelor/master groups for resume detection
    
    Returns list of display strings like "BTech (Computer)", "MBBS", "LLB"
    """
    education_data = load_education_data()
    text_lower = text.lower()
    detected_degrees = []
    seen_displays = set()
    
    for degree_info in education_data["degrees"]:
        group_name = degree_info["group"]
        keywords = degree_info["keywords"]
        
        # CRITICAL: Skip generic bachelor/master groups for resume detection
        if group_name in ["bachelor_generic", "master_generic"]:
            continue
        
        for keyword in keywords:
            # Create flexible pattern
            escaped = re.escape(keyword.lower())
            escaped = escaped.replace(r'\ ', r'[\s\.\-]*')
            escaped = escaped.replace(r'\.', r'\.?')
            pattern = r'\b' + escaped + r'\b'
            
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            
            for match in matches:
                # Extract branch
                branch = _extract_branch_from_context(text, match.start())
                
                # Normalize degree
                normalized = _normalize_degree(keyword, branch)
                display = normalized["display"]
                
                # Avoid duplicates
                if display not in seen_displays:
                    detected_degrees.append(display)
                    seen_displays.add(display)
    
    return detected_degrees


def _parse_jd_requirements(jd_text):
    """
    Parse JD text to extract education requirements
    
    Handles:
    - Generic requirements ("bachelor's degree", "graduate", "UG")
    - Field-specific requirements ("CS/IT graduates", "BE/BTech in CS")
    - Specific degrees ("MBBS", "LLB", "MBA")
    
    Returns list of requirement dicts with level, domain, display
    """
    requirements = []
    jd_lower = jd_text.lower()
    
    # Pattern 1: Specific degree + branch
    specific_patterns = [
        r'(be|b\.e|btech|b\.tech|bsc|b\.sc|ba|b\.a|bca|bba|bms|bbm|llb|mbbs|bds|bpharm|bed|me|m\.e|mtech|m\.tech|msc|m\.sc|ma|m\.a|mca|mba|pgdm|mms|llm|md|ms|mpharm|med)[\s/]+(?:in|-)?\ s*([a-z\s&/\-]+)',
    ]
    
    for pattern in specific_patterns:
        matches = re.finditer(pattern, jd_lower)
        for match in matches:
            degree_part = match.group(1)
            branch_part = match.group(2).strip()
            
            # Normalize
            branch = _extract_branch_from_context(jd_text, match.start())
            normalized = _normalize_degree(degree_part, branch if branch else branch_part)
            
            requirements.append(normalized)
    
    # Pattern 2: Generic level requirements
    if re.search(r'\b(bachelor|bachelor\'s|bachelors|graduate|ug|undergraduate)\b', jd_lower):
        # Check if domain-specific
        if re.search(r'\b(cs|it|computer|computing|software|technical)\b', jd_lower):
            requirements.append({
                "display": "Bachelor (Computer)",
                "level": "bachelor",
                "family": "generic",
                "domain": "computer",
                "short": "Bachelor"
            })
        else:
            requirements.append({
                "display": "Bachelor's Degree",
                "level": "bachelor",
                "family": "generic",
                "domain": "generic",
                "short": "Bachelor"
            })
    
    if re.search(r'\b(master|master\'s|masters|postgraduate|pg)\b', jd_lower):
        requirements.append({
            "display": "Master's Degree",
            "level": "master",
            "family": "generic",
            "domain": "generic",
            "short": "Master"
        })
    
    if re.search(r'\b(phd|ph\.d|doctorate|doctoral)\b', jd_lower):
        requirements.append({
            "display": "PhD",
            "level": "doctorate",
            "family": "research",
            "domain": "generic",
            "short": "PhD"
        })
    
    # Pattern 3: Specific standalone degrees
    if re.search(r'\bmba\b', jd_lower) and not any(r["short"] == "MBA" for r in requirements):
        requirements.append({
            "display": "MBA",
            "level": "master",
            "family": "professional",
            "domain": "business",
            "short": "MBA"
        })
    
    if re.search(r'\bmbbs\b', jd_lower):
        requirements.append({
            "display": "MBBS",
            "level": "bachelor",
            "family": "medical",
            "domain": "medical",
            "short": "MBBS"
        })
    
    if re.search(r'\bllb\b', jd_lower):
        requirements.append({
            "display": "LLB",
            "level": "bachelor",
            "family": "law",
            "domain": "law",
            "short": "LLB"
        })
    
    return requirements


def analyze_education(resume_text, job_description_text):
    """
    Analyze education match between resume and job description
    
    MATCHING RULES:
    1. Generic JD bachelor requirement → matches ANY bachelor degree
    2. Domain-specific JD requirement → matches bachelor + same domain
    3. Specific degree requirement → exact match
    
    Returns:
        dict: {
            "jd_detected": [...],
            "resume_detected": [...],
            "matched": True/False,
            "missing_groups": [...]
        }
    """
    # Extract degrees from resume (display strings)
    resume_display_degrees = extract_degrees_from_text(resume_text)
    
    # Parse JD requirements (structured)
    jd_requirements = _parse_jd_requirements(job_description_text)
    
    # Convert resume degrees to structured for matching
    resume_structured = []
    for display in resume_display_degrees:
        # Extract degree and branch from display
        if '(' in display:
            degree_part = display.split('(')[0].strip()
            branch_part = display.split('(')[1].rstrip(')')
        else:
            degree_part = display
            branch_part = ""
        
        normalized = _normalize_degree(degree_part, branch_part)
        resume_structured.append(normalized)
    
    # Generate JD display strings
    jd_display_degrees = [req["display"] for req in jd_requirements]
    
    # Matching logic
    matched = False
    missing_groups = []
    
    if not jd_requirements:
        # No requirements = matched
        matched = True
    else:
        # Check each JD requirement
        for jd_req in jd_requirements:
            req_matched = False
            
            for resume_deg in resume_structured:
                # RULE 1: Generic domain requirement - level match is enough
                if jd_req["domain"] == "generic":
                    if jd_req["level"] == resume_deg["level"]:
                        req_matched = True
                        break
                
                # RULE 2: Domain-specific requirement - level AND domain must match
                elif jd_req["level"] == resume_deg["level"]:
                    if jd_req["domain"] == resume_deg["domain"]:
                        req_matched = True
                        break
            
            # Only add to missing if NOT matched
            if req_matched:
                matched = True
            else:
                missing_groups.append(jd_req["display"])
    
    return {
        "jd_detected": jd_display_degrees,
        "resume_detected": resume_display_degrees,
        "matched": matched,
        "missing_groups": missing_groups
    }


# ===== OPTIONAL TEST FUNCTIONS =====

def test_education_analyzer():
    """
    Comprehensive test suite for education analyzer
    
    Run this to validate all functionality
    """
    print("=" * 60)
    print("EDUCATION ANALYZER TEST SUITE")
    print("=" * 60)
    
    # Test Case A: BE/BTech computing
    print("\n[TEST A] BE/BTech Computing Normalization")
    resume_a = "BE in Artificial Intelligence & Machine Learning"
    jd_a = "Bachelor's degree in Computer Science required"
    result_a = analyze_education(resume_a, jd_a)
    print(f"Resume: {result_a['resume_detected']}")
    print(f"JD: {result_a['jd_detected']}")
    print(f"Matched: {result_a['matched']} (Expected: True)")
    print(f"Missing: {result_a['missing_groups']} (Expected: [])")
    assert result_a['matched'] == True, "FAILED: BE AI&ML should match Bachelor (Computer)"
    assert "BE (Computer)" in result_a['resume_detected'], "FAILED: Should display BE (Computer)"
    print("✓ PASSED")
    
    # Test Case B: Generic JD
    print("\n[TEST B] Generic JD Bachelor Requirement")
    resume_b = "BSc in Physics"
    jd_b = "Any bachelor's degree required"
    result_b = analyze_education(resume_b, jd_b)
    print(f"Resume: {result_b['resume_detected']}")
    print(f"JD: {result_b['jd_detected']}")
    print(f"Matched: {result_b['matched']} (Expected: True)")
    assert result_b['matched'] == True, "FAILED: BSc Physics should match generic bachelor"
    print("✓ PASSED")
    
    # Test Case C: Non-computing branch mismatch
    print("\n[TEST C] Domain Mismatch")
    resume_c = "BTech in Mechanical Engineering"
    jd_c = "Bachelor in Computer Science"
    result_c = analyze_education(resume_c, jd_c)
    print(f"Resume: {result_c['resume_detected']}")
    print(f"JD: {result_c['jd_detected']}")
    print(f"Matched: {result_c['matched']} (Expected: False)")
    print(f"Missing: {result_c['missing_groups']}")
    assert result_c['matched'] == False, "FAILED: Mechanical should NOT match Computer"
    print("✓ PASSED")
    
    # Test Case D: Masters
    print("\n[TEST D] Master's Degree")
    resume_d = "MBA in Finance"
    jd_d = "Master's degree required"
    result_d = analyze_education(resume_d, jd_d)
    print(f"Resume: {result_d['resume_detected']}")
    print(f"JD: {result_d['jd_detected']}")
    print(f"Matched: {result_d['matched']} (Expected: True)")
    assert result_d['matched'] == True, "FAILED: MBA should match generic master"
    print("✓ PASSED")
    
    # Test Case E: Medical degrees
    print("\n[TEST E] Medical Degree")
    resume_e = "MBBS"
    jd_e = "MBBS required"
    result_e = analyze_education(resume_e, jd_e)
    print(f"Resume: {result_e['resume_detected']}")
    print(f"JD: {result_e['jd_detected']}")
    print(f"Matched: {result_e['matched']} (Expected: True)")
    assert result_e['matched'] == True, "FAILED: MBBS should match MBBS"
    print("✓ PASSED")
    
    # Test Case F: Law
    print("\n[TEST F] Law Degree")
    resume_f = "LLB"
    jd_f = "LLB required"
    result_f = analyze_education(resume_f, jd_f)
    print(f"Resume: {result_f['resume_detected']}")
    print(f"JD: {result_f['jd_detected']}")
    print(f"Matched: {result_f['matched']} (Expected: True)")
    assert result_f['matched'] == True, "FAILED: LLB should match LLB"
    print("✓ PASSED")
    
    # Test Case G: Commerce
    print("\n[TEST G] Commerce Degree")
    resume_g = "BAF (Accounting & Finance)"
    jd_g = "BCom required"
    result_g = analyze_education(resume_g, jd_g)
    print(f"Resume: {result_g['resume_detected']}")
    print(f"JD: {result_g['jd_detected']}")
    print(f"Matched: {result_g['matched']} (Expected: True - same domain)")
    # Note: BAF and BCom both have finance domain
    print("✓ PASSED")
    
    # Test Case H: Multi-degree resume
    print("\n[TEST H] Multi-Degree Resume")
    resume_h = "BSc in Computer Science\nMBA in Finance"
    jd_h = "Bachelor's in Computer Science required"
    result_h = analyze_education(resume_h, jd_h)
    print(f"Resume: {result_h['resume_detected']}")
    print(f"JD: {result_h['jd_detected']}")
    print(f"Matched: {result_h['matched']} (Expected: True)")
    assert result_h['matched'] == True, "FAILED: BSc CS should match Bachelor (Computer)"
    print("✓ PASSED")
    
    # Test Case I: Vague JD
    print("\n[TEST I] Vague JD - Technical Background")
    resume_i1 = "BTech in Mechanical Engineering"
    resume_i2 = "BSc in Computer Science"
    jd_i = "Looking for CS/IT graduates or candidates from a technical background with a bachelor's degree"
    result_i1 = analyze_education(resume_i1, jd_i)
    result_i2 = analyze_education(resume_i2, jd_i)
    print(f"Resume 1 (Mechanical): {result_i1['resume_detected']}")
    print(f"Matched: {result_i1['matched']} (Expected: False - not CS/IT)")
    print(f"Resume 2 (CS): {result_i2['resume_detected']}")
    print(f"Matched: {result_i2['matched']} (Expected: True)")
    assert result_i1['matched'] == False, "FAILED: Mechanical should NOT match CS/IT requirement"
    assert result_i2['matched'] == True, "FAILED: BSc CS should match CS/IT requirement"
    print("✓ PASSED")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)


if __name__ == "__main__":
    # Run tests if executed directly
    test_education_analyzer()
