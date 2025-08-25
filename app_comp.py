import streamlit as st
import pandas as pd
import os
import datetime
import random
from itertools import combinations

# --- Paths ---
INPUT_CSV_PATH = 'app_input/csv/list.csv'
OUTPUT_CSV_PATH = 'app_output/comp_eval_log.csv'
AUDIO_DIR = 'app_input/audios'

# --- Session State Initialization ---
default_state = {
    'user_name': '',
    'df': None,
    'pairs': [],
    'current_pair_index': 0,
    'current_row_index': 0,
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


def generate_model_pairs(df):
    model_cols = [c for c in df.columns if c != 'transcriptions']
    return list(combinations(model_cols, 2))  # All pairs without repeats


# --- Phase: Rating Sequentially ---
def phase_rating(df):
    total_pairs = len(st.session_state.pairs)
    # Check if all pairs finished
    if st.session_state.current_pair_index >= total_pairs:
        st.success("All model pairs evaluated! 🎉")
        st.stop()

    b_col, e_col = st.session_state.pairs[st.session_state.current_pair_index]

    # Filter valid rows
    valid_rows = [
        idx for idx, row in df.iterrows()
        if isinstance(row[b_col], str) and row[b_col].strip() and
           isinstance(row[e_col], str) and row[e_col].strip() and
           os.path.exists(audio_path(b_col, row[b_col])) and
           os.path.exists(audio_path(e_col, row[e_col]))
    ]

    total_samples = len(valid_rows)
    if total_samples == 0:
        # Skip empty pair
        st.session_state.current_pair_index += 1
        st.session_state.current_row_index = 0
        st.session_state.baseline_score = None
        st.session_state.experimental_score = None
        st.rerun()
        return

    # Check if finished this pair
    if st.session_state.current_row_index >= total_samples:
        st.session_state.current_pair_index += 1
        st.session_state.current_row_index = 0
        st.session_state.baseline_score = None
        st.session_state.experimental_score = None
        st.rerun()
        return

    row_idx = valid_rows[st.session_state.current_row_index]
    row = df.iloc[row_idx]
    transcription = row['transcriptions']
    base_audio = row[b_col]
    exp_audio = row[e_col]

    st.header(f"Evaluating Pair {st.session_state.current_pair_index + 1} of {total_pairs}: {b_col} vs {e_col}")
    st.subheader(f"Sample {st.session_state.current_row_index + 1} of {total_samples}")
    st.markdown(f"**Transcription:** {transcription}")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader(f"{b_col} (Baseline)")
        play_audio(b_col, base_audio)
    with col2:
        st.subheader(f"{e_col} (Exp.)")
        play_audio(e_col, exp_audio)

    st.session_state.baseline_score = st.slider(
        "Baseline Score", 0, 100, value=st.session_state.baseline_score or 50
    )
    st.session_state.experimental_score = st.slider(
        "Experimental Score", 0, 100, value=st.session_state.experimental_score or 50
    )

    if st.button("Submit & Next"):
        log_entry = {
            'user_name': st.session_state.user_name,
            'baseline_model': b_col,
            'experimental_model': e_col,
            'baseline_audio_name': base_audio,
            'experimental_audio_name': exp_audio,
            'baseline_score': st.session_state.baseline_score,
            'experimental_score': st.session_state.experimental_score
        }
        save_log(log_entry)
        st.session_state.current_row_index += 1
        st.session_state.baseline_score = None
        st.session_state.experimental_score = None
        st.rerun()


# --- Main ---
def main():
    st.title("TTS Model Comparison App")
    show_rating_criteria_sidebar()
    df = load_data()
    if df.empty:
        st.stop()

    # User name input
    if not st.session_state.user_name:
        st.session_state.user_name = st.text_input("Enter your name:")
        if not st.session_state.user_name:
            return
        st.rerun()

    # Generate all pairs if not yet
    if not st.session_state.pairs:
        st.session_state.pairs = generate_model_pairs(df)
        st.session_state.current_pair_index = 0
        st.session_state.current_row_index = 0
        if not st.session_state.pairs:
            st.warning("No valid model pairs found.")
            st.stop()

    # Phase: Sequential rating
    phase_rating(df)


if __name__ == "__main__":
    main()
