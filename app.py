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
        st.session_state.scores = {}  # { "model/ver/audio_name": score }
    if 'page' not in st.session_state:
        st.session_state.page = 'name_input'

# ----------------------------
# HELPERS
# ----------------------------
def ensure_dirs():
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)

@st.cache_data
def load_csv_metadata():
    """Load CSV metadata into dataframe."""
    if not os.path.exists(CSV_INPUT):
        st.error(f"Missing {CSV_INPUT}")
        return pd.DataFrame()
    
    df = pd.read_csv(CSV_INPUT)
    required_cols = {"audio_name", "transcriptions", "model_ver", "model_name"}
    if not required_cols.issubset(df.columns):
        st.error(f"{CSV_INPUT} must contain columns: {required_cols}")
        return pd.DataFrame()
    
    return df

def submit_name():
    """Set user name and go to evaluation page."""
    if st.session_state.temp_user_name:
        st.session_state.user_name = st.session_state.temp_user_name
        st.session_state.page = 'evaluation'
    else:
        st.warning("Please enter your name to start.")

def log_score(model, version, audio_name, transcription, score):
    """Log a single score, overwriting previous score for same user/model/version/audio."""
    ensure_dirs()
    if not st.session_state.user_name:
        st.warning("User name not set. Cannot save logs.")
        return

    # Prepare new entry
    timestamp = datetime.datetime.now().isoformat()
    new_entry = pd.DataFrame([{
        'user_name': st.session_state.user_name,
        'model_name': model,
        'model_ver': version,
        'audio_file': audio_name,
        'transcriptions': transcription,
        'score': score,
        'timestamp': timestamp
    }])

    # Load existing log if exists
    if os.path.exists(LOG_FILE):
        df_log = pd.read_csv(LOG_FILE)
        # Remove any existing row with the same user/model/version/audio
        df_log = df_log[
            ~(
                (df_log['user_name'] == st.session_state.user_name) &
                (df_log['model_name'] == model) &
                (df_log['model_ver'] == version) &
                (df_log['audio_file'] == audio_name)
            )
        ]
        # Append new entry
        df_log = pd.concat([df_log, new_entry], ignore_index=True)
    else:
        df_log = new_entry

    # Save back to CSV
    df_log.to_csv(LOG_FILE, index=False)
    st.success(f"Score saved for {audio_name} ({model}/{version})!")

# ----------------------------
# SIDEBAR: Score Criteria
# ----------------------------
def show_sidebar_criteria():
    st.sidebar.title("📊 Rating Criteria")
    criteria = [
        ("0–9", "Not speech", "Just noise or broken sound. Nothing understandable."),
        ("10–19", "Very hard to hear", "Almost nothing is clear. May have serious errors or missing words."),
        ("20–29", "Very bad", "Some parts are understandable, but many word errors. Unnatural or emotionless voice."),
        ("30–39", "Bad", "A lot of words are wrong or mispronounced. Sounds robotic or awkward."),
        ("40–49", "Not natural", "Most words are correct, but the voice is very flat or unnatural. Hard to enjoy."),
        ("50–59", "Clear but robotic", "All words are right, but voice is flat, with no emotion. Feels like a computer."),
        ("60–69", "Mostly accurate, some prosody", "All/most words correct, and there's a bit of pitch/emotion. Still sounds artificial."),
        ("70–79", "Natural feel with minor issues", "Sounds mostly human. Has emotion and rhythm. May have 1 small word mistake."),
        ("80–89", "Very natural", "Fluent, expressive, natural. Almost no errors."),
        ("90–99", "Extremely natural", "Feels just like a human speaker. No word errors, natural tone and flow."),
        ("100", "Perfect", "Perfect emotion, rhythm, clarity. Indistinguishable from a real person.")
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
    show_sidebar_criteria()  # always visible

    metadata_df = load_csv_metadata()
    if metadata_df.empty:
        st.stop()

    # ----------------------------
    # PAGE: NAME INPUT
    # ----------------------------
    if st.session_state.page == 'name_input':
        st.title("TTS Evaluation App")
        st.write("Please enter your name to begin audio evaluation.")
        st.text_input("Your Name:", key='temp_user_name', on_change=submit_name)
        st.button("Start Evaluation", on_click=submit_name)

    # ----------------------------
    # PAGE: EVALUATION
    # ----------------------------
    elif st.session_state.page == 'evaluation':
        if not st.session_state.user_name:
            st.error("User name not set. Please go back and enter your name.")
            st.button("Go back", on_click=lambda: st.session_state.update(page='name_input'))
            return

        st.title(f"Hello, {st.session_state.user_name}! 🎧")
        st.markdown("---")

        # --- Model selection ---
        models = metadata_df['model_name'].unique().tolist()
        chosen_model = st.selectbox("Select Model:", models)

        chosen_ver = None
        if chosen_model:
            versions = metadata_df[metadata_df['model_name'] == chosen_model]['model_ver'].unique().tolist()
            chosen_ver = st.selectbox("Select Version:", versions)

        chosen_audio_name = None
        if chosen_model and chosen_ver:
            audios_list = metadata_df[
                (metadata_df['model_name'] == chosen_model) &
                (metadata_df['model_ver'] == chosen_ver)
            ]['audio_name'].tolist()
            chosen_audio_name = st.selectbox("Select Audio:", audios_list)

        # --- Show audio + transcription + scoring ---
        if chosen_model and chosen_ver and chosen_audio_name:
            audio_path = os.path.join(AUDIO_DIR, chosen_model, chosen_ver, chosen_audio_name)

            if os.path.exists(audio_path):
                st.audio(audio_path, format='audio/wav')

                transcription = metadata_df.loc[
                    (metadata_df['model_name'] == chosen_model) &
                    (metadata_df['model_ver'] == chosen_ver) &
                    (metadata_df['audio_name'] == chosen_audio_name),
                    'transcriptions'
                ].values[0]
                st.markdown(f"**Transcript:** {transcription}")

                # --- Score input as slider ---
                # Use a unique key for each audio
                score_key = f"{chosen_model}_{chosen_ver}_{chosen_audio_name}"

                # Initialize in session_state if not exists
                if score_key not in st.session_state:
                    st.session_state[score_key] = 0 

                # Slider widget
                score = st.slider(
                    "Enter Score (0–100):",
                    min_value=0,
                    max_value=100,
                    step=1,
                    key=score_key
                )

                # Optional caption
                if st.session_state[score_key] == 0:
                    st.caption("Slide to assign a score.")

                # Update logging dict
                st.session_state.scores[f"{chosen_model}/{chosen_ver}/{chosen_audio_name}"] = st.session_state[score_key]

                if st.button("💾 Save Score"):
                    log_score(chosen_model, chosen_ver, chosen_audio_name, transcription, score)
            else:
                st.warning(f"Audio file not found: {audio_path}")

        st.markdown("---")
        st.info("Scores are logged in 'app_output/single_eval_log.csv'. Only entered scores are saved.")

# ----------------------------
# RUN
# ----------------------------
if __name__ == "__main__":
    main()
