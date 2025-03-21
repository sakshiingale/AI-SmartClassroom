import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.document_loaders import PyPDFLoader
from langchain.chains import RetrievalQA
from pydantic import BaseModel, ValidationError
from typing import List
import json
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# Initialize MongoDB client
db_client = MongoClient(os.getenv("MONGO_URI"))
db = db_client["quiz-cluster"]

# Initialize LLM
llm = ChatOpenAI(model="gpt-4", api_key=os.getenv("OPENAI_API_KEY"))

# Embeddings
from langchain.embeddings.openai import OpenAIEmbeddings
embeddings = OpenAIEmbeddings()

# Streamlit App
def generate_quiz_page():
    st.title("Generate Quiz")
    st.write("Upload a document and generate quizzes based on its content.")

    # User Inputs
    test_id = st.text_input("Enter Test ID:")
    subject_name = st.text_input("Enter Subject Name:")
    num_questions = st.slider("Number of Questions", min_value=1, max_value=10, value=5)
    test_description = st.text_area("Describe the test:", "Enter a short description of the test.")
    difficulty = st.slider("Difficulty Level", min_value=1, max_value=3, value=2)
    quiz_file = st.file_uploader("Upload a document (PDF only):", type=["pdf"])

    if st.button("Generate Quiz"):

        if quiz_file:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(quiz_file.read())
                temp_file_path = temp_file.name

            try:
                # Load and split the document
                loader = PyPDFLoader(temp_file_path)
                docs = loader.load()

                if not docs:
                    st.error("Failed to extract content from the uploaded document. Please try another file.")
                    return

                # Chunking 
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                splits = text_splitter.split_documents(docs)

                # Vector Store - FAISS
                vector_store = FAISS.from_documents(splits, embeddings)
                retriever = vector_store.as_retriever()

                # Prompt
                prompt = f"""
You are a teacher and need to generate a quiz for your class based on the provided document.

The quiz should contain {num_questions} questions.

Each question should have 4 options, out of which only one is correct.

Format the output as a JSON object with the following structure:

{{
    "quiz_id": "{test_id}",
    "title": "",
    "desc": "{test_description}",
    "subject": "{subject_name}",
    
    "questions": [
        {{
            "question_id": 1,
            "question": "",
            "options": [
                {{"option_text": "", "is_correct": true}},
                {{"option_text": "", "is_correct": false}},
                {{"option_text": "", "is_correct": false}},
                {{"option_text": "", "is_correct": false}}
            ]
        }},
        ...
    ]
}}

Ensure the questions are relevant to the content of the uploaded document.
                """
                # Retrieval-based QA
                rag_chain = RetrievalQA.from_chain_type(
                    llm=llm,
                    chain_type="stuff",
                    retriever=retriever,
                )

                st.info("Generating quiz, please wait...")
                result = rag_chain.invoke(prompt)
                st.write(result)
                
                if result:
                    st.success("Quiz generated successfully!")
                    result_to_send = json.loads(result['result'].strip())

                    # Store quiz temporarily in session state
                    st.session_state['generated_quiz'] = result_to_send

                    # Display quiz preview
                    st.subheader("📜 Quiz Preview")
                    st.json(result_to_send)

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
        else:
            st.error("Please upload a document before generating a quiz.")

    # If a quiz is generated, show Post and Discard buttons
    if 'generated_quiz' in st.session_state:
        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Post Quiz"):
                result_to_send = st.session_state['generated_quiz']
                
                # Check if the subject name exists as a database
                if subject_name in db_client.list_database_names():
                    subject_db = db_client[subject_name]  # Access subject database
                    subject_db["quiz"].insert_one(result_to_send)  # Store in "quiz" collection
                    st.success(f"Quiz successfully stored in '{subject_name}' database under 'quiz' collection!")
                else:
                    st.warning("Subject name not found in the database. Quiz not stored.")

                # Clear session state after posting
                del st.session_state['generated_quiz']

        with col2:
            if st.button("❌ Discard Quiz"):
                del st.session_state['generated_quiz']
                st.warning("Quiz discarded!")

generate_quiz_page()