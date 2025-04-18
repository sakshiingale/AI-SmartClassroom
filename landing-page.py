import streamlit as st

# Page config
st.set_page_config(page_title="AI-Smart Classroom", layout="wide")

# Title and Description with dark mode styles
st.markdown("""
    <style>
        body {
            background-color: #121212;
        }
        .title {
            text-align: center;
            font-size: 48px;
            font-weight: bold;
            color: #00B4D8;
            margin-top: 30px;
        }
        .subtitle {
            text-align: center;
            font-size: 22px;
            color: #ccc;
            margin-bottom: 3rem;
        }
        .role-box {
            border-radius: 20px;
            padding: 30px;
            background-color: #1e1e1e;
            box-shadow: 0 0 15px rgba(0, 180, 216, 0.2);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            text-align: center;
        }
        .role-box:hover {
            transform: scale(1.03);
            box-shadow: 0 0 25px rgba(0, 180, 216, 0.4);
        }
        .btn {
            background-color: #00B4D8;
            color: white !important;
            font-weight: bold;
            padding: 12px 28px;
            font-size: 16px;
            border: none;
            border-radius: 10px;
            margin-top: 20px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            box-shadow: 0px 4px 10px rgba(0, 180, 216, 0.3);
            transition: background 0.3s ease, transform 0.2s ease;
        }
        .btn:hover {
            background-color: #0077B6;
            transform: translateY(-2px);
            box-shadow: 0px 6px 14px rgba(0, 180, 216, 0.4);
        }
        h3 {
            color: #fff;
        }
        p {
            color: #ccc;
        }
    </style>

    <div class="title">AI- Smart Classroom</div>
    <div class="subtitle">Select your role to continue</div>
""", unsafe_allow_html=True)

# URLs
teacher_url = "https://ai-smartclassroom-teacher.streamlit.app/"
student_url = "https://ai-smartclassroom-student.streamlit.app/"

# Layout
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
        <div class="role-box">
            <img src="https://img.icons8.com/ios-filled/100/00B4D8/teacher.png" width="80"/>
            <h3>👩‍🏫 I'm a Teacher</h3>
            <p>Create and manage quizzes using GPT-4 and LangChain.</p>
            <a href="{teacher_url}" target="_blank" class="btn">Go to Teacher Portal</a>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class="role-box">
            <img src="https://img.icons8.com/ios-filled/100/00B4D8/student-center.png" width="80"/>
            <h3>🎓 I'm a Student</h3>
            <p>Attempt quizzes and track your performance in real-time.</p>
            <a href="{student_url}" target="_blank" class="btn">Go to Student Portal</a>
        </div>
    """, unsafe_allow_html=True)
