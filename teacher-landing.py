import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import re  # To sanitize database names

# Load environment variables
load_dotenv()

# MongoDB connection
CONNECTION_STRING = os.getenv("MONGO_URI")
if not CONNECTION_STRING:
    st.error("MongoDB connection string not found. Please set it in the .env file.")
    st.stop()

client = MongoClient(CONNECTION_STRING)
quiz_db = client["quiz-db"]
teachers_collection = quiz_db["teacher_meta"]
courses_collection = quiz_db["courses"]

# Session state for login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.teacher_name = ""

# Login Page
st.title("👩‍🎓 Teacher Login & Signup")
st.sidebar.title("Navigation")
option = st.sidebar.radio("Select an option", ("Login", "Sign Up"))

if option == "Login":
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        teacher = teachers_collection.find_one({"username": username, "password": password})
        if teacher:
            st.session_state.logged_in = True
            st.session_state.teacher_name = teacher["full_name"]
            st.rerun()
        else:
            st.error("Invalid credentials. Please try again.")

elif option == "Sign Up":
    full_name = st.text_input("Full Name")
    username = st.text_input("Choose a Username")
    password = st.text_input("Choose a Password", type="password")
    
    if st.button("Sign Up"):
        if teachers_collection.find_one({"username": username}):
            st.warning("Username already exists! Choose a different one.")
        else:
            teachers_collection.insert_one({"username": username, "password": password, "full_name": full_name})
            st.success("Sign-up successful! Please log in.")

# Dashboard Page
if st.session_state.logged_in:
    teacher_name = st.session_state.teacher_name
    st.title("👩‍🎓 Teacher Dashboard")
    st.write(f"Welcome, {teacher_name}!")

    # Fetch courses created by the logged-in teacher
    created_courses = [
        {
            "course_name": course["course_name"]
        }
        for course in courses_collection.find({"creator_name": teacher_name})
    ]

    # Apply custom CSS
    st.markdown("""
    <style>
        .flex-container {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            justify-content: center;
            margin-top: 16px;
        }
        .flex-item {
            background-color: #E3F2FD;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            flex: 1 1 calc(30% - 40px);
        }
        .flex-item:hover {
            background-color: #BBDEFB;
            cursor: pointer;
        }
    </style>
    """, unsafe_allow_html=True)

    st.subheader("Your Created Courses")
    st.markdown('<div class="flex-container">', unsafe_allow_html=True)
    for course in created_courses:
        st.markdown(
            f'<div class="flex-item"><h4>{course["course_name"]}</h4></div>',
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # Input fields to create a new course
    st.subheader("Create a New Course")
    new_course_name = st.text_input("Enter the course name")
    new_course_id = st.text_input("Enter the course ID (unique)")
    creator_name = teacher_name

    if st.button("Create Course"):
        if new_course_name and new_course_id:
            if courses_collection.find_one({"course_id": new_course_id}):
                st.warning(f"A course with ID '{new_course_id}' already exists.")
            else:
                # Sanitize course name to create a valid MongoDB database name
                sanitized_db_name = re.sub(r"[^a-zA-Z0-9_]", "_", new_course_name.lower())
                
                # Create course entry in main database
                course_data = {
                    "course_id": new_course_id,
                    "course_name": new_course_name,
                    "creator_name": creator_name,
                    "db_name": sanitized_db_name  # Store the database name for reference
                }
                courses_collection.insert_one(course_data)

                # Create a new database for the course
                course_db = client[sanitized_db_name]
                course_db.create_collection("quiz")
                course_db.create_collection("test_scores")

                st.success(f"Successfully created the course: {new_course_name}!")
                st.success(f"Database '{sanitized_db_name}' and collections created successfully.")
                st.rerun()
        else:
            st.error("Please fill in all the fields to create a new course.")

    st.write("---")
    st.write("Thank you for using the Teacher Portal!")

    # Logout button
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()