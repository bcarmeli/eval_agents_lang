import os
import streamlit as st
import pandas as pd
import ast
import uuid
from datetime import datetime
from PIL import Image
import random
import io
import smtplib
from email.message import EmailMessage
import urllib.parse

st.set_page_config(page_title="Referential Game Evaluation", layout="wide")

# Change these:
email = "boaz.carmeli@gmail.com"
subject = "Evaluation Results"
body = "Hi,\n\nPlease find attached the evaluation results.\n\nBest,\n[Your App Name]"

# Encode for mailto
mailto_link = f"mailto:{email}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"


# Get all experiment files
EXPERIMENT_FOLDER = "experiments"
experiment_files = sorted([f for f in os.listdir(EXPERIMENT_FOLDER) if f.endswith(".csv")])

# Load experiment data once
@st.cache_data
def load_experiment_data(csv_path):
    df = pd.read_csv(csv_path)
    df['candidate_paths'] = [path.replace("/Users/boazc/workarea/phd/country-flags/", "") for path in df['candidate_paths']]
    df["candidate_paths"] = df["candidate_paths"].apply(ast.literal_eval)
    return df

def parse_image_paths(candidate_paths_str):
    try:
        return ast.literal_eval(candidate_paths_str)
    except Exception as e:
        st.error(f"Error parsing image paths: {e}")
        return []

def shuffled_exp_trials(experiment):
    trials = []
    for turn_num, row in experiment.iterrows():
        images = row["candidate_paths"]
        gold_img = images[int(row["gold_index"]) - 1]  # 1-based to 0-based
        shuffled = images.copy()
        random.shuffle(shuffled)
        gold_shuffled_idx = shuffled.index(gold_img)
        trials.append({
            "turn_num": turn_num,
            "exp_num": row["exp_num"],
            "target": row["target"],
            "description": row["description"],
            "shuffled_paths": shuffled,
            "correct_index": gold_shuffled_idx
        })
    random.shuffle(trials)
    return trials[:10]

def init_experiment(csv_file_path):
    exp_info = {}
    csv_path = os.path.join(EXPERIMENT_FOLDER, csv_file_path)
    exp_info["experiment_df"] = load_experiment_data(csv_path)
    exp_info["shuffled_trials"] = shuffled_exp_trials(exp_info["experiment_df"])
    exp_info["responses"] = []
    exp_info["current_question"] = 0
    exp_info["done"] = False
    return exp_info

def send_email_with_results(to_email, csv_data):
    msg = EmailMessage()
    msg["Subject"] = "Study Results"
    msg["From"] = to_email
    msg["To"] = to_email
    msg.set_content("Attached are the study results from the app.")

    msg.add_attachment(csv_data, filename="study_results.csv", subtype="csv", maintype="text")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(to_email, APP_PASSWORD)
        smtp.send_message(msg)

# Session state for tracking completed experiments
if "completed_experiments" not in st.session_state:
    st.session_state.completed_experiments = set()

# Sidebar experiment selector
st.sidebar.title("🧪 Select Experiment")

# Session state for tracking completed experiments
if "loaded_experiments" not in st.session_state:
    all_experiments = {}
    # experiment_names = []
    for file in experiment_files:
        name = file.replace(".csv", "")
        label = f"✅ {name}" if name in st.session_state.completed_experiments else name
        all_experiments[name] = init_experiment(file)
    st.session_state.loaded_experiments = all_experiments

experiment_labels = []
for name in st.session_state.loaded_experiments:
    label = f"✅ {name}" if name in st.session_state.completed_experiments else name
    experiment_labels.append(label)

selected_label = st.sidebar.radio("Available Experiments", experiment_labels)
selected_experiment = selected_label.replace("✅ ", "")
experiment = st.session_state.loaded_experiments[selected_experiment] # all_experiments[selected_experiment]
# CSV_PATH = os.path.join(EXPERIMENT_FOLDER, f"{selected_experiment}.csv")
# 📝 Add instructions below the radio
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Instructions")
st.sidebar.markdown(
    """
    1. There are three experiments.
    2. There are 10 questions in each.
    3. For each turn, read the description.
    4. Select the image that best matches it.
    5. Once done with the experiment, download your results.
    **Note - results are saved locally. Please make sure you know to find them**.
    6. Move to the next experiment using the buttons on the left sidebar.
    **Note - you may need to click the radio button twice.**
    7. Collect the three results files and e-mail them to me (boazc@il.ibm.com)
    """
)
if "active_experiment_name" not in st.session_state:
    st.session_state.active_experiment_name = None # 
    
# Detect experiment change and reset session state
if st.session_state.active_experiment_name != selected_experiment:
# if st.session_state.active_experiment_name != selected_experiment:
    # save before switching:
    if st.session_state.active_experiment_name is not None:
        prev_exp_name = st.session_state.active_experiment_name
        st.session_state.loaded_experiments[prev_exp_name].update(
            {
                "current_question": st.session_state.current_question,
                "responses": st.session_state.responses,
                "done": st.session_state.done if not st.session_state.loaded_experiments[prev_exp_name]["done"] else True
                # "shuffled_trials": st.session_state.shuffled_trials,
            }
        )
    # st.session_state.active_experiment_name = selected_experiment
    # st.rerun()  # <- F

