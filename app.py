import streamlit as st
import requests
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd
import concurrent.futures


BASE_URL = 'http://peoplepulse.diu.edu.bd:8189'

# CACHED Functions
@st.cache_data(ttl=3600)
def get_student_info(student_id):
    url = f"{BASE_URL}/result/studentInfo"
    params = {'studentId': student_id}
    response = requests.get(url, params=params)
    return response.json() if response.status_code == 200 else None

@st.cache_data(ttl=3600)
def get_semester_list():
    url = f"{BASE_URL}/result/semesterList"
    response = requests.get(url)
    return response.json() if response.status_code == 200 else None

@st.cache_data(ttl=3600)
def get_result_for_semester(student_id, semester_id):
    url = f"{BASE_URL}/result"
    params = {'studentId': student_id, 'semesterId': semester_id, 'grecaptcha': ''}
    response = requests.get(url, params=params)
    try:
        return response.json() if response.status_code == 200 else None
    except ValueError:
        return None

def fetch_all_semester_results(student_id, semesters):
    results_by_semester = {}

    def fetch(semester):
        try:
            sid = semester['semesterId']
            name = f"{semester['semesterName']} {semester['semesterYear']}"
            result = get_result_for_semester(student_id, sid)
            return name, result if result else []
        except Exception as e:
            print(f"Error fetching {semester['semesterName']} {semester['semesterYear']}: {e}")
            return semester['semesterName'], []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch, s) for s in semesters]
        for f in concurrent.futures.as_completed(futures):
            name, result = f.result()
            if result:  # Only add if data exists
                results_by_semester[name] = result

    return dict(sorted(results_by_semester.items()))  # Optional: sort by name

def create_pdf(student_info, semesters, total_cgpa):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    pdf.setTitle("Student Academic Transcript")
    page_number = 1  # Initial page

    def draw_footer():
        pdf.setFont("Helvetica-Oblique", 9)
        #pdf.drawCentredString(width / 2, 60, "Generated via Student Result Viewer App")
        #pdf.drawCentredString(width / 2, 45, "This App Made by ABDULLAH AL RIFAT")
        pdf.drawRightString(width - 50, 30, f"Page {page_number}")

    # Header
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawCentredString(width / 2, height - 50, "Daffodil International University")
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(width / 2, height - 70, "Academic Transcript")
    pdf.line(100, height - 75, width - 100, height - 75)

    # Student Info
    y = height - 110
    pdf.setFont("Helvetica", 11)
    if student_info:
        pdf.drawString(50, y, f"Name: {student_info.get('studentName')}")
        y -= 20
        pdf.drawString(50, y, f"Student ID: {student_info.get('studentId')}")
        y -= 20
        pdf.drawString(50, y, f"Program: {student_info.get('programName')}")
        y -= 20
        pdf.drawString(50, y, f"Department: {student_info.get('departmentName')}")
        y -= 20
        pdf.drawString(50, y, f"Campus: {student_info.get('campusName')}")
        y -= 30

    # Semester Results
    for semester_name, results in semesters.items():
        pdf.setFont("Helvetica-Bold", 14)
        #y-=15
        pdf.drawCentredString(300, y, f"{semester_name}")
        y -= 20
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(60, y, "Course Title")
        pdf.drawString(250, y, "Course Code")
        pdf.drawString(350, y, "Grade")
        pdf.drawString(420, y, "Credits")
        pdf.drawString(480, y, "CGPA")
        y -= 10
        pdf.line(50, y, width - 50, y)
        y -= 20

        pdf.setFont("Helvetica", 10)
        for result in results:
            pdf.drawString(60, y, result['courseTitle'][:30])
            pdf.drawString(250, y, result['customCourseId'])
            pdf.drawString(350, y, result['gradeLetter'])
            pdf.drawString(420, y, f"{result['totalCredit']}")
            pdf.drawString(480, y, f"{result['pointEquivalent']}")
            y -= 10
            if y < 80:
                draw_footer()
                pdf.showPage()
                page_number += 1
                y = height - 80

    pdf.line(50, y, width - 50, y)
    y -= 30

    # Total CGPA
    pdf.setFont("Helvetica-Bold", 14)
    if y < 100:
        draw_footer()
        pdf.showPage()
        page_number += 1
        y = height - 100
    pdf.drawString(50, y, f"Total CGPA: {total_cgpa:.2f}")

    pdf.setFont("Helvetica-Oblique", 9)
    y -= 20
    pdf.drawCentredString(width / 2, y, "Generated via Student Result Viewer App")
    y -= 10
    pdf.drawCentredString(width / 2, y, "This App Made by ABDULLAH AL RIFAT")

    # Final Footer
    draw_footer()
    pdf.save()
    buffer.seek(0)
    return buffer


