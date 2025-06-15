import streamlit as st
import random
import uuid
from datetime import datetime
import pandas as pd
import ast

# --- Setup ---
NUM_QUESTIONS = 10
NUM_IMAGES = 10

def load_experiment_data(csv_path):
    # Load CSV into a DataFrame
    df = pd.read_csv(csv_path)

    # Convert the stringified list of image paths to actual lists
    df['candidate_paths'] = df['candidate_paths'].apply(ast.literal_eval)

    return df

def get_images_for_experiment(df, experiment_index):
    """
    Returns a list of image file paths for a specific experiment.
    """
    return df.loc[experiment_index, 'candidate_paths']

# Simulated data
def load_images():
    # Replace with actual image URLs or file paths
    return [f"https://via.placeholder.com/150?text=Image+{i+1}" for i in range(NUM_IMAGES)]

def get_description(correct_index):
    return f"This is a description for image {correct_index + 1}"

# Initialize session state
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
    st.session_state.responses = []
    st.session_state.current_question = 0
    st.session_state.start_time = datetime.utcnow()

# images = load_images()

# --- Survey Flow ---
st.title("🧠 Image Description Matching Task")

if st.session_state.current_question < NUM_QUESTIONS:
    q_idx = st.session_state.current_question
    correct_idx = random.randint(0, NUM_IMAGES - 1)
    description = get_description(correct_idx)

    st.markdown(f"**Question {q_idx + 1} of {NUM_QUESTIONS}**")
    st.markdown(f"**Description:** {description}")

    # Show images
    choice = st.radio("Which image matches the description?", [f"Image {i+1}" for i in range(NUM_IMAGES)])
    selected_idx = int(choice.split()[-1]) - 1

    if st.button("Submit"):
        st.session_state.responses.append({
            "user_id": st.session_state.user_id,
            "question": q_idx + 1,
            "correct_index": correct_idx,
            "selected_index": selected_idx,
            "correct": selected_idx == correct_idx,
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
    import pandas as pd
    df = pd.DataFrame(st.session_state.responses)
    st.download_button("📥 Download your responses", df.to_csv(index=False), "responses.csv")
