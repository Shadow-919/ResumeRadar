from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import os
import time
from threading import Lock, Thread
from werkzeug.utils import secure_filename

# Import utility functions from utils package
from utils import (
    extract_resume_text,
    analyze_sections,
    analyze_skills_match,
    analyze_resume_length,
    analyze_education,
    analyze_experience,
    analyze_action_verbs,
    save_education_section
)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True



# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

# In-memory session storage with thread safety
# Structure: {uid: {all_analysis_data, extracted_text, results, timestamp}}
in_memory_sessions = {}
session_lock = Lock()

# Clear any old references on startup
in_memory_sessions.clear()

# TTL Configuration (15 minutes)
SESSION_TTL_SECONDS = 900  # 15 minutes
CLEANUP_INTERVAL_SECONDS = 30  # Run cleanup every 30 seconds



# ===================== TTL CLEANUP SYSTEM =====================


def cleanup_expired_sessions():
    """Background daemon to auto-delete expired sessions based on TTL"""
    while True:
        try:
            time.sleep(CLEANUP_INTERVAL_SECONDS)
            current_time = time.time()
            
            with session_lock:
                expired_uids = []
                for uid, data in list(in_memory_sessions.items()):
                    timestamp = data.get('timestamp', 0)
                    if (current_time - timestamp) > SESSION_TTL_SECONDS:
                        expired_uids.append(uid)
                
                # Delete expired sessions
                for uid in expired_uids:
                    del in_memory_sessions[uid]
                    print(f"Auto-cleaned expired session: {uid}")
        
        except Exception as e:
            print(f"Error in cleanup thread: {e}")


# Start TTL cleanup daemon thread
cleanup_thread = Thread(target=cleanup_expired_sessions, daemon=True)
cleanup_thread.start()
print("[TTL Cleanup] Background cleanup thread started (15 min expiration)")



