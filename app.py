# -----------------------------------------------------------
#  Smart Resume Analyzer - FULL app.py (Premium PDF Layout)
#  • PDF: BaseDocTemplate header/footer, page numbers, full content
#  • Memory: TTL cleanup + immediate wipe on visiting upload page
#  • Render-safe: no background threads
# -----------------------------------------------------------

from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import os
import time
import traceback
from werkzeug.utils import secure_filename

# ---------------- Register Safe ReportLab Font ----------------
try:
    pdfmetrics.registerFont(TTFont("Helvetica", "Helvetica.ttf"))
except:
    pass  # system font already exists

# ---------------- Import Utility Modules ----------------
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
from utils.name_extractor import extract_name
from utils.contact_extractor import extract_email, extract_phone
from utils.action_verb_analyzer import categorize_resume_by_experience

# ---------------- Flask Setup ----------------
app = Flask(__name__)
app.secret_key = os.environ.get("APP_SECRET", "your-secret-key-here")
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_env.auto_reload = True

ALLOWED_EXTENSIONS = {"pdf", "docx"}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------- Session Store ----------------
from threading import Lock
session_lock = Lock()
in_memory_sessions = {}
SESSION_TTL_SECONDS = 900  # 15 minutes

# ---------------- TTL CLEANUP (Render Safe) ----------------
def cleanup_expired_sessions():
    now = time.time()
    expired = []
    with session_lock:
        for uid, stored in list(in_memory_sessions.items()):
            created_at = stored.get("created_at", 0)
            if now - created_at > SESSION_TTL_SECONDS:
                expired.append(uid)

        for uid in expired:
            in_memory_sessions.pop(uid, None)

@app.before_request
def auto_cleanup():
    cleanup_expired_sessions()

# ---------------- Upload Page ----------------
@app.route("/", methods=["GET"])
def upload_page():
    uid = session.get("uid")

    # Wipe user data whenever they return to upload page
    if uid:
        with session_lock:
            in_memory_sessions.pop(uid, None)

    session.clear()
    return render_template("upload.html")

