import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import re  # To sanitize database names
from streamlit_option_menu import option_menu
import tempfile
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.document_loaders import PyPDFLoader
from langchain.chains import RetrievalQA
from langchain.embeddings.openai import OpenAIEmbeddings
import json
import pandas as pd
import matplotlib.pyplot as plt

# Load .env variables
load_dotenv()

# MongoDB & OpenAI setup
MONGO_URI = os.getenv("MONGO_URI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not MONGO_URI:
    st.error("MongoDB connection string not found. Please set MONGO_URI in the .env file.")
    st.stop()

if not OPENAI_API_KEY:
    st.error("OpenAI API key not found. Please set OPENAI_API_KEY in the .env file.")
    st.stop()

client = MongoClient(MONGO_URI)
quiz_db = client["quiz-db"]
teachers_collection = quiz_db["teacher_meta"]
courses_collection = quiz_db["courses"]

# Session State
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.teacher_name = ""

# Sidebar
with st.sidebar:
    selected = option_menu(
        menu_title="Teacher Dashboard",
        options=["🔑 Login", "🏠 Home", "📝 Quiz Generation", "📊 Visualization"],
        icons=["person", "house", "clipboard-check", "bar-chart"],
        menu_icon="cast",
        default_index=0,
    )

# Login/Signup
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
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials.")

    elif option == "Sign Up":
        full_name = st.text_input("Full Name")
        username = st.text_input("Choose a Username")
        password = st.text_input("Choose a Password", type="password")
        if st.button("Sign Up"):
            if teachers_collection.find_one({"username": username}):
                st.warning("Username already exists!")
            else:
                teachers_collection.insert_one({
                    "username": username,
                    "password": password,
                    "full_name": full_name
                })
                st.success("Sign-up successful! Please log in.")

# Home
if selected == "🏠 Home":
    if not st.session_state.logged_in:
        st.warning("Please log in first!")
        st.stop()

    teacher_name = st.session_state.teacher_name
    st.title("👩‍🎓 Teacher Dashboard")
    st.write(f"Welcome, {teacher_name}!")

    created_courses = list(courses_collection.find({"creator_name": teacher_name}))
    st.subheader("📚 Your Created Courses")

    if created_courses:
        for i, course in enumerate(created_courses):
            if st.button(course['course_name'], key=f"course_{i}"):
                st.session_state.selected_course_id = course['course_id']
                st.session_state.selected_course_name = course['course_name']
                st.success(f"Selected course: {course['course_name']}")
    else:
        st.info("You haven't created any courses yet.")

    st.subheader("➕ Create a New Course")
    new_course_name = st.text_input("Enter Course Name")
    new_course_id = st.text_input("Enter Unique Course ID")

    if st.button("Create Course", key="create_course_button"):
        if new_course_name and new_course_id:
            if courses_collection.find_one({"course_id": new_course_id}):
                st.warning("Course ID already exists.")
            else:
                sanitized_db_name = re.sub(r"[^a-zA-Z0-9_]", "_", new_course_name.lower())
                course_data = {
                    "course_id": new_course_id,
                    "course_name": new_course_name,
                    "creator_name": teacher_name,
                    "db_name": sanitized_db_name
                }
                courses_collection.insert_one(course_data)
                course_db = client[sanitized_db_name]
                course_db.create_collection("quiz")
                course_db.create_collection("test_scores")
                course_db.create_collection("enroll_stud")
                st.success(f"🎉 Course '{new_course_name}' created successfully!")
                st.rerun()
        else:
            st.error("Please enter both the Course Name and ID.")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# Quiz Generation
if selected == "📝 Quiz Generation":
    if not st.session_state.logged_in:
        st.warning("Please log in first!")
        st.stop()

    teacher_name = st.session_state.teacher_name
    created_courses = list(courses_collection.find({"creator_name": teacher_name}))

    if created_courses:
        course_options = {c['course_name']: c for c in created_courses}
        selected_course_name = st.selectbox("Select Course", list(course_options.keys()))
        selected_course = course_options[selected_course_name]
        db_name = selected_course["db_name"]
        course_id = selected_course["course_id"]
    else:
        st.warning("No courses found. Please create a course first.")
        st.stop()

    llm = ChatOpenAI(model="gpt-4", api_key=OPENAI_API_KEY)
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

    if "retriever" not in st.session_state:
        st.session_state.retriever = None

    def generate_quiz(prompt, retriever):
        if retriever is None:
            st.error("Retriever not initialized.")
            return None
        rag_chain = RetrievalQA.from_chain_type(
            llm=llm, chain_type="stuff", retriever=retriever)
        return rag_chain.invoke(prompt)

    st.title("📝 Generate Quiz")
    st.write(f"Creating quiz for course: {selected_course_name}")

    quiz_id = st.text_input("Enter Test ID")
    num_questions = st.slider("Number of Questions", 1, 10, 5)
    test_description = st.text_area("Test Description", "Short description of the test.")
    difficulty = st.slider("Difficulty Level", 1, 3, 2)
    quiz_file = st.file_uploader("Upload a PDF", type=["pdf"])

    if st.button("Generate Quiz"):
        if not quiz_file:
            st.error("Please upload a document.")
            st.stop()

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(quiz_file.read())
            path = temp_file.name

        try:
            loader = PyPDFLoader(path)
            docs = loader.load()
            if not docs:
                st.error("Could not extract content from document.")
                st.stop()

            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = splitter.split_documents(docs)
            vector_store = FAISS.from_documents(splits, embeddings)
            st.session_state.retriever = vector_store.as_retriever()

            prompt = f"""
You are a teacher and need to generate a quiz for your class based on the provided document.

The quiz should contain {num_questions} questions.

Each question should have 4 options, out of which only one is correct.

Format the output as a JSON object with the following structure:

{{
    "quiz_id": "{quiz_id}",
    "title": "",
    "desc": "{test_description}",
    "subject": "{selected_course_name}",
    "course_id": "{course_id}",
    "questions": [
        {{
            "question_id": 1,
            "question": "",
            "options": [
                {{"option_text": "", "is_correct": false}},
                {{"option_text": "", "is_correct": false}},
                {{"option_text": "", "is_correct": false}},
                {{"option_text": "", "is_correct": true}}
            ]
        }},
        ...
    ]
}}
Ensure the questions are relevant to the document.
"""
            st.info("Generating quiz...")
            result = generate_quiz(prompt, st.session_state.retriever)

            if result:
                st.success("Quiz generated!")
                quiz_data = json.loads(result["result"].strip())
                st.session_state.generated_quiz = quiz_data
                st.subheader("📜 Quiz Preview")
                st.json(quiz_data)

        except Exception as e:
            st.error(f"An error occurred: {e}")

    if "generated_quiz" in st.session_state:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Post Quiz"):
                db = client[db_name]
                db["quiz"].insert_one(st.session_state.generated_quiz)
                st.success("Quiz posted successfully.")
                del st.session_state.generated_quiz
        with col2:
            if st.button("❌ Discard Quiz"):
                del st.session_state.generated_quiz
                st.warning("Quiz discarded.")
