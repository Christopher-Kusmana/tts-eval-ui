import streamlit as st
import pandas as pd
import os
import random
import datetime

# ----------------------------
# CONFIG
# ----------------------------
TEST_AUDIO_DIR = "./app_input/audios/test"
LOG_DIR = "./app_output"
LOG_FILE = os.path.join(LOG_DIR, "criteria_test_log.csv")
# ----------------------------
# TRANSCRIPTIONS
# ----------------------------
TRANSCRIPTIONS = {
    "sample_0.wav": "Setuju. Oiya, setelah turun stasiun, kita mampir ngopi yuk. Gue butuh kafein ekstra buat pulih. <mmm>",
    "sample_1.wav": "Oh baik, terima kasih telah melakukan pencairan di aplikasi kami. Jika nanti ada pertanyaan, silakan menghubungi Customer Service kami di 1500 729. Selamat beraktivitas kembali.',",
    "sample_2.wav": "Mohon maaf sepertinya ada gangguan sinyal, kami hanya ingin menginformasikan karena riwayat pembayaran kakak yang cukup baik di GoPay Pinjam, kakak bisa mendapatkan potongan biaya untuk penarikan selanjutnya.",
    "sample_3.wav": "Pinjaman kamu dua puluh ribu akan jatuh tempo dalam tiga hari, jangan lupa mengingatkan saya untuk melunasi ya",
    "sample_4.wav": "Dengan menggunakan QRIS, pembayaran menjadi lebih mudah dan praktis, baik untuk transaksi kecil maupun besar",
    "sample_5.wav": "Baik, kalau boleh tahu, apa ada alasan khusus kenapa kakak belum tertarik untuk melanjutkan ke proses pencairan?",
    "sample_6.wav": "Oh baik, mungkin bisa dicoba dulu kak untuk mencairkan dananya, mulai dari dua ratus ribu saja. Setelah ada riwayat transaksi, kedepannya akun Gopay Pinjam kakak bisa kami upgrade untuk dapat harga lebih murah, limit lebih tinggi dan tenor lebih panjang.",
    "sample_7.wav": "<mmm> mengenai masalah ini, pastikan kakak sudah memperbarui aplikasinya ke versi terbaru.",
    "sample_8.wav": "Iya, padahal kalau santai pasti lebih nyaman. Tapi ya gitu, siapa cepat dia dapat spot deket pegangan.",
    "sample_9.wav": "Mohon maaf sepertinya ada gangguan sinyal, kami hanya ingin menginformasikan karena riwayat pembayaran kakak yang cukup baik di GoPay Pinjam, kakak bisa mendapatkan potongan biaya untuk penarikan selanjutnya.",
}

# Expected reference scores for sample_0.wav to sample_9.wav
REFERENCE_SCORES = {f"sample_{i}.wav": i for i in range(10)}  # 0-10 scale
TOTAL_TESTS = len(REFERENCE_SCORES)

# ----------------------------
# SIDEBAR CRITERIA
# ----------------------------
def show_sidebar_criteria():
    st.sidebar.title("📊 Rating Criteria")
    criteria = [
        ("0", "Not speech", "Just noise or broken sound."),
        ("1", "Very hard to hear", "Almost nothing is clear."),
        ("2", "Very bad", "Many word errors."),
        ("3", "Bad", "Robotic or awkward."),
        ("4", "Not natural", "Flat or unnatural."),
        ("5", "Clear but robotic", "No emotion."),
        ("6", "Mostly accurate", "Some pitch/emotion."),
        ("7", "Natural feel", "Minor issues."),
        ("8", "Very natural", "Almost no errors."),
        ("9", "Extremely natural", "Feels human."),
        ("10", "Perfect", "Indistinguishable from real.")
    ]
    df = pd.DataFrame(criteria, columns=["Score", "Label", "Description"])
    st.sidebar.markdown(df.to_html(index=False), unsafe_allow_html=True)

