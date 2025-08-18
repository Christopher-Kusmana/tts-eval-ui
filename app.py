import streamlit as st
import pandas as pd
import os
import glob

# CONFIG
LOG_DIR = 'logs'
LOG_FILE = os.path.join(LOG_DIR, 'eval_log.csv')
AUDIO_DIR = 'audios' # Stored audio dir

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
    current_audio = st.session_state.audio_files[st.session_state.audio_index]
    # The score is directly from the text input widget's key
    st.session_state.scores[current_audio] = st.session_state.score_text_input_key


def log_all_evaluations():
    """Logs all current evaluations for the user to the CSV file, overwriting previous entries for this user."""
    user = st.session_state.user_name

    if user:
        # Load existing logs from the CSV file
        if os.path.exists(LOG_FILE):
            df_log = pd.read_csv(LOG_FILE)
        else:
            df_log = pd.DataFrame(columns=['user_name', 'audio_file', 'score'])

        # Filter out existing entries for the current user to prepare for update
        df_other_users = df_log[df_log['user_name'] != user]

        # Create new entries for the current user based on current session_state.scores
        new_user_scores = []
        for audio_file_path, score_val in st.session_state.scores.items():
            if score_val != -1: # Only log if a score has been set (not -1)
                new_user_scores.append({
                    'user_name': user,
                    'audio_file': os.path.basename(audio_file_path), # Keep actual filename in log
                    'score': score_val
                })
        df_current_user = pd.DataFrame(new_user_scores)

        # Combine the other users' data with the current user's updated data
        df_final_log = pd.concat([df_other_users, df_current_user], ignore_index=True)
        
        # Save the complete, updated DataFrame back to the CSV
        df_final_log.to_csv(LOG_FILE, index=False)
        st.success(f"All {len(new_user_scores)} scores for {user} saved to '{LOG_FILE}'!")
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
        # Load audio files once the name is submitted
        st.session_state.audio_files = load_audio_files()
        # Initialize scores for each audio file to -1 (unscored)
        for audio_file in st.session_state.audio_files:
            if audio_file not in st.session_state.scores:
                st.session_state.scores[audio_file] = -1 # Default score is now -1
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
        if st.session_state.user_name:
            st.title(f"Hello, {st.session_state.user_name}! Let's Evaluate. 🎧")

            if not st.session_state.audio_files:
                st.warning(f"No audio files found. Please add .wav files to the '{AUDIO_DIR}' directory.")
                return

            current_audio_file = st.session_state.audio_files[st.session_state.audio_index]
            
            # Anonymize the display name
            audio_display_name = f"Audio {st.session_state.audio_index + 1}"

            st.subheader(f"Audio {st.session_state.audio_index + 1} of {len(st.session_state.audio_files)}")
            st.markdown(f"**Now evaluating:** `{audio_display_name}`")

            # Display audio player
            st.audio(current_audio_file, format='audio/wav')

            # Get the current score for this audio file, or use default (-1) if not set
            current_score_value = st.session_state.scores.get(current_audio_file, -1)

            #  SCORING INPUT FIELD
            display_score_text_input = "Unscored" if current_score_value == -1 else str(current_score_value)
            st.write(f"**Current Score:** {display_score_text_input}") 
            
            st.number_input(
                'Enter rating (1-100, or -1 for unscored):',
                min_value=-1,
                max_value=100,
                value=current_score_value,
                step=1, # Ensure it takes integer steps
                key='score_text_input_key', # Key for the text input
                on_change=_save_score_from_input # Callback to save score when text input changes
            )

            st.caption("This slider is for visual reference only. Enter your score in the text field above. ")
            st.slider(
                'Visual Score Range:', # Label for visual slider
                min_value=-1, # Allow -1 for visual representation
                max_value=100,
                value=current_score_value, # Value directly from session state (updated by text input)
                disabled=True, 
                key='score_visual_slider_key' # Distinct key, not used for saving
            )
            
            # NAV BUTTONS AND SAVE
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button('⬅️ Previous', on_click=prev_audio, disabled=(st.session_state.audio_index == 0)):
                    pass # Handled by on_click
            with col2:
                if st.button('Next ➡️', on_click=next_audio, disabled=(st.session_state.audio_index == len(st.session_state.audio_files) - 1)):
                    pass # Handled by on_click
            with col3:
                # --- Changed button to save all logs ---
                st.button('💾 Save All Scores to Log', on_click=log_all_evaluations)

            st.markdown("---")
            st.write("### Your Current Scores (Session-only preview):")
            # Display current scores in session state for user reference, also anonymized
            session_scores_data = []
            # Iterate through the actual audio_files list to maintain order and current index
            for i, aud_file_path in enumerate(st.session_state.audio_files):
                score_val = st.session_state.scores.get(aud_file_path)
                # Display "Unscored" for -1 in the preview table
                display_score_in_table = "Unscored" if score_val == -1 else score_val
                session_scores_data.append({"Audio File": f"Audio {i+1}", "Score": display_score_in_table})
            if session_scores_data:
                st.dataframe(pd.DataFrame(session_scores_data), use_container_width=True)
            else:
                st.info("No scores recorded yet in this session.")

            st.markdown("---")
            st.info("Your scores are logged to 'logs/eval_log.csv'. **Only scores not equal to -1 will be saved.**")

        else:
            st.error("User name not set. Please go back and enter your name.")
            st.button("Go back to Name Input", on_click=lambda: st.session_state.update(page='name_input'))

if __name__ == '__main__':
    main()
