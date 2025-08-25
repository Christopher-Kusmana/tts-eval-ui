import streamlit as st
import pandas as pd
import os
import random
import datetime

# --- Paths ---
INPUT_CSV_PATH = 'app_input/csv/list.csv'
OUTPUT_CSV_PATH = 'app_output/comp_eval_log.csv'
AUDIO_DIR = 'app_input/audios'

# --- Session State Initialization ---
default_state = {
    'user_name': '',
    'df': None,
    'phase': 0,  # 0=select baseline/experimental, 1=rate, 2=preference
    'baseline_col': None,
    'experimental_col': None,
    'selected_row': None,
    'baseline_score': None,
    'experimental_score': None
}
for key, value in default_state.items():
    if key not in st.session_state:
        st.session_state[key] = value


# --- Helpers ---
@st.cache_data
def load_data():
    if not os.path.exists(INPUT_CSV_PATH):
        st.error(f"Missing {INPUT_CSV_PATH}")
        return pd.DataFrame()
    df = pd.read_csv(INPUT_CSV_PATH)
    if 'transcriptions' not in df.columns:
        st.error(f"{INPUT_CSV_PATH} must have a 'transcriptions' column")
        return pd.DataFrame()
    return df


def show_rating_criteria_sidebar():
    criteria = [
        ("0–9", "Not speech", "Just noise or broken sound."),
        ("10–19", "Very hard to hear", "Almost nothing understandable."),
        ("20–29", "Very bad", "Many word errors, unnatural."),
        ("30–39", "Bad", "Robotic or awkward."),
        ("40–49", "Not natural", "Flat voice, unnatural."),
        ("50–59", "Clear but robotic", "All words correct, flat voice."),
        ("60–69", "Mostly accurate", "Some pitch/emotion."),
        ("70–79", "Natural feel", "Minor issues."),
        ("80–89", "Very natural", "Almost no errors."),
        ("90–99", "Extremely natural", "Feels human."),
        ("100", "Perfect", "Indistinguishable from real.")
    ]
    df = pd.DataFrame(criteria, columns=["Score Range", "Label", "Description"])
    st.sidebar.markdown("### 📊 Rating Criteria")
    st.sidebar.markdown(df.to_html(index=False), unsafe_allow_html=True)


def audio_path(model_col, audio_file):
    return os.path.join(AUDIO_DIR, model_col, audio_file)


def play_audio(model_col, audio_file):
    path = audio_path(model_col, audio_file)
    if os.path.exists(path):
        st.audio(path)
    else:
        st.error(f"Missing file: {path}")


def save_log(entry):
    os.makedirs(os.path.dirname(OUTPUT_CSV_PATH), exist_ok=True)
    df_log = pd.DataFrame([entry])
    if os.path.exists(OUTPUT_CSV_PATH):
        old_df = pd.read_csv(OUTPUT_CSV_PATH)
        mask = ~(
            (old_df['user_name'] == entry['user_name']) &
            (old_df['baseline_model'] == entry['baseline_model']) &
            (old_df['experimental_model'] == entry['experimental_model']) &
            (old_df['baseline_audio_name'] == entry['baseline_audio_name']) &
            (old_df['experimental_audio_name'] == entry['experimental_audio_name'])
        )
        old_df = old_df[mask]
        df_log = pd.concat([old_df, df_log], ignore_index=True)
    df_log.to_csv(OUTPUT_CSV_PATH, index=False)