# ----------------------------
# SESSION STATE INITIALIZATION
# ----------------------------
def initialize_session_state():
    defaults = {
        "user_name": None,
        "current_audio": None,
        "chosen_score": None,
        "done_audios": set(),
        "page": "name_input",
        "temp_user_name": ""
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def ensure_dirs():
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(TEST_AUDIO_DIR, exist_ok=True)

def pick_random_audio():
    remaining = list(set(REFERENCE_SCORES.keys()) - st.session_state.done_audios)
    if not remaining:
        return None
    return random.choice(remaining)

def log_user_score(audio_name, reference_score, user_score):
    ensure_dirs()
    timestamp = datetime.datetime.now().isoformat()
    new_entry = pd.DataFrame([{
        "user_name": st.session_state.user_name,
        "audio_name": audio_name,
        "reference_score": reference_score,
        "user_score": user_score,
        "timestamp": timestamp
    }])

    if os.path.exists(LOG_FILE):
        df_log = pd.read_csv(LOG_FILE)
        # Remove existing record for this user & audio
        df_log = df_log[
            ~((df_log["user_name"] == st.session_state.user_name) &
              (df_log["audio_name"] == audio_name))
        ]
        df_log = pd.concat([df_log, new_entry], ignore_index=True)
    else:
        df_log = new_entry

    df_log.to_csv(LOG_FILE, index=False)

# ----------------------------
# RESULTS CALCULATION
# ----------------------------
def calculate_results():
    if not os.path.exists(LOG_FILE):
        return None

    df_log = pd.read_csv(LOG_FILE)
    user_df = df_log[df_log["user_name"] == st.session_state.user_name]

    if user_df.empty:
        return None

    # Calculate error metrics
    user_df["abs_error"] = (user_df["user_score"] - user_df["reference_score"]).abs()

    # Accuracy: score considered correct if within ±1
    accuracy = (user_df["abs_error"] <= 1).mean() * 100

    avg_error = user_df["abs_error"].mean()
    max_error = user_df["abs_error"].max()
    min_error = user_df["abs_error"].min()

    return {
        "accuracy": accuracy,
        "avg_error": avg_error,
        "min_error": min_error,
        "max_error": max_error,
        "log": user_df
    }

# ----------------------------
# MAIN APP
# ----------------------------
def main():
    st.set_page_config(page_title="Criteria Understanding Test", layout="centered")
    initialize_session_state()
    ensure_dirs()
    show_sidebar_criteria()

    # ---------------- Name Input Page ----------------
    if st.session_state.page == "name_input":
        st.title("Criteria Understanding Test")

        def start_test():
            name = st.session_state.temp_user_name.strip()
            if name:
                st.session_state.user_name = name
                st.session_state.page = "testing"
                st.session_state.current_audio = pick_random_audio()
                st.session_state.trigger_rerun = True

        st.text_input(
            "Enter your name:",
            key="temp_user_name",
            on_change=start_test
        )

        if st.session_state.get("trigger_rerun", False):
            st.session_state.trigger_rerun = False
            st.rerun()

    # ---------------- Testing Page ----------------
    elif st.session_state.page == "testing":
        done_count = len(st.session_state.done_audios)
        st.markdown(f"### Progress: {done_count}/{TOTAL_TESTS} audios rated")

        if done_count >= TOTAL_TESTS:
            st.success("All audios have been rated! Thank you for completing the test.")
            results = calculate_results()
            if results:
                st.subheader("Your Results")
                st.metric("Accuracy (±1 Tolerance)", f"{results['accuracy']:.1f}%")
                st.metric("Average Error", f"{results['avg_error']:.2f}")
                st.metric("Min Error", f"{results['min_error']:.0f}")
                st.metric("Max Error", f"{results['max_error']:.0f}")

                # Pass/Fail
                if results["accuracy"] >= 80:
                    st.success("Status: PASSED 🎉")
                else:
                    st.error("Status: FAILED ❌ (Accuracy < 80%)")

                st.dataframe(results["log"])
            return

        st.title(f"Hello {st.session_state.user_name}! Rate the following audio.")
        audio_name = st.session_state.current_audio
        audio_path = os.path.join(TEST_AUDIO_DIR, audio_name)

        if os.path.exists(audio_path):
            st.audio(audio_path, format="audio/wav")

            if audio_name in TRANSCRIPTIONS:
                st.markdown(f"**Transcription:** {TRANSCRIPTIONS[audio_name]}")

            if "chosen_score" not in st.session_state or st.session_state.chosen_score is None:
                st.session_state.chosen_score = 5

            st.slider(
                "Rate from 0 (worst) to 10 (best):",
                min_value=0,
                max_value=10,
                step=1,
                key="chosen_score"
            )

            if st.button("Submit Score", key=f"submit_{audio_name}"):
                ref_score = REFERENCE_SCORES[audio_name]
                log_user_score(audio_name, ref_score, st.session_state.chosen_score)
                st.session_state.done_audios.add(audio_name)
                st.session_state.current_audio = pick_random_audio()
                st.rerun()
        else:
            st.error(f"Audio file not found: {audio_path}")

if __name__ == "__main__":
    main()
