# TTS Evaluation UI - Single Eval App

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

# TTS Evaluation UI – Comparison Eval App

A **Streamlit app** for **A/B testing two Text-to-Speech (TTS) models**.  
Users evaluate audio pairs through a **two-phase process**, and results are automatically logged to a CSV file.

---

## Features

- **User Authentication**  
  - Logs the evaluator’s name for tracking.

- **Two-Phase Evaluation**
  1. **Scoring Phase** – Rate the *Experimental* audio (1–5) while referencing a *Baseline*.  
  2. **Blind A/B Test** – Choose your preferred audio from a randomized pair.  

- **Consistency Check**  
  - Automatically determines if blind preference aligns with the scored rating.  

- **Automatic Logging**  
  - All results saved to:  
    ```
    app_output/comp_eval_log.csv
    ```
## Setup
```bash
1. git pull https://github.com/Christopher-Kusmana/tts-eval-ui.git
2. cd tts-eval-ui
3. sh setup.sh        # enter Conda env name when prompted
4. conda activate <env_name>
5. add audio recordings in audios directory  
6. streamlit run app_comp.py
```