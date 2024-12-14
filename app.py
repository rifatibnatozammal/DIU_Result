import streamlit as st
import requests

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

# App layout
st.set_page_config(page_title="DIU Student Result Viewer", layout="centered", page_icon="📘")

# Header
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>Student Result Viewer</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center;'>Easily View Student Information and Academic Results</h4>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# Input Section
st.markdown("### Enter Student Information")
student_id = st.text_input("Student ID:", help="Provide a valid Student ID to fetch results.")

add_defense = st.checkbox("Add Defense CGPA?")
defense_cgpa = None
if add_defense:
    defense_cgpa = st.number_input(
        "Defense CGPA (Optional):",
        min_value=0.0, max_value=4.0, step=0.01,
        help="Optional CGPA for defense course."
    )

# Process and Display Results
if student_id:
    st.info(f"Fetching data for Student ID: **{student_id}**")

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

        st.markdown("<h3>📜 Academic Results</h3>", unsafe_allow_html=True)
        for semester in semesters:
            semester_id = semester['semesterId']
            semester_name = semester['semesterName']
            semester_year = semester['semesterYear']

            results = get_result_for_semester(student_id, semester_id)
            if results:
                with st.expander(f"{semester_name} {semester_year}"):
                    for result in results:
                        course_title = result['courseTitle']
                        course_code = result['customCourseId']
                        grade_letter = result['gradeLetter']
                        credits = float(result['totalCredit'])
                        cgpa = float(result['pointEquivalent'])

                        # Use columns for larger screens, fallback to stacked for mobile
                        col1, col2, col3 = st.columns([4, 2, 2])
                        col1.markdown(f"**{course_title} ({course_code})**")
                        col2.markdown(f"**Grade:** {grade_letter}")
                        col3.markdown(f"**CGPA:** {cgpa}")

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
        else:
            st.warning("No credits earned, CGPA cannot be calculated.")

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