# Streamlit App UI
st.set_page_config(page_title="Student Result Viewer", layout="centered", page_icon="📘")
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>Student Result Viewer</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>Easily View Student Information and Academic Results</h3>", unsafe_allow_html=True)

with st.form("student_form"):
    st.markdown("### Input Student Information")
    student_id = st.text_input("Enter Student ID:")
    add_defense = st.checkbox("Add Defense CGPA?")
    defense_cgpa = st.number_input("Enter Defense CGPA (Optional):", min_value=0.0, max_value=4.0, step=0.01) if add_defense else None
    col1, col2 = st.columns([3, 1])
    with col2:
        submitted = st.form_submit_button("Get Result")

if submitted and student_id:
    st.info(f"Fetching results for: **{student_id}**")

    student_info = get_student_info(student_id)
    if not student_info:
        st.error("Failed to fetch student information.")
    else:
        semesters = get_semester_list()
        if not semesters:
            st.error("Failed to fetch semester list.")
        else:
            semester_results = fetch_all_semester_results(student_id, semesters)

            st.markdown("<h3>🎓 Student Information</h3>", unsafe_allow_html=True)
            st.markdown(f"""
            - **Name:** {student_info.get('studentName')}
            - **ID:** {student_info.get('studentId')}
            - **Program:** {student_info.get('programName')}
            - **Department:** {student_info.get('departmentName')}
            - **Campus:** {student_info.get('campusName')}
            """)

            total_credits = 0
            weighted_sum = 0

            st.markdown("<h3>📜 Academic Results</h3>", unsafe_allow_html=True)
            for semester_name, results in semester_results.items():
                table = []
                for result in results:
                    table.append({
                        "Course Title": result['courseTitle'],
                        "Course Code": result['customCourseId'],
                        "Grade": result['gradeLetter'],
                        "Credits": float(result['totalCredit']),
                        "CGPA": float(result['pointEquivalent']),
                    })
                    weighted_sum += float(result['pointEquivalent']) * float(result['totalCredit'])
                    total_credits += float(result['totalCredit'])

                df = pd.DataFrame(table)
                with st.expander(f"{semester_name} (Click to Expand)"):
                    st.dataframe(df)

            if defense_cgpa:
                weighted_sum += defense_cgpa * 6.0
                total_credits += 6.0
                
            if total_credits > 0:
                total_cgpa = weighted_sum / total_credits
                st.success(f"🎉 Total CGPA: {total_cgpa:.2f}")
                st.toast(f"📢 CGPA calculated: {total_cgpa:.2f}", icon="✅")

            else:
                st.warning("CGPA could not be calculated due to missing credits.")

            st.markdown("### Options")
            pdf = create_pdf(student_info, semester_results, total_cgpa)
            st.download_button("Download Results as PDF", data=pdf, file_name=f"{student_id}_results.pdf", mime="application/pdf")

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("""
<p style='text-align: center;'>
    Created by Rifat | © 2024<br>
    Contact: <a href="mailto:rifatibnatozammal@gmail.com">rifatibnatozammal@gmail.com</a>
</p>
""", unsafe_allow_html=True)
