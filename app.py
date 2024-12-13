import streamlit as st
import requests
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

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

# Function to generate PDF
def generate_pdf(student_info, results, total_cgpa):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, height - 72, "Student Result Viewer")
    c.line(72, height - 75, width - 72, height - 75)

    # Student Info
    y_position = height - 100
    c.setFont("Helvetica", 12)
    c.drawString(72, y_position, f"Name: {student_info.get('studentName')}")
    c.drawString(72, y_position - 15, f"ID: {student_info.get('studentId')}")
    c.drawString(72, y_position - 30, f"Program: {student_info.get('programName')}")
    c.drawString(72, y_position - 45, f"Department: {student_info.get('departmentName')}")
    c.drawString(72, y_position - 60, f"Campus: {student_info.get('campusName')}")

    # Academic Results
    y_position -= 100
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, y_position, "Academic Results:")
    y_position -= 20
    c.setFont("Helvetica", 12)
    for semester, courses in results.items():
        c.drawString(72, y_position, f"{semester}:")
        y_position -= 15
        for course in courses:
            c.drawString(90, y_position, f"{course['courseTitle']} ({course['customCourseId']}) - Grade: {course['gradeLetter']}, CGPA: {course['pointEquivalent']}")
            y_position -= 15
            if y_position < 72:  # Check for page overflow
                c.showPage()
                y_position = height - 72

    # Total CGPA
    y_position -= 20
    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, y_position, f"Total CGPA: {total_cgpa:.2f}")

    # Save PDF
    c.save()
    buffer.seek(0)
    return buffer

# App layout
st.set_page_config(page_title="Student Result Viewer", layout="centered", page_icon="📘")

# Header
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>Student Result Viewer</h1>", unsafe_allow_html=True)

# Input Section
student_id = st.text_input("Enter Student ID:", help="Provide a valid Student ID to fetch results.")
add_defense = st.checkbox("Add Defense CGPA?")
defense_cgpa = None
if add_defense:
    defense_cgpa = st.number_input("Defense CGPA (Optional):", min_value=0.0, max_value=4.0, step=0.01)

# Process and Display Results
if student_id:
    st.info(f"Fetching data for Student ID: **{student_id}**")

    # Fetch and display student info
    student_info = get_student_info(student_id)
    if student_info:
        st.markdown("### 🎓 Student Information")
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

        st.markdown("### 📜 Academic Results")
        for semester in semesters:
            semester_id = semester['semesterId']
            semester_name = semester['semesterName']
            semester_year = semester['semesterYear']

            results = get_result_for_semester(student_id, semester_id)
            if results:
                semester_title = f"{semester_name} {semester_year}"
                semester_results[semester_title] = results
                with st.expander(f"{semester_title}"):
                    for result in results:
                        st.write(f"{result['courseTitle']} ({result['customCourseId']}) - Grade: {result['gradeLetter']}, CGPA: {result['pointEquivalent']}")
                        weighted_cgpa_sum += float(result['pointEquivalent']) * float(result['totalCredit'])
                        total_credits += float(result['totalCredit'])

        # Include defense CGPA
        if defense_cgpa:
            defense_credits = 6.0
            weighted_cgpa_sum += defense_cgpa * defense_credits
            total_credits += defense_credits

        # Calculate total CGPA
        total_cgpa = weighted_cgpa_sum / total_credits if total_credits > 0 else 0.0
        st.success(f"### 🎉 Total CGPA: {total_cgpa:.2f}")

        # Print and Download Options
        st.markdown("---")
        st.markdown("### 📄 Save or Print Results")
        col1, col2 = st.columns(2)
        with col1:
            # Print Button
            st.markdown('<button onclick="window.print()">Print Results</button>', unsafe_allow_html=True)
        with col2:
            # Download PDF
            pdf_buffer = generate_pdf(student_info, semester_results, total_cgpa)
            st.download_button(
                label="Download PDF",
                data=pdf_buffer,
                file_name=f"{student_info.get('studentId')}_results.pdf",
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
