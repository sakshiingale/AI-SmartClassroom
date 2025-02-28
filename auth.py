import streamlit as st
import bcrypt
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# MongoDB connection details
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "quiz-db"
STUDENT_COLLECTION = "student_meta"
TEACHER_COLLECTION = "teacher_meta"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
student_collection = db[STUDENT_COLLECTION]
teacher_collection = db[TEACHER_COLLECTION]

# Fetch user data from the appropriate collection
def get_user_by_username_and_role(username, role):
    if role == "Teacher":
        user = teacher_collection.find_one({"username": username})
    elif role == "Student":
        user = student_collection.find_one({"username": username})
    else:
        user = None
    return user

# Function to check password
def check_password(stored_password_hash, entered_password):
    return bcrypt.checkpw(entered_password.encode('utf-8'), stored_password_hash)

# Streamlit login page
st.title("Login Page")

# User login form
role = st.selectbox("Select Role", ["Teacher", "Student"], key="login_role")
username = st.text_input("Username", key="login_username")
password = st.text_input("Password", type="password", key="login_password")

# Handle login action
if st.button("Login", key="login_button"):
    if username and password and role:
        user = get_user_by_username_and_role(username, role)
        if user:
            # Check if password is correct
            stored_password_hash = user["password"]
            if check_password(stored_password_hash, password):
                st.success(f"Welcome {role} {username}!")
                if role == "Student":
                    # Store student_id in session state for use in the student-landing page
                    st.session_state.student_id = username
                    
            else:
                st.error("Invalid username or password.")
        else:
            st.error("User not found.")
    else:
        st.warning("Please enter your role, username, and password.")