def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET'])
def upload_page():
    """Render the upload page and cleanup previous session data"""
    # Clean up in-memory session data when user returns to upload page
    uid = session.get('uid')
    if uid:
        with session_lock:
            if uid in in_memory_sessions:
                del in_memory_sessions[uid]
                print(f"Cleaned up in-memory session: {uid}")
    
    # Clear Flask session
    session.clear()
    
    return render_template('upload.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """Handle resume upload and analysis - FULLY IN-MEMORY, no disk writes"""
    try:
        
        # BACK-END VALIDATION
        if 'resume' not in request.files:
            flash('Please upload a resume file')
            return redirect(url_for('upload_page'))
        
        file = request.files['resume']
        job_description = request.form.get('job_description', '')
        
        if file.filename == '':
            flash('Please upload a resume file')
            return redirect(url_for('upload_page'))
        
        if not job_description.strip():
            flash('Please enter a job description')
            return redirect(url_for('upload_page'))
        
        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload PDF or DOCX only.')
            return redirect(url_for('upload_page'))
        
        # ===== CREATE UNIQUE SESSION ID =====
        uid = f"{int(time.time()*1000)}_{os.urandom(4).hex()}"
        session['uid'] = uid
        
        # Read file content into memory
        original_filename = secure_filename(file.filename)
        file_content = file.read()
        

        
        # ===== EXTRACT TEXT FROM RESUME (IN-MEMORY) =====
        resume_text = extract_resume_text(file_content, original_filename)
        
        if not resume_text or resume_text.strip() == '':
            flash('PDF/DOCX file does not contain detectable text. System rejected it.')
            return redirect(url_for('upload_page'))
        
        # ===== EXTRACT CANDIDATE INFO =====
        from utils.name_extractor import extract_name
        from utils.contact_extractor import extract_email, extract_phone
        
        candidate_name = extract_name(resume_text)
        candidate_email = extract_email(resume_text)
        candidate_phone = extract_phone(resume_text)
        
        # ===== PREPARE DATA =====
        resume_text_lower = resume_text.lower()
        job_description_lower = job_description.lower()
        
        # Extract education section text (no file writing)
        education_section_text = save_education_section(resume_text, None)
        
        # ===== RUN ANALYZERS (pass text directly) =====
        analysis_results = analyze_sections(resume_text)
        skills_results = analyze_skills_match(resume_text_lower, job_description_lower)
        education_results = analyze_education(education_section_text.lower(), job_description_lower)
        
        experience_results = analyze_experience(resume_text_lower, job_description_lower)
        
        from utils.action_verb_analyzer import categorize_resume_by_experience
        resume_type = categorize_resume_by_experience(
            experience_results['total_experience_years'],
            experience_results['total_experience_months']
        )
        
        length_results = analyze_resume_length(resume_text, resume_type)
        
        action_verb_results = analyze_action_verbs(
            resume_text, 
            length_results['word_count'],
            experience_results['total_experience_years'],
            experience_results['total_experience_months']
        )

      
        # ====== RADAR METRICS ======
        def _score_ratio(matched_list, total_count):
            if total_count > 0:
                return (len(matched_list) / total_count) * 100.0
            return None
        
        present_sections = analysis_results.get('present', [])
        missing_sections = analysis_results.get('missing', [])
        total_sections = len(present_sections) + len(missing_sections)
        sections_score = (len(present_sections) / total_sections) * 100.0 if total_sections > 0 else 50.0
        
        matched_skills = skills_results.get('matched_skills', []) or []
        missing_skills = skills_results.get('missing_skills', []) or []
        technical_matched = skills_results.get('technical_matched', []) or []
        technical_missing = skills_results.get('technical_missing', []) or []
        soft_matched = skills_results.get('soft_matched', []) or []
        soft_missing = skills_results.get('soft_missing', []) or []
        
        total_tech = len(technical_matched) + len(technical_missing)
        total_soft = len(soft_matched) + len(soft_missing)
        total_required = len(matched_skills) + len(missing_skills)
        
        tech_score = _score_ratio(technical_matched, total_tech)
        soft_score = _score_ratio(soft_matched, total_soft)
        
        if total_tech > 0 and total_soft > 0:
            skills_score = 0.7 * tech_score + 0.3 * soft_score
        elif total_tech > 0:
            skills_score = tech_score
        elif total_soft > 0:
            skills_score = soft_score
        elif total_required > 0:
            skills_score = (len(matched_skills) / total_required) * 100.0
        else:
            skills_score = 50.0
        
        category_to_score = {
            "Very Weak": 20.0,
            "Weak": 40.0,
            "Average": 60.0,
            "Strong": 80.0,
            "Outstanding": 100.0
        }
        action_category = action_verb_results.get("category", "Unknown")
        action_verb_score = category_to_score.get(action_category, 50.0)
        
        length_cat_map = {"Short": 60.0, "Good": 100.0, "Long": 70.0, "Overly Long": 40.0}
        resume_quality_score = length_cat_map.get(length_results.get("category", "Unknown"), 50.0)
        
        radar_metrics = {
            "skills": round(skills_score, 2),
            "action_verbs": round(action_verb_score, 2),
            "sections": round(sections_score, 2),
            "resume_quality": round(resume_quality_score, 2),
        }
        
        # ====== ATS SCORE ======
        ats_skills_score = radar_metrics["skills"]
        ats_action_verb_score = radar_metrics["action_verbs"]
        ats_sections_score = radar_metrics["sections"]
        ats_resume_length_score = radar_metrics["resume_quality"]
        
        edu_matched = education_results.get("matched", False)
        if edu_matched:
            ats_education_score = 100.0
        else:
            jd_detected = education_results.get("jd_detected", [])
            ats_education_score = 80.0 if not jd_detected else 40.0
        
        jd_years = experience_results.get("jd_required_years", 0)
        jd_months = experience_results.get("jd_required_months", 0)
        meets_requirement = experience_results.get("meets_requirement", False)
        
        if jd_years == 0 and jd_months == 0:
            ats_experience_score = 80.0
        elif meets_requirement:
            ats_experience_score = 100.0
        else:
            jd_total = jd_years * 12 + jd_months
            resume_total = (
                experience_results.get("total_experience_years", 0) * 12 +
                experience_results.get("total_experience_months", 0)
            )
            gap = jd_total - resume_total
            ats_experience_score = 70.0 if gap <= 12 else 40.0
        
        ats_score = (
            0.35 * ats_skills_score +
            0.15 * ats_action_verb_score +
            0.15 * ats_sections_score +
            0.10 * ats_resume_length_score +
            0.10 * ats_education_score +
            0.15 * ats_experience_score
        )
        ats_score = max(0, min(100, round(ats_score, 2)))
        
        ats_breakdown = {
            "Skills": round(ats_skills_score, 2),
            "Action Verbs": round(ats_action_verb_score, 2),
            "Sections": round(ats_sections_score, 2),
            "Resume Length": round(ats_resume_length_score, 2),
            "Education": round(ats_education_score, 2),
            "Experience": round(ats_experience_score, 2),
        }

        # ===== SAVE ALL DATA TO IN-MEMORY STORAGE =====
        with session_lock:
            in_memory_sessions[uid] = {
                # TTL timestamp
                'timestamp': time.time(),
                # Extracted text
                'name': candidate_name,
                'resume_text': resume_text_lower,
                'job_description': job_description_lower,
                'education_extracted': education_section_text.lower(),
                # Analysis results
                'analysis_results': analysis_results,
                'skills_results': skills_results,
                'length_results': length_results,
                'education_results': education_results,
                'experience_results': experience_results,
                'action_verb_results': action_verb_results,
                # Candidate info
                'candidate_name': candidate_name,
                'candidate_email': candidate_email,
                'candidate_phone': candidate_phone,
                # Scores
                'radar_metrics': radar_metrics,
                'ats_score': ats_score,
                'ats_breakdown': ats_breakdown
            }
        
        return redirect(url_for('result_page'))
    
    except Exception as e:
        # Log error to console (visible in hosting logs only)
        print(f"ANALYZE ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up in-memory session if created
        uid = session.get('uid')
        if uid:
            with session_lock:
                if uid in in_memory_sessions:
                    del in_memory_sessions[uid]
        
        # Show generic error to user
        flash('System memory error. Please try again.')
        return redirect(url_for('upload_page'))


@app.route('/result', methods=['GET'])
def result_page():
    """Display analysis results - reads from in_memory_sessions"""
    # Get uid from Flask session
    uid = session.get('uid')
    if not uid:
        flash('No analysis data found. Please upload a resume first.')
        return redirect(url_for('upload_page'))
    
    # Read all data from in-memory storage
    with session_lock:
        data = in_memory_sessions.get(uid)
    
    if not data:
        flash('Session expired. Please upload a resume again.')
        return redirect(url_for('upload_page'))
    
    # Extract all data from in-memory storage
    analysis_results = data.get('analysis_results', {'present': [], 'missing': []})
    skills_results = data.get('skills_results', {
        'matched_skills': [],
        'missing_skills': [],
        'technical_matched': [],
        'technical_missing': [],
        'soft_matched': [],
        'soft_missing': []
    })
    length_results = data.get('length_results', {
        'category': 'Unknown', 
        'color': '#666666', 
        'description': 'Unable to analyze', 
        'word_count': 0,
        'resume_type': 'unknown'
    })
    education_results = data.get('education_results', {
        'jd_detected': [],
        'resume_detected': [],
        'matched': True,
        'missing_groups': []
    })
    experience_results = data.get('experience_results', {
        'total_experience_years': 0,
        'total_experience_months': 0,
        'jd_required_years': 0,
        'jd_required_months': 0,
        'meets_requirement': True,
        'experience_ranges': []
    })
    action_verb_results = data.get('action_verb_results', {
        'action_verb_count': 0,
        'category': 'Unknown',
        'color': '#666666',
        'description': 'Unable to analyze action verb usage.',
        'resume_type': 'unknown'
    })
    
    candidate_name = data.get('candidate_name', '')
    candidate_email = data.get('candidate_email', '')
    candidate_phone = data.get('candidate_phone', '')
    
    radar_metrics = data.get('radar_metrics', None)
    ats_score = data.get('ats_score', None)
    ats_breakdown = data.get('ats_breakdown', None)
    
    return render_template(
        'result.html',
        results=analysis_results,
        skills=skills_results,
        length=length_results,
        technical_matched=skills_results.get('technical_matched', []),
        technical_missing=skills_results.get('technical_missing', []),
        soft_matched=skills_results.get('soft_matched', []),
        soft_missing=skills_results.get('soft_missing', []),
        education=education_results,
        experience=experience_results,
        action_verb_results=action_verb_results,
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        candidate_phone=candidate_phone,
        radar_metrics=radar_metrics,
        ats_score=ats_score,
        ats_breakdown=ats_breakdown
    )


@app.route('/download-report', methods=['GET'])
def download_report():
    """Generate and download PDF report - reads from in_memory_sessions"""
    try:
        # Get uid from Flask session
        uid = session.get('uid')
        if not uid:
            flash('No analysis data found. Please upload a resume first.')
            return redirect(url_for('upload_page'))
        
        # Read all data from in-memory storage
        with session_lock:
            data = in_memory_sessions.get(uid)
        
        if not data:
            flash('Session expired. Please upload a resume again.')
            return redirect(url_for('upload_page'))
        
        # Get data from in-memory storage
        candidate_name = data.get('candidate_name', 'Candidate')
        ats_score = data.get('ats_score', 0)
        ats_breakdown = data.get('ats_breakdown', {})
        analysis_results = data.get('analysis_results', {'present': [], 'missing': []})
        skills_results = data.get('skills_results', {})
        education_results = data.get('education_results', {})
        experience_results = data.get('experience_results', {})
        action_verb_results = data.get('action_verb_results', {})
        length_results = data.get('length_results', {})
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30,
            alignment=1  # Center
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#764ba2'),
            spaceAfter=12,
            spaceBefore=12
        )
        normal_style = styles['Normal']
        
        # Title
        elements.append(Paragraph("Resume Analysis Report", title_style))
        elements.append(Spacer(1, 12))
        
        # Candidate Info
        elements.append(Paragraph("Candidate Profile", heading_style))
        candidate_data = [
            ['Name:', candidate_name],
            ['Email:', data.get('candidate_email', 'Not Found')],
            ['Phone:', data.get('candidate_phone', 'Not Found')],
            ['Experience:', f"{experience_results.get('total_experience_years', 0)} years {experience_results.get('total_experience_months', 0)} months"]
        ]
        candidate_table = Table(candidate_data, colWidths=[1.5*inch, 4*inch])
        candidate_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#333333')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        elements.append(candidate_table)
        elements.append(Spacer(1, 20))
        
        # ATS Score
        elements.append(Paragraph("ATS Score", heading_style))
        ats_status = "Excellent" if ats_score >= 75 else "Good" if ats_score >= 60 else "Fair" if ats_score >= 40 else "Needs Improvement"
        elements.append(Paragraph(f"<b>Overall Score:</b> {ats_score}% ({ats_status})", normal_style))
        elements.append(Spacer(1, 12))
        
        # ATS Breakdown
        if ats_breakdown:
            breakdown_data = [['Component', 'Score']]
            for key, value in ats_breakdown.items():
                breakdown_data.append([key, f"{value}%"])
            
            breakdown_table = Table(breakdown_data, colWidths=[3*inch, 2*inch])
            breakdown_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(breakdown_table)
        elements.append(Spacer(1, 20))
        
        # Resume Length
        elements.append(Paragraph("Resume Length Analysis", heading_style))
        elements.append(Paragraph(f"<b>Category:</b> {length_results.get('category', 'Unknown')}", normal_style))
        elements.append(Paragraph(f"<b>Word Count:</b> {length_results.get('word_count', 0)}", normal_style))
        elements.append(Paragraph(f"<b>Description:</b> {length_results.get('description', 'N/A')}", normal_style))
        elements.append(Spacer(1, 20))
        
        # Action Verbs
        elements.append(Paragraph("Action Verb Usage", heading_style))
        elements.append(Paragraph(f"<b>Category:</b> {action_verb_results.get('category', 'Unknown')}", normal_style))
        elements.append(Paragraph(f"<b>Count:</b> {action_verb_results.get('action_verb_count', 0)}", normal_style))
        elements.append(Paragraph(f"<b>Assessment:</b> {action_verb_results.get('description', 'N/A')}", normal_style))
        elements.append(Spacer(1, 20))
        
        # Section Coverage
        elements.append(Paragraph("Section Coverage", heading_style))
        present_sections = ', '.join(analysis_results.get('present', [])) if analysis_results.get('present') else 'None'
        missing_sections = ', '.join(analysis_results.get('missing', [])) if analysis_results.get('missing') else 'None'
        elements.append(Paragraph(f"<b>Present Sections:</b> {present_sections}", normal_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(f"<b>Missing Sections:</b> {missing_sections}", normal_style))
        elements.append(Spacer(1, 20))
        
        # Skills Match
        elements.append(Paragraph("Skills Analysis", heading_style))
        matched_skills = ', '.join(skills_results.get('matched_skills', [])) if skills_results.get('matched_skills') else 'None'
        missing_skills = ', '.join(skills_results.get('missing_skills', [])) if skills_results.get('missing_skills') else 'None'
        elements.append(Paragraph(f"<b>Matched Skills:</b> {matched_skills}", normal_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(f"<b>Missing Skills:</b> {missing_skills}", normal_style))
        elements.append(Spacer(1, 20))
        
        # Education
        elements.append(Paragraph("Education Analysis", heading_style))
        edu_status = "Requirements Met" if education_results.get('matched') else "Requirements Not Met"
        elements.append(Paragraph(f"<b>Status:</b> {edu_status}", normal_style))
        resume_edu = ', '.join(education_results.get('resume_detected', [])) if education_results.get('resume_detected') else 'None detected'
        elements.append(Paragraph(f"<b>Your Qualifications:</b> {resume_edu}", normal_style))
        elements.append(Spacer(1, 20))
        
        # Experience
        elements.append(Paragraph("Experience Analysis", heading_style))
        exp_status = "Requirements Met" if experience_results.get('meets_requirement') else "Requirements Not Met"
        elements.append(Paragraph(f"<b>Status:</b> {exp_status}", normal_style))
        elements.append(Paragraph(f"<b>Your Experience:</b> {experience_results.get('total_experience_years', 0)} years {experience_results.get('total_experience_months', 0)} months", normal_style))
        elements.append(Paragraph(f"<b>Required Experience:</b> {experience_results.get('jd_required_years', 0)} years {experience_results.get('jd_required_months', 0)} months", normal_style))
        elements.append(Spacer(1, 20))
        
        # Recommendations
        elements.append(Paragraph("Recommendations", heading_style))
        recommendations = []
        if ats_score < 60:
            recommendations.append("• Focus on improving your ATS score by addressing missing skills and sections")
        if missing_sections:
            recommendations.append(f"• Add missing sections: {', '.join(analysis_results.get('missing', []))}")
        if skills_results.get('missing_skills'):
            recommendations.append(f"• Acquire or highlight these skills: {', '.join(skills_results.get('missing_skills', [])[:5])}")
        if action_verb_results.get('category') in ['Weak', 'Very Weak']:
            recommendations.append("• Use more action verbs to describe your achievements")
        if not education_results.get('matched'):
            recommendations.append("• Ensure your education qualifications match the job requirements")
        if not experience_results.get('meets_requirement'):
            recommendations.append("• Consider applying to positions that better match your experience level")
        
        if recommendations:
            for rec in recommendations:
                elements.append(Paragraph(rec, normal_style))
        else:
            elements.append(Paragraph("Your resume looks great! Keep up the good work.", normal_style))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF data
        pdf_data = buffer.getvalue()
        buffer.close()
        
        # Create response
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=Resume_Analysis_{candidate_name.replace(" ", "_")}.pdf'
        
        return response
        
    except Exception as e:
        print(f"PDF GENERATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        flash('System memory error. Please try again.')
        return redirect(url_for('result_page'))






if __name__ == '__main__':
    app.run(host="127.0.0.1", debug=True, port=5001, use_reloader=True)