# if "active_experiment_name" not in st.session_state or st.session_state.active_experiment_name != selected_experiment:
    st.session_state.active_experiment_name = selected_experiment
    st.session_state.active_experiment = experiment
    st.session_state.current_question = experiment["current_question"]
    st.session_state.responses = experiment["responses"]
    st.session_state.done = experiment["done"]
    st.session_state.shuffled_trials = experiment["shuffled_trials"]


# --- App Setup ---
st.title("🧠 Image Description Matching Task")

# --- Session State Init ---
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
    st.session_state.start_time = str(datetime.now())

# # --- Early Exit ---
# if st.button("🚪 Quit and Save Results"):
#     df = pd.DataFrame(st.session_state.responses)
#     st.download_button("📥 Download your responses", df.to_csv(index=False), "responses.csv")
#     st.stop()

# --- Main Loop ---
if st.session_state.current_question < len(st.session_state.shuffled_trials):
    trial = st.session_state.shuffled_trials[st.session_state.current_question]
    turn_num = trial["turn_num"]
    exp_num = trial["exp_num"]
    target =trial["target"]
    description = trial["description"]
    image_paths = trial["shuffled_paths"]
    correct_index = trial["correct_index"]

    st.markdown(f"### Question {st.session_state.current_question + 1}")
    st.markdown(f"**Description:** {description}")

    cols = st.columns(len(image_paths))
    selected_index = None

    for i, (col, img_path) in enumerate(zip(cols, image_paths)):
        if col.button("Select", key=f"select_{i}"):
            selected_index = i
        col.image(img_path, use_container_width=True, caption=f"Image {i+1}")


    if selected_index is not None:
        st.session_state.responses.append({
            "user_id": st.session_state.user_id,
            "question": st.session_state.current_question + 1,
            "turn_num": turn_num,
            "exp_num": exp_num,
            "target": target,
            "description": description,
            "correct_index": correct_index,
            "selected_index": selected_index,
            "correct": selected_index == correct_index,
            "timestamp": str(datetime.utcnow())
        })
        st.session_state.current_question += 1
        st.rerun()
elif st.session_state.done or st.session_state.current_question >= len(st.session_state.shuffled_trials):
    st.session_state.completed_experiments.add(selected_experiment)
    st.session_state.loaded_experiments[selected_experiment]["done"] = True
    
    correct_answers = sum(r["correct"] for r in st.session_state.responses)
    st.markdown(f"**Your score:** {correct_answers} / {len(st.session_state.responses)}")
    df = pd.DataFrame(st.session_state.responses)
    

    # 📝 Automatically save to server
    output_dir = "results"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/{selected_experiment}_{st.session_state.user_id}_{timestamp}.csv"
    df.to_csv(filename, index=False)

    st.download_button("📥 Download your responses", df.to_csv(index=False), f"{selected_experiment}_{st.session_state.user_id}_{timestamp}.csv")

    all_experiments_names = list(st.session_state.loaded_experiments.keys())
    remaining = [1 for e in list(st.session_state.loaded_experiments.values()) if not e["done"]]
    if remaining:
        st.warning("Please download your responses before moving to the next step.")
        st.markdown("**🧪 Next step:** Select another experiment from the sidebar on the left ⬅️ to continue.")
    else:
        st.warning("Please do not forget to download your last responses using the above button.")
        st.markdown("Please collect all three files and send them to me (boazc@il.ibm.com)")
        st.success(f"🎉 Thank you for completing the evaluation of all studies!")
    
        # results_df = pd.DataFrame(st.session_state.responses)
        # csv_buffer = io.StringIO()
        # results_df.to_csv(csv_buffer, index=False)
        # csv_bytes = csv_buffer.getvalue().encode("utf-8")
        # # Provide download first
        # st.download_button(
        #     label="📥 Download Results",
        #     data=csv_bytes,  # Assuming you have your CSV data as bytes
        #     file_name="study_results.csv",
        #     mime="text/csv"
        # )

        # # Mailto button
        # st.markdown(f"""
        # <a href="{mailto_link}">
        #     <button style="margin-top: 10px;">📧 Open Mail App</button>
        # </a>
        # """, unsafe_allow_html=True)

        # # Convert session responses to CSV
        # if "responses" in st.session_state and st.session_state.responses:
        #     results_df = pd.DataFrame(st.session_state.responses)
        #     csv_buffer = io.StringIO()
        #     results_df.to_csv(csv_buffer, index=False)
        #     csv_bytes = csv_buffer.getvalue().encode("utf-8")

        #     # Display download and email button
        #     if st.button("📤 Download & Email Results"):
        #         # Email the results
        #         try:
        #             send_email_with_results(YOUR_EMAIL, csv_bytes)
        #             st.success("✅ Results emailed successfully!")
        #         except Exception as e:
        #             st.error(f"❌ Failed to send email: {e}")

        #         # Trigger file download using st.download_button workaround
        #         st.download_button(
        #             label="Click here to download manually if needed",
        #             data=csv_bytes,
        #             file_name="study_results.csv",
        #             mime="text/csv"
        #         )

    
else:
    st.warning("Unexpected state.")
