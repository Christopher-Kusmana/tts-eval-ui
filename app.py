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
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    if 'scores' not in st.session_state:
        st.session_state.scores = {}
    if 'page' not in st.session_state:
        st.session_state.page = 'name_input'

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

def submit_name():
    if st.session_state.temp_user_name:
        st.session_state.user_name = st.session_state.temp_user_name
        st.session_state.page = 'evaluation'
    else:
        st.warning("Please enter your name to start.")

# ----------------------------
# LOGGING FUNCTION (UPDATED)
# ----------------------------
def log_score(model_col, audio_name, transcription, score):
    ensure_dirs()
    if not st.session_state.user_name:
        st.warning("User name not set. Cannot save logs.")
        return

    timestamp = datetime.datetime.now().isoformat()

    new_entry = pd.DataFrame([{
        'user_name': st.session_state.user_name,
        'model': model_col,
        'audio_file': audio_name,
        'transcriptions': transcription,
        'score': score,
        'timestamp': timestamp
    }])

    # Load existing log if exists
    if os.path.exists(LOG_FILE):
        df_log = pd.read_csv(LOG_FILE)
        # Remove any existing entry for this combination (to overwrite)
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
    df = pd.DataFrame(criteria, columns=["Score Range", "Rating Label", "Description"])
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

    # PAGE: NAME INPUT
    if st.session_state.page == 'name_input':
        st.title("TTS Evaluation App")
        st.text_input("Your Name:", key='temp_user_name', on_change=submit_name)
        st.button("Start Evaluation", on_click=submit_name)

    # PAGE: EVALUATION
    elif st.session_state.page == 'evaluation':
        st.title(f"Hello, {st.session_state.user_name}! 🎧")
        st.markdown("---")

        model_cols = [c for c in df.columns if c != 'transcriptions']
        chosen_model_col = st.selectbox("Select Model:", model_cols)

        valid_rows = []
        for idx, row in df.iterrows():
            audio_file_name = row[chosen_model_col]
            if isinstance(audio_file_name, str) and audio_file_name.strip():
                audio_path = os.path.join(AUDIO_DIR, chosen_model_col, audio_file_name)
                if os.path.exists(audio_path):
                    valid_rows.append((idx, row['transcriptions'], audio_file_name))

        if not valid_rows:
            st.warning(f"No audio files found for model: {chosen_model_col}")
            st.stop()

        row_display = [f"{i} - {t}" for i, t, _ in valid_rows]
        row_idx_choice = st.selectbox(
            "Select Audio by Transcript:",
            list(range(len(valid_rows))),
            format_func=lambda x: row_display[x]
        )

        row_idx, transcription, audio_file_name = valid_rows[row_idx_choice]
        audio_path = os.path.join(AUDIO_DIR, chosen_model_col, audio_file_name)

        st.audio(audio_path, format='audio/wav')
        st.markdown(f"**Transcript:** {transcription}")

        score_key = f"{chosen_model_col}_{audio_file_name}"
        if score_key not in st.session_state:
            st.session_state[score_key] = 0

        score = st.slider(
            "Enter Score (0–100):",
            min_value=0,
            max_value=100,
            step=1,
            key=score_key
        )

        st.session_state.scores[f"{chosen_model_col}/{audio_file_name}"] = score

        if st.button("💾 Save Score"):
            log_score(chosen_model_col, audio_file_name, transcription, score)

if __name__ == "__main__":
    main()
