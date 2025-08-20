import streamlit as st
import pandas as pd
import os
import glob

# CONFIG
CSV_INPUT = "app_input/csv/single_eval_list.csv"
LOG_DIR = 'app_output'
LOG_FILE = os.path.join(LOG_DIR, 'single_eval_log.csv')
AUDIO_DIR = 'app_input/audios' # Stored audio dir

# STATES
def initialize_session_state():
    if 'user_name' not in st.session_state:
        st.session_state.user_name = None
    if 'audio_files' not in st.session_state:
        st.session_state.audio_files = []
    if 'audio_index' not in st.session_state:
        st.session_state.audio_index = 0
    if 'scores' not in st.session_state:
        # Dictionary to store scores: {audio_file_path: score}
        st.session_state.scores = {}
    if 'page' not in st.session_state:
        st.session_state.page = 'name_input' # 'name_input' or 'evaluation'

# HELPER FUNCTIONS

def ensure_dirs():
    """Enforces logs and audio directories existence"""
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)

def show_rating_criteria():
    criteria = [
        ( "0–9",   "Not speech", "Just noise or broken sound. Nothing understandable."),
        ( "10–19", "Very hard to hear", "Almost nothing is clear. May have serious errors or missing words."),
        ( "20–29", "Very bad", "Some parts are understandable, but many word errors. Unnatural or emotionless voice."),
        ( "30–39", "Bad", "A lot of words are wrong or mispronounced. Sounds robotic or awkward."),
        ( "40–49", "Not natural", "Most words are correct, but the voice is very flat or unnatural. Hard to enjoy."),
        ( "50–59", "Clear but robotic", "All words are right, but voice is flat, with no emotion. Feels like a computer."),
        ( "60–69", "Mostly accurate, some prosody", "All/most words correct, and there's a bit of pitch/emotion. Still sounds artificial."),
        ( "70–79", "Natural feel with minor issues", "Sounds mostly human. Has emotion and rhythm. May have 1 small word mistake."),
        ( "80–89", "Very natural", "Fluent, expressive, natural. Almost no errors."),
        ( "90–99", "Extremely natural", "Feels just like a human speaker. No word errors, natural tone and flow."),
        ( "100",   "Perfect", "Perfect emotion, rhythm, clarity. Indistinguishable from a real person.")
    ]
    df = pd.DataFrame(criteria, columns=["Score Range", "Rating Label", "Description"])
    st.markdown("### 📊 Rating Criteria")
    st.markdown(df.to_html(index=False), unsafe_allow_html=True)

def load_audio_list():
    """Load audio metadata list from CSV."""
    if not os.path.exists(CSV_INPUT):
        st.error(f"Missing {CSV_INPUT}. Please provide a CSV with audio_name, transcriptions, log_ver, model_name.")
        return []

    df = pd.read_csv(CSV_INPUT)

    # Check required columns
    required_cols = {"audio_name", "transcriptions", "model_ver", "model_name"}
    if not required_cols.issubset(df.columns):
        st.error(f"{CSV_INPUT} must contain columns: {required_cols}")
        return []

    # Attach .wav path for each row
    df["audio_path"] = df["audio_name"].apply(lambda x: os.path.join(AUDIO_DIR, x))
    missing = df[~df["audio_path"].apply(os.path.exists)]
    if not missing.empty:
        st.warning(f"⚠️ Missing audio files for: {missing['audio_name'].tolist()}")

    return df.to_dict("records")  # return list of dicts

def load_transcriptions():
    """Load transcriptions from CSV into a dict {audio_name: transcription}."""
    if not os.path.exists(CSV_INPUT):
        st.error(f"Missing {CSV_INPUT}. Please provide it with audio_name, transcriptions, model_ver, model_name.")
        return {}

    df = pd.read_csv(CSV_INPUT)

    if "audio_name" not in df.columns or "transcriptions" not in df.columns:
        st.error("CSV must contain at least 'audio_name' and 'transcriptions' columns.")
        return {}

    # Build mapping {audio_name: transcription}
    transcription_map = {}
    for _, row in df.iterrows():
        # Use the audio_name directly as the key
        transcription_map[str(row["audio_name"])] = str(row["transcriptions"])
    return transcription_map

