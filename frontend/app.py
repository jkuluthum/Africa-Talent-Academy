import streamlit as st
import pandas as pd
import requests
from io import StringIO, BytesIO

API_URL = "http://localhost:8000"

st.title("📊 Grade Calculator App")

st.write("""
You can either upload a CSV file or enter student grades manually.

**CSV requirements:** Columns: student_name, coursework, test, final (scores out of 100).
""")

input_method = st.radio("Choose input method:", ["Upload CSV", "Manual Input"])

# We'll store the last processed CSV here for download
if "processed_csv" not in st.session_state:
    st.session_state.processed_csv = None

def send_csv_to_backend(csv_data):
    files = {"file": ("grades.csv", csv_data, "text/csv")}
    with st.spinner("Calculating grades..."):
        response = requests.post(f"{API_URL}/upload-grades/", files=files)
    if response.status_code == 200:
        data = response.json()
        if "error" in data:
            st.error(data["error"])
            st.session_state.processed_csv = None
        else:
            results = data.get("results", [])
            if results:
                st.success("Grades calculated successfully!")
                result_df = pd.DataFrame(results)
                st.dataframe(result_df)
                # Save CSV bytes for download
                st.session_state.processed_csv = csv_data
            else:
                st.warning("No results returned.")
                st.session_state.processed_csv = None
    else:
        st.error(f"Error from server: {response.status_code}")
        st.session_state.processed_csv = None

if input_method == "Upload CSV":
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write("Preview of uploaded CSV:")
        st.dataframe(df)

        if st.button("Calculate Grades"):
            csv_buffer = StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)
            send_csv_to_backend(csv_buffer.getvalue())

else:  # Manual Input
    st.write("Enter student details and grades below:")

    if "students" not in st.session_state:
        st.session_state.students = []

    with st.form("grade_form", clear_on_submit=True):
        student_name = st.text_input("Student Name")
        coursework = st.number_input("coursework Score (0-100)", min_value=0, max_value=100, step=1)
        test = st.number_input("test Score (0-100)", min_value=0, max_value=100, step=1)
        final = st.number_input("Final Score (0-100)", min_value=0, max_value=100, step=1)
        submitted = st.form_submit_button("Add Student")

        if submitted:
            if student_name.strip() == "":
                st.error("Please enter a student name.")
            else:
                st.session_state.students.append({
                    "student_name": student_name,
                    "coursework": coursework,
                    "test": test,
                    "final": final
                })
                st.success(f"Added {student_name}")

    if st.session_state.students:
        st.write("Students added:")
        st.dataframe(pd.DataFrame(st.session_state.students))

        if st.button("Calculate Grades for All"):
            manual_df = pd.DataFrame(st.session_state.students)
            csv_buffer = StringIO()
            manual_df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)
            send_csv_to_backend(csv_buffer.getvalue())

# Show download button if processed CSV is available
if st.session_state.processed_csv is not None:
    st.download_button(
        label="📥 Download Grades CSV",
        data=st.session_state.processed_csv,
        file_name="final_grades.csv",
        mime="text/csv"
    )