# --- Phase 0: Selection ---
def phase_0(df):
    st.header("Step 1: Select Baseline and Experimental Models")
    model_cols = [c for c in df.columns if c != 'transcriptions']

    st.session_state.baseline_col = st.selectbox("Select Baseline Model:", model_cols)
    exp_options = [m for m in model_cols if m != st.session_state.baseline_col]
    st.session_state.experimental_col = st.selectbox("Select Experimental Model:", exp_options)

    # Filter rows with existing audio for both models
    valid_rows = []
    for idx, row in df.iterrows():
        base_audio = row[st.session_state.baseline_col]
        exp_audio = row[st.session_state.experimental_col]
        if (isinstance(base_audio, str) and os.path.exists(audio_path(st.session_state.baseline_col, base_audio)) and
            isinstance(exp_audio, str) and os.path.exists(audio_path(st.session_state.experimental_col, exp_audio))):
            valid_rows.append((idx, row['transcriptions']))

    if not valid_rows:
        st.warning("No matching audio pairs found.")
        return

    row_labels = [f"{i} - {t}" for i, t in valid_rows]
    row_choice = st.selectbox("Select transcription:", list(range(len(valid_rows))),
                              format_func=lambda x: row_labels[x])
    st.session_state.selected_row = valid_rows[row_choice][0]

    if st.button("Confirm Selection"):
        st.session_state.phase = 1
        st.rerun()


# --- Phase 1: Rating ---
def phase_1(df):
    st.header("Phase 1: Rate Both Versions")
    row = df.iloc[st.session_state.selected_row]
    transcription = row['transcriptions']
    base_audio = row[st.session_state.baseline_col]
    exp_audio = row[st.session_state.experimental_col]

    st.markdown(f"**Transcription:** {transcription}")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Baseline Audio")
        play_audio(st.session_state.baseline_col, base_audio)
    with col2:
        st.subheader("Experimental Audio")
        play_audio(st.session_state.experimental_col, exp_audio)

    st.session_state.baseline_score = st.slider(
        "Baseline Score:", 0, 100,
        value=st.session_state.baseline_score or 50
    )
    st.session_state.experimental_score = st.slider(
        "Experimental Score:", 0, 100,
        value=st.session_state.experimental_score or 50
    )

    if st.button("Submit Scores"):
        st.session_state.phase = 2
        st.rerun()


# --- Phase 2: Blind A/B ---
def phase_2(df):
    st.header("Phase 2: Blind Preference Test")
    row = df.iloc[st.session_state.selected_row]
    base_audio = row[st.session_state.baseline_col]
    exp_audio = row[st.session_state.experimental_col]

    pair = [
        ('baseline', st.session_state.baseline_col, base_audio),
        ('experimental', st.session_state.experimental_col, exp_audio)
    ]
    random.shuffle(pair)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Audio 1")
        play_audio(pair[0][1], pair[0][2])
    with col2:
        st.subheader("Audio 2")
        play_audio(pair[1][1], pair[1][2])

    choice = st.radio("Which do you prefer?", ["Audio 1", "Audio 2"])

    if st.button("Submit Preference"):
        preferred = pair[0][0] if choice == "Audio 1" else pair[1][0]
        consistent = preferred == 'experimental'

        log_entry = {
            'user_name': st.session_state.user_name,
            'baseline_model': st.session_state.baseline_col,
            'experimental_model': st.session_state.experimental_col,
            'baseline_audio_name': row[st.session_state.baseline_col],
            'experimental_audio_name': row[st.session_state.experimental_col],
            'baseline_score': st.session_state.baseline_score,
            'experimental_score': st.session_state.experimental_score,
            'preferred': preferred,
            'consistent': consistent
        }

        save_log(log_entry)
        st.success("Evaluation saved!")

        # Reset state
        for key in ['phase', 'baseline_score', 'experimental_score', 'selected_row']:
            st.session_state[key] = default_state[key]
        st.rerun()



# --- Main ---
def main():
    st.title("TTS Model Comparison App")
    show_rating_criteria_sidebar()
    df = load_data()
    if df.empty:
        st.stop()

    if not st.session_state.user_name:
        st.session_state.user_name = st.text_input("Enter your name:")
        if not st.session_state.user_name:
            return
        st.rerun()

    if st.session_state.phase == 0:
        phase_0(df)
    elif st.session_state.phase == 1:
        phase_1(df)
    elif st.session_state.phase == 2:
        phase_2(df)


if __name__ == "__main__":
    main()