def load_audio_files():
    """Loads all .wav files from the audio directory."""
    # Create some dummy audio files if the directory is empty for demonstration
    if not os.listdir(AUDIO_DIR):
        st.warning(f"'{AUDIO_DIR}' directory is empty. Creating dummy audio files for demonstration.")
        for i in range(5):
            with open(os.path.join(AUDIO_DIR, f'dummy_audio_{i+1}.wav'), 'wb') as f:
                f.write(b'RIFF\x26\x00\x00\x00WAVEfmt \x12\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88\x13\x00\x00\x02\x00\x10\x00data\x02\x00\x00\x00\x00\x00')
                
    audio_files = sorted(glob.glob(os.path.join(AUDIO_DIR, '*.wav')))
    if not audio_files:
        st.error(f"No .wav files found in the '{AUDIO_DIR}' directory. Please add some audio files.")
    return audio_files

def _save_score_from_input():
    """Saves the score from the text input field to session_state.scores."""
    # Get the dictionary for the current audio file
    current_audio_entry = st.session_state.audio_files[st.session_state.audio_index]
    
    # Use the 'audio_path' (a string) from the dictionary as the key
    current_audio_path = current_audio_entry['audio_path']

    # The score is directly from the text input widget's key
    st.session_state.scores[current_audio_path] = st.session_state.score_text_input_key

def log_all_evaluations():
    """Logs all new evaluations for the user to the CSV file, appending new entries."""
    user = st.session_state.user_name

    if user:
        # Create a list to store new log entries for the current session
        new_log_entries = []

        # Find which audio files have new scores to log
        for audio_file_path, score_val in st.session_state.scores.items():
            # Only log if a score has been set and it's not the default unscored value
            if score_val != -1:
                # Find the corresponding audio entry from the loaded list
                audio_entry = next((entry for entry in st.session_state.audio_files if entry['audio_path'] == audio_file_path), None)

                if audio_entry:
                    new_log_entries.append({
                        'user_name': user,
                        'audio_file': os.path.basename(audio_file_path),
                        'transcriptions': audio_entry['transcriptions'],
                        'model_name': audio_entry['model_name'],
                        'model_ver': audio_entry['model_ver'],
                        'score': score_val
                    })
                else:
                    st.warning(f"Metadata for audio file '{os.path.basename(audio_file_path)}' not found in session state. Skipping log for this file.")
        
        if new_log_entries:
            df_to_append = pd.DataFrame(new_log_entries)
            
            # Check if the log file exists to decide whether to write the header
            if not os.path.exists(LOG_FILE):
                df_to_append.to_csv(LOG_FILE, index=False)
            else:
                df_to_append.to_csv(LOG_FILE, mode='a', header=False, index=False)
            
            st.success(f"All {len(new_log_entries)} scores for {user} saved to '{LOG_FILE}'!")
            # Reset scores to prevent duplicate logging on subsequent runs
            st.session_state.scores = {audio['audio_path']: -1 for audio in st.session_state.audio_files}
        else:
            st.info("No new scores to save.")
    else:
        st.warning("User name not set. Cannot save logs.")

def next_audio():
    """Advances to the next audio file."""
    _save_score_from_input() # Save current score from the text input before moving
    if st.session_state.audio_index < len(st.session_state.audio_files) - 1:
        st.session_state.audio_index += 1
    else:
        st.info("You've reached the last audio file.")

def prev_audio():
    """Goes back to the previous audio file."""
    _save_score_from_input() # Save current score from the text input before moving
    if st.session_state.audio_index > 0:
        st.session_state.audio_index -= 1
    else:
        st.info("You're at the first audio file.")

def submit_name():
    """Sets the user name and transitions to the evaluation page."""
    if st.session_state.temp_user_name:
        st.session_state.user_name = st.session_state.temp_user_name
        st.session_state.page = 'evaluation'
        # Call the correct function to load audio metadata from the CSV
        st.session_state.audio_files = load_audio_list()
        # Initialize scores for each audio entry
        for audio_entry in st.session_state.audio_files:
            audio_path = audio_entry["audio_path"]
            if audio_path not in st.session_state.scores:
                st.session_state.scores[audio_path] = -1
    else:
        st.warning("Please enter your name to start the evaluation.")