# ---------------- Analyze Resume ----------------
@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        if "resume" not in request.files:
            flash("Please upload a resume file")
            return redirect(url_for("upload_page"))

        file = request.files["resume"]
        jd_text = request.form.get("job_description", "")

        if not jd_text.strip():
            flash("Please enter a job description")
            return redirect(url_for("upload_page"))

        if not allowed_file(file.filename):
            flash("Invalid file type. Please upload PDF or DOCX.")
            return redirect(url_for("upload_page"))

        # Create user session
        uid = f"{int(time.time()*1000)}_{os.urandom(4).hex()}"
        session["uid"] = uid
        session["report_ready"] = True

        original_filename = secure_filename(file.filename)
        file_bytes = file.read()
        unique_file_name = f"{uid}_{original_filename}"
        session["resume_file_path"] = unique_file_name

        resume_text = extract_resume_text(file_bytes, original_filename)
        if not resume_text.strip():
            flash("Resume contains no text.")
            return redirect(url_for("upload_page"))

        # Extract candidate data
        name = extract_name(resume_text) or "Candidate"
        email = extract_email(resume_text) or "N/A"
        phone = extract_phone(resume_text) or "N/A"

        resume_lower = resume_text.lower()
        jd_lower = jd_text.lower()
        edu_section = save_education_section(resume_text, None) or ""

        # Run analyzers
        analysis = analyze_sections(resume_text)
        skills = analyze_skills_match(resume_lower, jd_lower)
        edu = analyze_education(edu_section.lower(), jd_lower)
        exp = analyze_experience(resume_lower, jd_lower)

        resume_type = categorize_resume_by_experience(
            exp.get("total_experience_years", 0),
            exp.get("total_experience_months", 0)
        )

        length = analyze_resume_length(resume_text, resume_type)
        action = analyze_action_verbs(
            resume_text,
            length.get("word_count", 0),
            exp.get("total_experience_years", 0),
            exp.get("total_experience_months", 0)
        )

        # Calculations
        def _ratio(matched, total):
            return (len(matched) / total * 100) if total else None

        present = analysis.get("present", [])
        missing = analysis.get("missing", [])
        total_sections = len(present) + len(missing)
        sections_score = (len(present) / total_sections * 100) if total_sections else 50

        tech_matched = skills.get("technical_matched", [])
        tech_missing = skills.get("technical_missing", [])
        soft_matched = skills.get("soft_matched", [])
        soft_missing = skills.get("soft_missing", [])

        tech_score = _ratio(tech_matched, len(tech_matched) + len(tech_missing))
        soft_score = _ratio(soft_matched, len(soft_matched) + len(soft_missing))

        skills_score = (
            0.7 * tech_score + 0.3 * soft_score
            if tech_score and soft_score else (tech_score or soft_score or 50)
        )

        category_map = {"Very Weak": 20, "Weak": 40, "Average": 60, "Strong": 80, "Outstanding": 100}
        action_score = category_map.get(action.get("category", "Unknown"), 50)

        length_map = {"Short": 60, "Good": 100, "Long": 70, "Overly Long": 40}
        length_score = length_map.get(length.get("category", "Unknown"), 50)

        edu_score = 100 if edu.get("matched") else (40 if edu.get("jd_detected") else 80)

        if exp.get("jd_required_years") == 0:
            exp_score = 80
        elif exp.get("meets_requirement"):
            exp_score = 100
        else:
            exp_score = 70

        ats_score = round(max(0, min(100,
            0.35 * skills_score +
            0.15 * action_score +
            0.15 * sections_score +
            0.10 * length_score +
            0.10 * edu_score +
            0.15 * exp_score
        )), 2)

        ats_breakdown = {
            "Skills": round(skills_score, 2),
            "Action Verbs": round(action_score, 2),
            "Sections": round(sections_score, 2),
            "Resume Length": round(length_score, 2),
            "Education": round(edu_score, 2),
            "Experience": round(exp_score, 2),
        }

        # Save session
        with session_lock:
            in_memory_sessions[uid] = {
                "created_at": time.time(),
                "candidate_name": name,
                "candidate_email": email,
                "candidate_phone": phone,
                "resume_text": resume_lower,
                "job_description": jd_lower,
                "education_extracted": edu_section.lower(),
                "analysis_results": analysis,
                "skills_results": skills,
                "length_results": length,
                "education_results": edu,
                "experience_results": exp,
                "action_verb_results": action,
                "radar_metrics": {
                    "skills": round(skills_score, 2),
                    "action_verbs": round(action_score, 2),
                    "sections": round(sections_score, 2),
                    "resume_quality": round(length_score, 2)
                },
                "ats_score": ats_score,
                "ats_breakdown": ats_breakdown
            }

        return redirect(url_for("result_page"))

    except Exception as e:
        print("ANALYZE ERROR:", e)
        traceback.print_exc()
        flash("Unexpected error.")
        return redirect(url_for("upload_page"))

# ---------------- Result Page ----------------
@app.route("/result", methods=["GET"])
def result_page():
    uid = session.get("uid")
    if not uid:
        flash("Please upload a resume first.")
        return redirect(url_for("upload_page"))

    with session_lock:
        data = in_memory_sessions.get(uid)

    if not data:
        flash("Session expired. Please upload again.")
        return redirect(url_for("upload_page"))

    return render_template(
        "result.html",
        results=data.get("analysis_results"),
        skills=data.get("skills_results"),
        length=data.get("length_results"),
        education=data.get("education_results"),
        experience=data.get("experience_results"),
        technical_matched=data.get("skills_results", {}).get("technical_matched", []),
        technical_missing=data.get("skills_results", {}).get("technical_missing", []),
        soft_matched=data.get("skills_results", {}).get("soft_matched", []),
        soft_missing=data.get("skills_results", {}).get("soft_missing", []),
        action_verb_results=data.get("action_verb_results"),
        candidate_name=data.get("candidate_name"),
        candidate_email=data.get("candidate_email"),
        candidate_phone=data.get("candidate_phone"),
        radar_metrics=data.get("radar_metrics"),
        ats_score=data.get("ats_score"),
        ats_breakdown=data.get("ats_breakdown")
    )

