import streamlit as st
import requests
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd

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

    # Debugging: Print the response content
    st.write("API Response:", response.text)  # Use this to see the response in the app
    
    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            st.error("Error parsing JSON. Check API response.")
            return None
    else:
        st.error(f"Error fetching result for semester {semester_id}: {response.status_code}")
        return None


# Function to create a PDF
def create_pdf(student_info, semesters, total_cgpa):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Student Results")

    # Add header
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(30, 750, "Student Result Report")
    pdf.setFont("Helvetica", 12)

    # Add student information
    if student_info:
        pdf.drawString(30, 730, f"Name: {student_info.get('studentName')}")
        pdf.drawString(30, 710, f"Student ID: {student_info.get('studentId')}")
        pdf.drawString(30, 690, f"Program: {student_info.get('programName')}")
        pdf.drawString(30, 670, f"Department: {student_info.get('departmentName')}")
        pdf.drawString(30, 650, f"Campus: {student_info.get('campusName')}")

    # Add results
    y = 630
    pdf.drawString(30, y, "Semester Results:")
    pdf.setFont("Helvetica", 10)

    for semester_name, results in semesters.items():
        y -= 20
        pdf.drawString(30, y, f"{semester_name}:")
        for result in results:
            y -= 15
            pdf.drawString(50, y, f"{result['courseTitle']} ({result['customCourseId']}):")
            pdf.drawString(300, y, f"Grade: {result['gradeLetter']}, CGPA: {result['pointEquivalent']}")
            if y < 50:
                pdf.showPage()
                y = 750

    # Add CGPA
    y -= 30
    pdf.drawString(30, y, f"Total CGPA: {total_cgpa:.2f}")

    pdf.save()
    buffer.seek(0)
    return buffer

# App layout
st.set_page_config(page_title="Student Result Viewer", layout="centered", page_icon="📘")

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

# Process and Display Results
if student_id:
    st.info(f"Getting Results for Student ID: **{student_id}**")

    # Fetch and display student info
    student_info = get_student_info(student_id)
    if student_info:
        st.markdown("<h3>🎓 Student Information</h3>", unsafe_allow_html=True)
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

        st.markdown("<h3>📜 Academic Results</h3>", unsafe_allow_html=True)
        for semester in semesters:
            semester_id = semester['semesterId']
            semester_name = f"{semester['semesterName']} {semester['semesterYear']}"
            results = get_result_for_semester(student_id, semester_id)

            if results:
                semester_results[semester_name] = results

                # Prepare table data
                table_data = []
                for result in results:
                    table_data.append({
                        "Course Title": result['courseTitle'],
                        "Course Code": result['customCourseId'],
                        "Grade": result['gradeLetter'],
                        "Credits": float(result['totalCredit']),
                        "CGPA": float(result['pointEquivalent'])
                    })

                df = pd.DataFrame(table_data)

                # Display in expander as a table
                with st.expander(f"{semester_name} (Click to Expand)"):
                    st.dataframe(df)

                    # Calculate CGPA and Credits
                    for result in results:
                        weighted_cgpa_sum += float(result['pointEquivalent']) * float(result['totalCredit'])
                        total_credits += float(result['totalCredit'])

        # Add defense CGPA
        if defense_cgpa:
            defense_credits = 6.0
            weighted_cgpa_sum += defense_cgpa * defense_credits
            total_credits += defense_credits

        # Calculate and display total CGPA
        if total_credits > 0:
            total_cgpa = weighted_cgpa_sum / total_credits
            st.success(f"🎉 **Total CGPA Across All Semesters:** {total_cgpa:.2f}")
        else:
            st.warning("No credits earned, CGPA cannot be calculated.")

        # Add buttons for Print and PDF download
        st.markdown("### Options")
        st.button("Print Results", help="Use your browser's print option to print this page.")

        pdf_buffer = create_pdf(student_info, semester_results, total_cgpa)
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
