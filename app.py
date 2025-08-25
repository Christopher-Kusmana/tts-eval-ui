import streamlit as st
import pandas as pd
import os
import datetime

# ----------------------------
# CONFIG
# ----------------------------
CSV_INPUT = "app_input/csv/list.csv"
LOG_DIR = 'app_output'
LOG_FILE = os.path.join(LOG_DIR, 'single_eval_log.csv')
AUDIO_DIR = 'app_input/audios'  # Root folder for all models

# ----------------------------
# SESSION STATE INITIALIZATION
# ----------------------------
def initialize_session_state():
    defaults = {
        'user_name': None,
        'temp_user_name': '',
        'page': 'name_input',
        'chosen_model': None,
        'current_index': 0,
        'valid_rows': [],
        'scores': {}
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def ensure_dirs():
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)

@st.cache_data
def load_csv_metadata():
    if not os.path.exists(CSV_INPUT):
        st.error(f"Missing {CSV_INPUT}")
        return pd.DataFrame()
    df = pd.read_csv(CSV_INPUT)
    if 'transcriptions' not in df.columns:
        st.error(f"{CSV_INPUT} must contain column: transcriptions")
        return pd.DataFrame()
    return df

# ----------------------------
# NAME SUBMISSION
# ----------------------------
def submit_name():
    if st.session_state.temp_user_name.strip():
        st.session_state.user_name = st.session_state.temp_user_name.strip()
        st.session_state.page = 'model_select'
    else:
        st.warning("Please enter your name to start.")

# ----------------------------
# LOGGING FUNCTION
# ----------------------------
def log_score(model_col, audio_name, transcription, score):
    ensure_dirs()
    timestamp = datetime.datetime.now().isoformat()
    new_entry = pd.DataFrame([{
        'user_name': st.session_state.user_name,
        'model': model_col,
        'audio_file': audio_name,
        'transcriptions': transcription,
        'score': score,
        'timestamp': timestamp
    }])

    if os.path.exists(LOG_FILE):
        df_log = pd.read_csv(LOG_FILE)
        # Remove existing entry to overwrite
        df_log = df_log[
            ~(
                (df_log['user_name'] == st.session_state.user_name) &
                (df_log['model'] == model_col) &
                (df_log['audio_file'] == audio_name)
            )
        ]
        df_log = pd.concat([df_log, new_entry], ignore_index=True)
    else:
        df_log = new_entry

    df_log.to_csv(LOG_FILE, index=False)
    st.success(f"Score saved for {audio_name} ({model_col})!")

# ----------------------------
# SIDEBAR CRITERIA
# ----------------------------
def show_sidebar_criteria():
    st.sidebar.title("📊 Rating Criteria")
    criteria = [
        ("0–9", "Not speech", "Just noise or broken sound."),
        ("10–19", "Very hard to hear", "Almost nothing is clear."),
        ("20–29", "Very bad", "Many word errors."),
        ("30–39", "Bad", "Robotic or awkward."),
        ("40–49", "Not natural", "Flat or unnatural."),
        ("50–59", "Clear but robotic", "No emotion."),
        ("60–69", "Mostly accurate", "Some pitch/emotion."),
        ("70–79", "Natural feel", "Minor issues."),
        ("80–89", "Very natural", "Almost no errors."),
        ("90–99", "Extremely natural", "Feels human."),
        ("100", "Perfect", "Indistinguishable from real.")
    ]
    df = pd.DataFrame(criteria, columns=["Score Range", "Label", "Description"])
    st.sidebar.markdown(df.to_html(index=False), unsafe_allow_html=True)

# ----------------------------
# MAIN APP
# ----------------------------
def main():
    st.set_page_config(page_title="TTS Evaluation", layout="centered")
    initialize_session_state()
    ensure_dirs()
    show_sidebar_criteria()

    df = load_csv_metadata()
    if df.empty:
        st.stop()

    # ---------------- NAME INPUT PAGE ----------------
    if st.session_state.page == 'name_input':
        st.title("TTS Evaluation App")
        st.text_input("Your Name:", key='temp_user_name', on_change=submit_name)

    # ---------------- MODEL SELECT PAGE ----------------
    elif st.session_state.page == 'model_select':
        st.title(f"Welcome {st.session_state.user_name}!")
        model_cols = [c for c in df.columns if c != 'transcriptions']
        st.session_state.chosen_model = st.selectbox("Select Model to Evaluate:", model_cols)
        if st.session_state.chosen_model:
            # Prepare valid rows for iteration
            st.session_state.valid_rows = [
                (idx, row['transcriptions'], row[st.session_state.chosen_model])
                for idx, row in df.iterrows()
                if isinstance(row[st.session_state.chosen_model], str) and row[st.session_state.chosen_model].strip() and
                os.path.exists(os.path.join(AUDIO_DIR, st.session_state.chosen_model, row[st.session_state.chosen_model]))
            ]
            st.session_state.current_index = 0
            if st.button("Start Evaluating"):
                st.session_state.page = 'evaluation'
                st.rerun()

    # ---------------- EVALUATION PAGE ----------------
    elif st.session_state.page == 'evaluation':
        chosen_model_col = st.session_state.chosen_model
        current_idx = st.session_state.current_index
        total = len(st.session_state.valid_rows)

        # Finished evaluating all samples
        if current_idx >= total:
            st.success(f"Finished all samples for model: {chosen_model_col} 🎉")
            st.session_state.page = 'model_select'
            st.rerun()

        row_idx, transcription, audio_file_name = st.session_state.valid_rows[current_idx]
        audio_path = os.path.join(AUDIO_DIR, chosen_model_col, audio_file_name)

        st.title(f"Sample {current_idx + 1} of {total} - Model: {chosen_model_col}")
        st.audio(audio_path, format='audio/wav')
        st.markdown(f"**Transcript:** {transcription}")

        score_key = f"{chosen_model_col}_{audio_file_name}"
        if score_key not in st.session_state:
            st.session_state[score_key] = 0  # default slider

        score = st.slider(
            "Enter Score (0–100):",
            min_value=0,
            max_value=100,
            step=1,
            key=score_key
        )

        if st.button("💾 Save & Next"):
            log_score(chosen_model_col, audio_file_name, transcription, score)
            st.session_state.current_index += 1
            st.rerun()

if __name__ == "__main__":
    main()
