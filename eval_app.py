import streamlit as st
import pandas as pd
import ast
import uuid
from datetime import datetime
from PIL import Image
import random

# Constants
CSV_PATH = "your_experiment_data.csv"  # Replace with your actual CSV path
NUM_QUESTIONS = 1  # Just one for now, showing the first experiment

# Load experiments CSV and parse image paths
@st.cache_data
def load_experiment_data(path):
    df = pd.read_csv(path)
    df['candidate_paths'] = df['candidate_paths'].apply(ast.literal_eval)
    return df

df = load_experiment_data(CSV_PATH)

# Initialize session state
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
    st.session_state.responses = []
    st.session_state.current_question = 0
    st.session_state.start_time = datetime.utcnow()

# --- Survey Flow ---
st.title("🧠 Image Description Matching Task")

if st.session_state.current_question < NUM_QUESTIONS:
    q_idx = st.session_state.current_question
    row = df.iloc[q_idx]

    description = row["description"]
    images = row["candidate_paths"]
    gold_index = row["gold_index"]

    st.markdown(f"**Question {q_idx + 1} of {NUM_QUESTIONS}**")
    st.markdown(f"**Description:** {description}")

    # Show image choices
    st.image(images, width=150, caption=[f"Image {i+1}" for i in range(len(images))])
    choice = st.radio("Which image matches the description?", [f"Image {i+1}" for i in range(len(images))])
    selected_idx = int(choice.split()[-1]) - 1

    if st.button("Submit"):
        st.session_state.responses.append({
            "user_id": st.session_state.user_id,
            "question": q_idx + 1,
            "correct_index": gold_index,
            "selected_index": selected_idx,
            "correct": selected_idx == gold_index,
            "timestamp": str(datetime.utcnow())
        })
        st.session_state.current_question += 1
        st.experimental_rerun()
else:
    st.success("🎉 Thank you for completing the study!")

    # Summary
    correct_answers = sum([r["correct"] for r in st.session_state.responses])
    st.markdown(f"**Your score:** {correct_answers} / {NUM_QUESTIONS}")

    # Download results
    df_out = pd.DataFrame(st.session_state.responses)
    st.download_button("📥 Download your responses", df_out.to_csv(index=False), "responses.csv")
