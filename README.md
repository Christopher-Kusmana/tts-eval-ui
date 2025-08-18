# TTS Evaluation UI

A Streamlit app to evaluate TTS audio. Users enter a name, rate audio (1–100, -1 = unscored), navigate samples, and log scores to `logs/eval_log.csv`.

## Features
- Name submission before evaluation  
- Audio anonymized as "Audio 1", "Audio 2", …  
- Number input for scoring (-1 = unscored)  
- Previous/Next navigation  
- Automatic CSV logging per user  

## Setup
```bash
1. git pull https://github.com/Christopher-Kusmana/tts-eval-ui.git
2. cd tts-eval-ui
3. sh setup.sh        # enter Conda env name when prompted
4. conda activate <env_name>
5. add audio recordings in audios directory  
6. streamlit run app.py
```

## Usage


1. Enter your name when prompted.
2. Evaluate audio:
  2a. Listen to the audio.
  2b. Enter score (1–100) in the number input, or -1 for unscored.
  2c. Navigate with "Previous" / "Next" buttons.
3. Save logs: click "💾 Save All Scores to Log" to persist session scores to logs/eval_log.csv.
