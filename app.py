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

# Function to generate a PDF
def generate_pdf(student_info, semesters, results_summary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add student info
    pdf.cell(200, 10, txt="Student Results", ln=True, align="C")
    pdf.cell(200, 10, txt="Student Information", ln=True, align="L")
    pdf.cell(200, 10, txt=f"Name: {student_info.get('studentName')}", ln=True)
    pdf.cell(200, 10, txt=f"ID: {student_info.get('studentId')}", ln=True)
    pdf.cell(200, 10, txt=f"Program: {student_info.get('programName')}", ln=True)
    pdf.cell(200, 10, txt=f"Department: {student_info.get('departmentName')}", ln=True)
    pdf.cell(200, 10, txt=f"Campus: {student_info.get('campusName')}", ln=True)
    pdf.ln(10)

    # Add semester results
    for semester in semesters:
        semester_name = semester['semesterName']
        semester_year = semester['semesterYear']
        pdf.cell(200, 10, txt=f"{semester_name} {semester_year}", ln=True, align="L")
        for result in results_summary[semester['semesterId']]:
            pdf.cell(200, 10, txt=f"Course: {result['courseTitle']} - Grade: {result['gradeLetter']} - CGPA: {result['pointEquivalent']}", ln=True)
        pdf.ln(5)

    # Add overall CGPA
    pdf.cell(200, 10, txt=f"Total CGPA: {results_summary['total_cgpa']:.2f}", ln=True, align="L")
    
    # Save to BytesIO
    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer

# App layout
st.set_page_config(page_title="Student Result Viewer", layout="wide", page_icon="📘")

# Header
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>Student Result Viewer</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>Easily View Student Information and Academic Results</h3>", unsafe_allow_html=True)

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
        results_summary = {}

        st.subheader("📜 Academic Results")
        for semester in semesters:
            semester_id = semester['semesterId']
            semester_name = semester['semesterName']
            semester_year = semester['semesterYear']

            results = get_result_for_semester(student_id, semester_id)
            if results:
                results_summary[semester_id] = results
                with st.expander(f"{semester_name} {semester_year} (Click to Expand)"):
                    for result in results:
                        course_title = result['courseTitle']
                        course_code = result['customCourseId']
                        grade_letter = result['gradeLetter']
                        credits = float(result['totalCredit'])
                        cgpa = float(result['pointEquivalent'])

                        col1, col2, col3, col4 = st.columns(4)
                        col1.write(f"**Course:** {course_title}")
                        col2.write(f"**Code:** {course_code}")
                        col3.write(f"**Grade:** {grade_letter}")
                        col4.write(f"**Credits:** {credits} / CGPA: {cgpa}")

                        weighted_cgpa_sum += cgpa * credits
                        total_credits += credits

        # Calculate total CGPA including defense
        if defense_cgpa:
            defense_credits = 6.0
            weighted_cgpa_sum += defense_cgpa * defense_credits
            total_credits += defense_credits

        # Display overall CGPA
        if total_credits > 0:
            total_cgpa = weighted_cgpa_sum / total_credits
            st.success(f"🎉 **Total CGPA Across All Semesters:** {total_cgpa:.2f}")
            results_summary['total_cgpa'] = total_cgpa

            # Generate PDF and provide download option
            pdf_buffer = generate_pdf(student_info, semesters, results_summary)
            st.download_button(
                label="📥 Download Results as PDF",
                data=pdf_buffer,
                file_name=f"{student_id}_results.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("No credits earned, CGPA cannot be calculated.")

        # Add a print button
        st.markdown(
            "<button onclick='window.print()'>🖨️ Print Results</button>",
            unsafe_allow_html=True
        )

else:
    st.warning("Please enter a Student ID to begin.")




# Footer
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("""
<p style='text-align: center;'>
    Created by Rifat | © 2024<br>
    Contact: <a href="mailto:rifatibnatozammal@gmail.com">rifatibnatozammal@gmail.com</a>
</p>
""", unsafe_allow_html=True)