# APP
def main():
    st.set_page_config(page_title="TTS Evaluation", layout="centered")
    initialize_session_state()
    ensure_dirs()

    if st.session_state.page == 'name_input':
        st.title('TTS Evaluation App')
        st.write('Please enter your name to begin the audio evaluation.')
        st.text_input('Your Name:', key='temp_user_name', on_change=submit_name)
        st.button('Start Evaluation', on_click=submit_name)

    elif st.session_state.page == 'evaluation':
        # This is where the logical flow for the evaluation page starts
        if not st.session_state.user_name:
            st.error("User name not set. Please go back and enter your name.")
            st.button("Go back to Name Input", on_click=lambda: st.session_state.update(page='name_input'))
            return

        st.title(f"Hello, {st.session_state.user_name}! Let's Evaluate. 🎧")
        show_rating_criteria()
        st.markdown("---")

        if not st.session_state.audio_files:
            st.warning("No audio entries found. Please check 'app_input/csv/single_eval_list.csv' and the 'audios' directory.")
            return

        # Fetch the current audio entry once at the beginning
        current_audio_entry = st.session_state.audio_files[st.session_state.audio_index]
        current_audio_path = current_audio_entry["audio_path"]
        current_transcription = current_audio_entry["transcriptions"]
        current_model_name = current_audio_entry["model_name"]
        
        # Display all information for the current audio entry
        st.subheader(f"Audio {st.session_state.audio_index + 1} of {len(st.session_state.audio_files)}")
        st.markdown(f"**Model:** `{current_model_name}`")
        st.markdown(f"**Transcript:** {current_transcription}")
        
        # Display audio player using the correct path
        st.audio(f"{current_audio_path}", format='audio/wav')
        
        # Get the current score for this audio file, or use default (-1) if not set
        # Use the audio path as the key for the scores dictionary
        current_score_value = st.session_state.scores.get(current_audio_path, -1)

        # SCORING INPUT FIELD
        display_score_text_input = "Unscored" if current_score_value == -1 else str(current_score_value)
        st.write(f"**Current Score:** {display_score_text_input}") 
        
        st.number_input(
            'Enter rating (1-100, or -1 for unscored):',
            min_value=-1,
            max_value=100,
            value=current_score_value,
            step=1, 
            key='score_text_input_key',
            on_change=_save_score_from_input
        )
        
        st.caption("This slider is for visual reference only. Enter your score in the text field above. ")
        st.slider(
            'Visual Score Range:',
            min_value=-1,
            max_value=100,
            value=current_score_value,
            disabled=True, 
            key='score_visual_slider_key'
        )
        
        is_current_audio_unscored = (st.session_state.scores.get(current_audio_path) == -1)

        # NAV BUTTONS AND SAVE
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button('⬅️ Previous', on_click=prev_audio, disabled=(st.session_state.audio_index == 0)):
                pass
        with col2:
            if st.button(
                'Next ➡️', 
                on_click=next_audio, 
                disabled=(st.session_state.audio_index == len(st.session_state.audio_files) - 1) or is_current_audio_unscored
            ):
                pass
        with col3:
            st.button('💾 Save All Scores to Log', on_click=log_all_evaluations)

        # st.write("### Your Current Scores (Session-only preview):")
        
        # session_scores_data = []
        # for i, audio_entry in enumerate(st.session_state.audio_files):
        #     audio_path = audio_entry['audio_path']
        #     score_val = st.session_state.scores.get(audio_path, -1)
        #     display_score_in_table = "Unscored" if score_val == -1 else score_val
        #     session_scores_data.append({"Audio File": f"Audio {i+1}", "Score": display_score_in_table})
        
        # if session_scores_data:
        #     st.dataframe(pd.DataFrame(session_scores_data), use_container_width=True)
        # else:
        #     st.info("No scores recorded yet in this session.")

        st.markdown("---")
        st.info("Your scores are logged to 'logs/single_eval_log.csv'. **Only scores not equal to -1 will be saved.**")
    
if __name__ == '__main__':
    main()