# ---------------- PDF DOWNLOAD (Premium Layout) ----------------
def header_footer(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFillColor(colors.HexColor("#667eea"))
    canvas_obj.rect(0, 760, 612, 40, fill=1)
    canvas_obj.setFillColor(colors.white)
    canvas_obj.setFont("Helvetica-Bold", 14)
    canvas_obj.drawString(30, 775, "Resume Radar - Report")
    page_num = canvas_obj.getPageNumber()
    canvas_obj.setFont("Helvetica", 10)
    canvas_obj.setFillColor(colors.grey)
    canvas_obj.drawRightString(580, 20, f"Page {page_num}")
    canvas_obj.restoreState()

@app.route("/download-report", methods=["GET"])
def download_report():
    try:
        uid = session.get("uid")
        if not uid or not session.get("report_ready"):
            flash("Session expired.")
            return redirect(url_for("upload_page"))

        with session_lock:
            data = in_memory_sessions.get(uid)
        if not data:
            flash("Session expired.")
            return redirect(url_for("upload_page"))

        # Extract fields
        candidate_name = data.get("candidate_name", "Candidate")
        ats_score = data.get("ats_score", 0)
        ats_breakdown = data.get("ats_breakdown", {})
        analysis = data.get("analysis_results", {})
        skills = data.get("skills_results", {})
        edu = data.get("education_results", {})
        exp = data.get("experience_results", {})
        action = data.get("action_verb_results", {})
        length = data.get("length_results", {})
        resume_type = length.get("resume_type", "N/A")

        buffer = BytesIO()

        doc = BaseDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=72,
            rightMargin=72,
            topMargin=90,
            bottomMargin=40
        )
        frame = Frame(72, 40, 468, 700, id="normal")
        template = PageTemplate(id="report", frames=frame, onPage=header_footer)
        doc.addPageTemplates([template])

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=22, alignment=1)
        section_header = ParagraphStyle(
            "Section",
            parent=styles["Heading2"],
            fontSize=15,
            textColor=colors.white,
            backColor=colors.HexColor("#667eea"),
            spaceBefore=12,
            spaceAfter=6
        )
        normal = styles["Normal"]

        elements = []
        elements.append(Paragraph("Resume Analysis Report", title_style))
        elements.append(Spacer(1, 12))

        # Candidate Profile
        elements.append(Paragraph("Candidate Profile", section_header))
        table_data = [
            ["Name:", candidate_name],
            ["Email:", data.get("candidate_email", "N/A")],
            ["Phone:", data.get("candidate_phone", "N/A")],
            ["Experience:", f"{exp.get('total_experience_years', 0)} years {exp.get('total_experience_months', 0)} months"],
            ["Resume Type:", resume_type],
            ["Education:", ", ".join(edu.get("resume_detected", []) or ["None"])],
        ]
        t = Table(table_data, colWidths=[1.7 * inch, 4 * inch])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
            ("GRID", (0, 0), (-1, -1), 0.7, colors.grey),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 15))

        # ATS score section
        elements.append(Paragraph("ATS Score Summary", section_header))
        ats_status = (
            "Excellent" if ats_score >= 75 else
            "Good" if ats_score >= 60 else
            "Fair" if ats_score >= 40 else
            "Needs Improvement"
        )
        elements.append(Paragraph(f"<b>ATS Score:</b> {ats_score}% — {ats_status}", normal))
        elements.append(Spacer(1, 10))

        if ats_breakdown:
            rows = [["Component", "Score (%)"]]
            for k, v in ats_breakdown.items():
                rows.append([k, f"{v}%"])
            tb = Table(rows, colWidths=[3 * inch, 2 * inch])
            tb.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#764ba2")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(tb)
            elements.append(Spacer(1, 15))

        # Resume Length
        elements.append(Paragraph("Resume Length Analysis", section_header))
        elements.append(Paragraph(f"<b>Category:</b> {length.get('category')}", normal))
        elements.append(Paragraph(f"<b>Word Count:</b> {length.get('word_count')}", normal))
        elements.append(Paragraph(f"<b>Description:</b> {length.get('description')}", normal))
        elements.append(Spacer(1, 12))

        # Action Verbs
        elements.append(Paragraph("Action Verb Usage", section_header))
        elements.append(Paragraph(f"<b>Category:</b> {action.get('category')}", normal))
        elements.append(Paragraph(f"<b>Count:</b> {action.get('action_verb_count')}", normal))
        elements.append(Paragraph(f"<b>Assessment:</b> {action.get('description')}", normal))
        elements.append(Spacer(1, 12))

        # Section Coverage
        elements.append(Paragraph("Section Coverage", section_header))
        elements.append(Paragraph(
            f"<b>Present:</b> {', '.join(analysis.get('present', []) or ['None'])}",
            normal
        ))
        elements.append(Paragraph(
            f"<b>Missing:</b> {', '.join(analysis.get('missing', []) or ['None'])}",
            normal
        ))
        elements.append(Spacer(1, 12))

        # Skills Match
        elements.append(Paragraph("Skills Match Analysis", section_header))
        elements.append(Paragraph(
            f"<b>Matched:</b> {', '.join(skills.get('matched_skills', []) or ['None'])}",
            normal
        ))
        elements.append(Paragraph(
            f"<b>Missing:</b> {', '.join(skills.get('missing_skills', []) or ['None'])}",
            normal
        ))
        elements.append(Spacer(1, 12))

        # Education
        elements.append(Paragraph("Education Evaluation", section_header))
        edu_status = "Requirements Met" if edu.get("matched") else "Requirements Not Met"
        detected_edu = ", ".join(edu.get("resume_detected", []) or ["None"])
        elements.append(Paragraph(f"<b>Status:</b> {edu_status}", normal))
        elements.append(Paragraph(f"<b>Detected:</b> {detected_edu}", normal))
        elements.append(Spacer(1, 12))

        # Experience
        elements.append(Paragraph("Experience Evaluation", section_header))
        exp_status = "Requirements Met" if exp.get("meets_requirement") else "Requirements Not Met"
        elements.append(Paragraph(f"<b>Status:</b> {exp_status}", normal))
        elements.append(Paragraph(
            f"<b>Your Experience:</b> {exp.get('total_experience_years')} years "
            f"{exp.get('total_experience_months')} months",
            normal
        ))
        elements.append(Paragraph(
            f"<b>Required Experience:</b> {exp.get('jd_required_years')} years "
            f"{exp.get('jd_required_months')} months",
            normal
        ))
        elements.append(Spacer(1, 12))

        # Recommendations
        elements.append(Paragraph("Recommendations", section_header))
        recs = []

        if ats_score < 60:
            recs.append("• Improve ATS score by addressing missing skills & sections.")
        if analysis.get("missing"):
            recs.append("• Add missing resume sections: " + ", ".join(analysis["missing"]))
        if skills.get("missing_skills"):
            recs.append("• Strengthen missing skills: " + ", ".join(skills["missing_skills"][:5]))
        if action.get("category") in ["Weak", "Very Weak"]:
            recs.append("• Use stronger & varied action verbs.")
        if not edu.get("matched"):
            recs.append("• Ensure education matches job requirements.")
        if not exp.get("meets_requirement"):
            recs.append("• Apply to roles better aligned with your experience.")

        if not recs:
            recs.append("• Excellent resume! Very well optimized.")

        for r in recs:
            elements.append(Paragraph(r, normal))
            elements.append(Spacer(1, 6))

        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()

        response = make_response(pdf_data)
        response.headers["Content-Disposition"] = f'attachment; filename="Resume_Analysis_{candidate_name.replace(" ", "_")}.pdf"'
        response.headers["Content-Type"] = "application/pdf"
        return response

    except Exception as e:
        print("PDF ERROR:", e)
        traceback.print_exc()
        flash("Error generating report.")
        return redirect(url_for("result_page"))

# ---------------- Run App ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
