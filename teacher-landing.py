import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import re  # To sanitize database names
from streamlit_option_menu import option_menu

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

# Sidebar Navigation
with st.sidebar:
    selected = option_menu(
        menu_title="Teacher Dashboard",
        options=["🏠 Home", "🔑 Login", "📝 Quiz Generation", "📊 Visualization"],
        icons=["house", "person", "clipboard-check", "bar-chart"],
        menu_icon="cast",
        default_index=0,
    )

# Login & Signup Page
if selected == "🔑 Login":
    st.title("👩‍🎓 Teacher Login & Signup")
    option = st.radio("Select an option", ("Login", "Sign Up"))

    if option == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            teacher = teachers_collection.find_one({"username": username, "password": password})
            if teacher:
                st.session_state.logged_in = True
                st.session_state.teacher_name = teacher["full_name"]
                st.success("Login successful! Redirecting to Home...")
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

# Home Page - Teacher Dashboard
if selected == "🏠 Home" and st.session_state.logged_in:
    teacher_name = st.session_state.teacher_name
    st.title("👩‍🎓 Teacher Dashboard")
    st.write(f"Welcome, {teacher_name}!")

    # Fetch courses created by the logged-in teacher
    created_courses = [
        {"course_name": course["course_name"], "course_id": course["course_id"]}
        for course in courses_collection.find({"creator_name": teacher_name})
    ]

    # Display created courses with buttons
    st.subheader("Your Created Courses")
    for course in created_courses:
        if st.button(course['course_name']):
            st.session_state.selected_course_id = course['course_id']
            st.session_state.selected_course_name = course['course_name']
            st.success(f"Selected course: {course['course_name']}")

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
                sanitized_db_name = re.sub(r"[^a-zA-Z0-9_]", "_", new_course_name.lower())
                course_data = {
                    "course_id": new_course_id,
                    "course_name": new_course_name,
                    "creator_name": creator_name,
                    "db_name": sanitized_db_name
                }
                courses_collection.insert_one(course_data)

                # Create a new database for the course
                course_db = client[sanitized_db_name]
                course_db.create_collection("quiz")
                course_db.create_collection("test_scores")

                st.success(f"Successfully created the course: {new_course_name}!")
                st.rerun()
        else:
            st.error("Please fill in all the fields to create a new course.")

    # Logout Button
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# Handle users who are not logged in and try to access Home
if selected == "🏠 Home" and not st.session_state.logged_in:
    st.warning("Please log in first!")