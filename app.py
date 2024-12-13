import streamlit as st
import requests
from io import BytesIO
from fpdf import FPDF

# Base URL for API
BASE_URL = 'http://software.diu.edu.bd:8006'

# Functions to fetch data from the API
def get_student_info(student_id):
    url = f"{BASE_URL}/result/studentInfo"
    params = {'studentId': student_id}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching student info: {response.status_code}")
        return None

def get_semester_list():
    url = f"{BASE_URL}/result/semesterList"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching semester list: {response.status_code}")
        return None

def get_result_for_semester(student_id, semester_id):
    url = f"{BASE_URL}/result"
    params = {'studentId': student_id, 'semesterId': semester_id, 'grecaptcha': ''}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error fetching result for semester {semester_id}: {response.status_code}")
        return None

# Function to create a PDF
def create_pdf(student_info, results, total_cgpa):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Student Info
    pdf.set_font("Arial", "B", size=14)
    pdf.cell(200, 10, txt="Student Result Report", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", size=12)
    if student_info:
        pdf.cell(200, 10, txt=f"Name: {student_info.get('studentName')}", ln=True)
        pdf.cell(200, 10, txt=f"ID: {student_info.get('studentId')}", ln=True)
        pdf.cell(200, 10, txt=f"Program: {student_info.get('programName')}", ln=True)
        pdf.cell(200, 10, txt=f"Department: {student_info.get('departmentName')}", ln=True)
        pdf.cell(200, 10, txt=f"Campus: {student_info.get('campusName')}", ln=True)

    pdf.ln(10)

    # Semester Results
    pdf.set_font("Arial", "B", size=12)
    pdf.cell(200, 10, txt="Academic Results:", ln=True)
    pdf.set_font("Arial", size=12)

    for semester_name, semester_results in results.items():
        pdf.cell(200, 10, txt=f"{semester_name}:", ln=True)
        for result in semester_results:
            pdf.cell(200, 10, txt=f"  - {result['courseTitle']} ({result['customCourseId']}): {result['gradeLetter']} (Credits: {result['totalCredit']}, CGPA: {result['pointEquivalent']})", ln=True)

    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Total CGPA: {total_cgpa:.2f}", ln=True)
    return pdf

# App layout
st.set_page_config(page_title="Student Result Viewer", layout="wide", page_icon="📘")

# Header
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>Student Result Viewer</h1>", unsafe_allow_html=True)

# Input Section
st.markdown("### Input Student Information")
student_id = st.text_input("Enter Student ID:", help="Provide a valid Student ID to fetch results.")

add_defense = st.checkbox("Add Defense CGPA?")
defense_cgpa = None
if add_defense:
    defense_cgpa = st.number_input(
        "Enter Defense CGPA (Optional):",
        min_value=0.0, max_value=4.0, step=0.01,
        help="Optional CGPA for defense course."
    )

# Display Results if Student ID is provided
if student_id:
    st.info(f"Fetching data for Student ID: **{student_id}**")

    # Fetch and display student info
    student_info = get_student_info(student_id)
    if student_info:
        st.subheader("🎓 Student Information")
        st.markdown(f"""
        - **Name:** {student_info.get('studentName')}
        - **ID:** {student_info.get('studentId')}
        - **Program:** {student_info.get('programName')}
        - **Department:** {student_info.get('departmentName')}
        - **Campus:** {student_info.get('campusName')}
        """)

    # Fetch and display semester results
    semesters = get_semester_list()
    if semesters:
        total_credits = 0
        weighted_cgpa_sum = 0
        semester_results = {}

        st.subheader("📜 Academic Results")
        for semester in semesters:
            semester_id = semester['semesterId']
            semester_name = f"{semester['semesterName']} {semester['semesterYear']}"
            results = get_result_for_semester(student_id, semester_id)

            if results:
                semester_results[semester_name] = results
                with st.expander(f"{semester_name} (Click to Expand)"):
                    for result in results:
                        course_title = result['courseTitle']
                        course_code = result['customCourseId']
                        grade_letter = result['gradeLetter']
                        credits = float(result['totalCredit'])
                        cgpa = float(result['pointEquivalent'])

                        st.write(f"**{course_title} ({course_code})**")
                        st.write(f"- Grade: {grade_letter}")
                        st.write(f"- Credits: {credits}")
                        st.write(f"- CGPA: {cgpa}")

                        weighted_cgpa_sum += cgpa * credits
                        total_credits += credits

        # Calculate total CGPA including defense
        if defense_cgpa:
            defense_credits = 6.0
            weighted_cgpa_sum += defense_cgpa * defense_credits
            total_credits += defense_credits

        if total_credits > 0:
            total_cgpa = weighted_cgpa_sum / total_credits
            st.success(f"🎉 **Total CGPA Across All Semesters:** {total_cgpa:.2f}")
        else:
            st.warning("No credits earned, CGPA cannot be calculated.")

        # Add buttons for Print and PDF download
        st.markdown("### Options")
        if st.button("Print Results"):
            st.write("To print, use your browser's print functionality (Ctrl+P or Command+P).")

        pdf = create_pdf(student_info, semester_results, total_cgpa)
        pdf_buffer = BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)

        st.download_button(
            label="Download Results as PDF",
            data=pdf_buffer,
            file_name=f"student_{student_id}_results.pdf",
            mime="application/pdf",
        )




# Footer
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("""
<p style='text-align: center;'>
    Created by Rifat | © 2024<br>
    Contact: <a href="mailto:rifatibnatozammal@gmail.com">rifatibnatozammal@gmail.com</a>
</p>
""", unsafe_allow_html=True)
