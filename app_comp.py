import streamlit as st
import pandas as pd
import random
import os

# Define file paths
INPUT_CSV_PATH = 'app_input/csv/comp_eval_list.csv'
OUTPUT_CSV_PATH = 'app_output/comp_eval_log.csv'
AUDIO_DIR = 'app_input/audios'

# --- Session State Initialization ---
if 'user_name' not in st.session_state:
    st.session_state.user_name = ''
if 'df' not in st.session_state:
    st.session_state.df = None
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'eval_data' not in st.session_state:
    st.session_state.eval_data = []
if 'current_phase' not in st.session_state:
    st.session_state.current_phase = 1
if 'new_score' not in st.session_state:
    st.session_state.new_score = None

# --- Main App Logic ---

def main():
    st.title("TTS Model Comparison App 🗣️")

    # 1. User Name Input (Authentication)
    if not st.session_state.user_name:
        st.session_state.user_name = st.text_input("Please enter your name to start:")
        if st.session_state.user_name:
            st.success(f"Hello, {st.session_state.user_name}! Let's begin the evaluation.")
            # Load the data after the user name is entered
            load_data()
            st.rerun()
        else:
            return

    # 2. Data Loading
    if st.session_state.df is None:
        load_data()
        return

    # Check if all audios have been evaluated
    if st.session_state.current_index >= len(st.session_state.df):
        evaluation_complete()
        return

    # Get the current row for evaluation
    current_row = st.session_state.df.iloc[st.session_state.current_index]

    # 3. Phase 1: Score Evaluation
    if st.session_state.current_phase == 1:
        phase_1(current_row)

    # 4. Phase 2: Preference Check
    elif st.session_state.current_phase == 2:
        phase_2(current_row)

# --- Helper Functions ---

def load_data():
    """Loads the evaluation list CSV into a DataFrame."""
    try:
        st.session_state.df = pd.read_csv(INPUT_CSV_PATH)
    except FileNotFoundError:
        st.error(f"Error: The file {INPUT_CSV_PATH} was not found. Please ensure it exists.")
        st.stop()
    except Exception as e:
        st.error(f"An error occurred while reading the CSV file: {e}")
        st.stop()

def phase_1(row):
    """Handles the first phase of evaluation (new score)."""
    st.header(f"Phase 1: Rate the Experimental Model ({st.session_state.current_index + 1}/{len(st.session_state.df)})")
    st.write("---")

    st.markdown(f"**Transcription:** *{row['transcriptions']}*")
    st.info(f"The baseline model's score is: **{row['baseline_score']}**")

    st.subheader("Baseline Audio")
    baseline_audio_path = os.path.join(AUDIO_DIR, row['baseline_audio_name'])
    display_audio(baseline_audio_path)

    st.subheader("Experimental Audio")
    experimental_audio_path = os.path.join(AUDIO_DIR, row['experimental_audio_name'])
    display_audio(experimental_audio_path)

    new_score = st.slider("Give the new audio a score (1-100):", min_value=1, max_value=100, value=50)

    if st.button("Submit Score", key="submit_score_btn"):
        st.session_state.new_score = new_score
        st.session_state.current_phase = 2
        st.rerun()

def phase_2(row):
    """Handles the second phase of evaluation (preference check)."""
    st.header(f"Phase 2: A/B Preference Test ({st.session_state.current_index + 1}/{len(st.session_state.df)})")
    st.write("---")
    st.info("Listen to both audios and select the one you prefer.")

    # Randomize the order of the audio files
    audio_pair = [
        ('baseline', os.path.join(AUDIO_DIR, row['baseline_audio_name'])),
        ('experimental', os.path.join(AUDIO_DIR, row['experimental_audio_name']))
    ]
    random.shuffle(audio_pair)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Audio 1")
        display_audio(audio_pair[0][1])
    with col2:
        st.subheader("Audio 2")
        display_audio(audio_pair[1][1])

    preference = st.radio("Which one do you prefer?", ('Audio 1', 'Audio 2'))

    if st.button("Submit Preference", key="submit_preference_btn"):
        # Determine consistency
        preferred_audio_label = 'experimental' if preference == 'Audio 2' else 'baseline'
        consistent = (preferred_audio_label == audio_pair[1][0] if preference == 'Audio 2' else preferred_audio_label == audio_pair[0][0])
        
        # Log the data
        log_entry = {
            'user_name': st.session_state.user_name,
            'baseline_audio_name': row['baseline_audio_name'],
            'experimental_audio_name': row['experimental_audio_name'],
            'transcriptions': row['transcriptions'],
            'model_name': row['model_name'],
            'baseline_model_ver': row['baseline_model_ver'],
            'experimental_model_ver': row['experimental_model_ver'],
            'baseline_score': row['baseline_score'],
            'new_score': st.session_state.new_score,
            'consistent': consistent
        }
        st.session_state.eval_data.append(log_entry)

        st.success("Your evaluation has been logged! Loading the next audio pair...")
        st.session_state.current_index += 1
        st.session_state.current_phase = 1
        st.session_state.new_score = None  # Reset score for the next round
        st.rerun()

def evaluation_complete():
    """Handles the completion of all evaluations."""
    st.header("Evaluation Complete! 🎉")
    st.success("Thank you for your help in evaluating the models.")

    # Convert logged data to a DataFrame and save to CSV
    log_df = pd.DataFrame(st.session_state.eval_data)
    
    # Check if the output directory exists, create if not
    output_dir = os.path.dirname(OUTPUT_CSV_PATH)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Append to the CSV file
    if not os.path.exists(OUTPUT_CSV_PATH):
        log_df.to_csv(OUTPUT_CSV_PATH, index=False)
    else:
        log_df.to_csv(OUTPUT_CSV_PATH, mode='a', header=False, index=False)
    
    st.balloons()
    
def display_audio(path):
    """Displays an audio player if the file exists."""
    if os.path.exists(path):
        st.audio(path, width=100)
    else:
        st.error(f"Audio file not found at: {path}")

# Run the app
if __name__ == "__main__":
    main()