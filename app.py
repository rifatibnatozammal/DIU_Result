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

# Streamlit app layout
st.title("Student Result Viewer")
st.write("Enter the Student ID below to fetch their information and results.")

# Input for Student ID
student_id = st.text_input("Student ID:")

if student_id:
    # Fetch and display student info
    student_info = get_student_info(student_id)
    if student_info:
        st.subheader("Student Information")
        st.write(f"**Name:** {student_info.get('studentName')}")
        st.write(f"**ID:** {student_info.get('studentId')}")
        st.write(f"**Program:** {student_info.get('programName')}")
        st.write(f"**Department:** {student_info.get('departmentName')}")
        st.write(f"**Campus:** {student_info.get('campusName')}")

    # Fetch and display semester results
    semesters = get_semester_list()
    if semesters:
        total_credits = 0
        weighted_cgpa_sum = 0

        for semester in semesters:
            semester_id = semester['semesterId']
            semester_name = semester['semesterName']
            semester_year = semester['semesterYear']

            results = get_result_for_semester(student_id, semester_id)
            if results:
                st.subheader(f"{semester_name} {semester_year}")
                for result in results:
                    st.write(f"- **Course:** {result['courseTitle']} ({result['customCourseId']})")
                    st.write(f"  **Grade:** {result['gradeLetter']}, **Credits:** {result['totalCredit']}, **CGPA:** {result['pointEquivalent']}")
                    weighted_cgpa_sum += float(result['pointEquivalent']) * float(result['totalCredit'])
                    total_credits += float(result['totalCredit'])

        # Option to add defense result
        defense_cgpa = st.number_input("Enter CGPA of defense (optional)", min_value=0.0, max_value=4.0, step=0.01)
        if defense_cgpa > 0:
            defense_credits = 6.0
            weighted_cgpa_sum += defense_cgpa * defense_credits
            total_credits += defense_credits

        # Calculate and display total CGPA
        if total_credits > 0:
            total_cgpa = weighted_cgpa_sum / total_credits
            st.success(f"**Total CGPA:** {total_cgpa:.2f}")
        else:
            st.warning("No credits earned, CGPA cannot be calculated.")
