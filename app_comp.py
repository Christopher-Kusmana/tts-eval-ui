import streamlit as st
import pandas as pd
import os
import random

# --- File paths ---
INPUT_CSV_PATH = 'app_input/csv/list.csv'
OUTPUT_CSV_PATH = 'app_output/comp_eval_log.csv'
AUDIO_DIR = 'app_input/audios'

# --- Session State Initialization ---
for key, default in {
    'user_name': '',
    'df': None,
    'current_phase': 0,  # 0=select model/version/audio, 1=phase1, 2=phase2
    'selected_model': None,
    'baseline_ver': None,
    'experimental_ver': None,
    'baseline_audio': None,
    'experimental_audio': None,
    'baseline_score': None,
    'new_score': None,
    'transcription': ''
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- Helper Functions ---
def load_data():
    if st.session_state.df is None:
        try:
            st.session_state.df = pd.read_csv(INPUT_CSV_PATH)
        except Exception as e:
            st.error(f"Error loading CSV: {e}")
            st.stop()

def show_rating_criteria_sidebar():
    criteria = [
        ("0–9", "Not speech", "Just noise or broken sound."),
        ("10–19", "Very hard to hear", "Almost nothing understandable."),
        ("20–29", "Very bad", "Many word errors, unnatural."),
        ("30–39", "Bad", "Robotic or awkward."),
        ("40–49", "Not natural", "Flat voice, unnatural."),
        ("50–59", "Clear but robotic", "All words correct, flat voice."),
        ("60–69", "Mostly accurate, some prosody", "Mostly correct words, slight emotion."),
        ("70–79", "Natural feel with minor issues", "Mostly human, 1 small mistake."),
        ("80–89", "Very natural", "Fluent, expressive, almost no errors."),
        ("90–99", "Extremely natural", "Feels human, no word errors."),
        ("100", "Perfect", "Perfect emotion, rhythm, clarity.")
    ]
    df = pd.DataFrame(criteria, columns=["Score Range", "Label", "Description"])
    st.sidebar.markdown("### 📊 Rating Criteria")
    st.sidebar.markdown(df.to_html(index=False), unsafe_allow_html=True)

def display_audio(model, version, audio_file):
    path = os.path.join(AUDIO_DIR, model, version, audio_file)
    if os.path.exists(path):
        st.audio(path, width=100)
    else:
        st.error(f"Audio not found: {path}")

def append_to_log(log_entry):
    """Overwrite existing log entry for the same user/model/audio pair."""
    df_log = pd.DataFrame([log_entry])
    os.makedirs(os.path.dirname(OUTPUT_CSV_PATH), exist_ok=True)

    if os.path.exists(OUTPUT_CSV_PATH):
        existing_df = pd.read_csv(OUTPUT_CSV_PATH)
        # Filter out any previous entry for this combination
        mask = ~(
            (existing_df['user_name'] == log_entry['user_name']) &
            (existing_df['model_name'] == log_entry['model_name']) &
            (existing_df['baseline_audio_name'] == log_entry['baseline_audio_name']) &
            (existing_df['experimental_audio_name'] == log_entry['experimental_audio_name'])
        )
        existing_df = existing_df[mask]
        # Append new log entry
        df_to_save = pd.concat([existing_df, df_log], ignore_index=True)
        df_to_save.to_csv(OUTPUT_CSV_PATH, index=False)
    else:
        df_log.to_csv(OUTPUT_CSV_PATH, index=False)


# --- Phase 0: Select Model, Versions, and Audio ---
def select_model_versions_audio():
    st.header("Step 1: Select Model, Versions, and Audio Pair")
    load_data()
    models = st.session_state.df['model_name'].unique()
    st.session_state.selected_model = st.selectbox("Choose model:", models)

    model_df = st.session_state.df[st.session_state.df['model_name'] == st.session_state.selected_model]
    versions = model_df['model_ver'].unique()

    st.session_state.baseline_ver = st.selectbox("Choose baseline version:", versions)

    # Prevent the same version for experimental
    experimental_versions = [v for v in versions if v != st.session_state.baseline_ver]
    if not experimental_versions:
        st.error("No other versions available for experimental selection.")
        return

    st.session_state.experimental_ver = st.selectbox("Choose experimental version:", experimental_versions)

    # Get audio lists for both versions
    baseline_df = model_df[model_df['model_ver'] == st.session_state.baseline_ver]
    experimental_df = model_df[model_df['model_ver'] == st.session_state.experimental_ver]

    # Only show experimental audio transcriptions for selection
    exp_options = list(experimental_df['transcriptions'])
    st.session_state.transcription = st.selectbox("Choose transcription (baseline and experimental must match):", exp_options)

    # Find the exact experimental audio
    exp_row = experimental_df[experimental_df['transcriptions'] == st.session_state.transcription].iloc[0]
    st.session_state.experimental_audio = exp_row['audio_name']

    # Find baseline audio with same transcription if exists
    matching_baseline_df = baseline_df[baseline_df['transcriptions'] == st.session_state.transcription]
    if not matching_baseline_df.empty:
        st.session_state.baseline_audio = matching_baseline_df.iloc[0]['audio_name']
    else:
        st.warning("No matching baseline audio found for this transcription. Select manually:")
        st.session_state.baseline_audio = st.selectbox("Baseline audio:", list(baseline_df['audio_name']))

    if st.button("Confirm Selection"):
        st.session_state.current_phase = 1
        st.rerun()

# --- Phase 1: Rate Experimental Audio ---
def phase_1():
    st.header("Phase 1: Rate Experimental Audio")
    st.markdown(f"**Transcription:** {st.session_state.transcription}")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Baseline Audio")
        display_audio(st.session_state.selected_model, st.session_state.baseline_ver, st.session_state.baseline_audio)
    with col2:
        st.subheader("Experimental Audio")
        display_audio(st.session_state.selected_model, st.session_state.experimental_ver, st.session_state.experimental_audio)

        # Always create the slider and store its value in session_state
    st.session_state.baseline_score = st.slider(
        "Enter baseline score (0-100):",
        min_value=0,
        max_value=100,
        value=st.session_state.baseline_score if st.session_state.baseline_score is not None else 50,
        key="baseline_slider"
    )

    st.session_state.new_score = st.slider("Rate experimental audio (0-100):", 0, 100, 50, key="new_score_slider")

    if st.button("Submit Scores"):
        st.session_state.current_phase = 2
        st.rerun()

# --- Phase 2: Preference Test ---
def phase_2():
    st.header("Phase 2: Preference Test")
    pair = [
        ('baseline', st.session_state.baseline_ver, st.session_state.baseline_audio),
        ('experimental', st.session_state.experimental_ver, st.session_state.experimental_audio)
    ]
    random.shuffle(pair)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Audio 1")
        display_audio(st.session_state.selected_model, pair[0][1], pair[0][2])
    with col2:
        st.subheader("Audio 2")
        display_audio(st.session_state.selected_model, pair[1][1], pair[1][2])

    preference = st.radio("Which audio do you prefer?", ("Audio 1", "Audio 2"))

    if st.button("Submit Preference"):
        preferred_label = 'experimental' if (
            (preference == "Audio 2" and pair[1][0] == 'experimental') or
            (preference == "Audio 1" and pair[0][0] == 'experimental')
        ) else 'baseline'

        consistent = preferred_label == 'experimental'

        log_entry = {
            'user_name': st.session_state.user_name,
            'model_name': st.session_state.selected_model,
            'baseline_model_ver': st.session_state.baseline_ver,
            'experimental_model_ver': st.session_state.experimental_ver,
            'baseline_audio_name': st.session_state.baseline_audio,
            'experimental_audio_name': st.session_state.experimental_audio,
            'baseline_score': st.session_state.baseline_score,
            'new_score': st.session_state.new_score,
            'preferred': preferred_label,
            'consistent': consistent
        }

        append_to_log(log_entry)

        st.success("Evaluation logged! ✅")
        st.session_state.current_phase = 0
        st.session_state.baseline_audio = None
        st.session_state.experimental_audio = None
        st.session_state.baseline_score = None
        st.session_state.new_score = None
        st.session_state.transcription = ''
        st.rerun()

# --- Main App ---
def main():
    st.title("TTS Model Comparison App 🗣️")
    show_rating_criteria_sidebar()

    if not st.session_state.user_name:
        st.session_state.user_name = st.text_input("Enter your name:")
        if st.session_state.user_name:
            st.success(f"Hello, {st.session_state.user_name}!")
            load_data()
            st.rerun()
        else:
            return

    load_data()
    st.markdown("---")

    if st.session_state.current_phase == 0:
        select_model_versions_audio()
    elif st.session_state.current_phase == 1:
        phase_1()
    elif st.session_state.current_phase == 2:
        phase_2()

if __name__ == "__main__":
    main()
