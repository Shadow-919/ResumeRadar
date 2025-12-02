# 🧠 Smart Resume Analyzer – ATS-Powered Resume Intelligence

**An intelligent NLP-driven system that analyzes resumes, evaluates ATS compatibility, matches skills with job descriptions, and generates detailed insights through an interactive, visually rich dashboard powered by Flask.**

🔗 **Live Demo:** *[Add Link]*  
🔗 **Project Video:** *[Add Link]*  

---

## 📌 What is ATS Resume Analysis?

Applicant Tracking Systems (ATS) are used by modern companies to automatically process and rank resumes.  
This project simulates ATS-style evaluation by extracting structured information using **NLP**, analyzing resume quality, and measuring its alignment with job requirements.

The system delivers a full breakdown of skills, experience, education, section completeness, and action verbs — all presented through a clean, real-time analysis dashboard.

---

## 🚀 Project Highlights

- ⚡ **Instant ATS evaluation** with multi-metric scoring  
- 🧠 Advanced **NLP pipelines** for extracting resume details  
- 🎯 **Skill matching engine** for technical & soft skills  
- 📊 **Interactive visual dashboard** using Chart.js  
- 📑 Intelligent **experience parsing** with date normalization  
- 🎓 **Education analysis** using mapped domains & degree groups  
- 🔍 **Resume section detection** for completeness scoring  
- 🛡️ **Privacy-first** — no resume or data is stored  

---

## 🏗️ System Architecture

The analyzer follows a modular NLP pipeline:

### **1. Text Extraction**
- PDF text extraction via **PyMuPDF**
- DOCX parsing via **python-docx**

### **2. Information Extraction**
- Name, email, phone extraction  
- Section detection  
- Education classification  
- Work experience timeline parsing  

### **3. Skill Matching Engine**
- Canonical skill normalization  
- Technical + soft skill libraries  
- JD-to-resume skill comparison  
- Abbreviation and synonym detection  

### **4. Scoring Algorithms**
- Overall ATS score  
- Skills match percentage  
- Action verb density  
- Resume length & readability  
- Section coverage score  

### **5. Visualization Layer**
- TailwindCSS UI  
- Chart.js graphs  
- Glass-morphism themed dashboard  

---

## 📂 Dataset & Resource Files

This project uses structured JSON datasets to maximize accuracy:

- 🔹 Technical skills library  
- 🔹 Soft skills dataset  
- 🔹 Education degree & domain mappings  
- 🔹 Action verbs list  
- 🔹 Section keywords for coverage analysis  

All datasets are fully customizable.

---

## 📊 Example Dashboard Screens

### 🖥️ Analysis Dashboard

<p align="center">
  <img src="assets/ADD_DASHBOARD_1" width="80%" />
  <img src="assets/ADD_DASHBOARD_2" width="80%" />
  <img src="assets/ADD_DASHBOARD_3" width="80%" />
</p>

---

## 📈 Sample ATS Insights

<table align="center">
  <tr>
    <td><img src="assets/ADD_OUTPUT_1" width="100%"></td>
    <td><img src="assets/ADD_OUTPUT_2" width="100%"></td>
  </tr>
  <tr>
    <td><img src="assets/ADD_OUTPUT_3" width="100%"></td>
    <td><img src="assets/ADD_OUTPUT_4" width="100%"></td>
  </tr>
</table>

---

## 🛠️ Tech Stack

- **Python**, **Flask**
- **PyMuPDF**, **python-docx**, **dateparser**
- **NLP + Regex pipelines**
- **HTML**, **CSS**, **TailwindCSS**
- **JavaScript**, **Chart.js**
- **Git**, **GitHub**

---

## 📦 Installation

```bash
git clone https://github.com/your-username/smart-resume-analyzer.git
cd smart-resume-analyzer
pip install -r requirements.txt
python app.py
