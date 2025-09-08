#!/bin/bash

# --- Environment Setup Script for Streamlit TTS Evaluation App ---

set -euo pipefail

APP_NAME="Streamlit TTS Evaluation App"
PY_VERSION="3.11"
TEST_AUDIO_DIR="./app_input/audios/test"
LOG_DIR="./app_output"
LOG_FILE="${LOG_DIR}/criteria_test_log.csv"

echo "======================================================================"
echo "🔧 Environment Setup: ${APP_NAME}"
echo "======================================================================"

# --- Helper to print final run instructions ---
print_final_instructions() {
  echo ""
  echo "----------------------------------------------------------------------"
  echo "🎉 Setup complete for your ${APP_NAME}! 🎉"
  echo "----------------------------------------------------------------------"
  echo "Project paths:"
  echo "  • Test audios: ${TEST_AUDIO_DIR}"
  echo "  • Output logs: ${LOG_DIR}"
  echo "  • Log file:    ${LOG_FILE}"
  echo ""
  echo "To run the app:"
  if [[ "${1}" == "conda" ]]; then
    echo "1) conda activate ${2}"
  else
    echo "1) source ${2}/bin/activate"
  fi
  echo "2) streamlit run app.py"
  echo "----------------------------------------------------------------------"
}

# Ensure folders exist (safe if already present)
mkdir -p "${TEST_AUDIO_DIR}" "${LOG_DIR}"

echo "Checking for Conda installation..."
if command -v conda &> /dev/null; then
  echo "✅ Conda found."

  # Ask for environment name
  read -p "Enter the name for your new conda environment (e.g., tts_eval_env): " ENV_NAME
  if [[ -z "${ENV_NAME}" ]]; then
    echo "❌ Environment name cannot be empty."
    exit 1
  fi

  # Initialize conda for correct 'conda activate' in scripts
  # shellcheck disable=SC1091
  source "$(conda info --base)/etc/profile.d/conda.sh"

  # Check if environment already exists
  if conda env list | awk '{print $1}' | grep -qx "${ENV_NAME}"; then
    echo "⚠️  Conda environment '${ENV_NAME}' already exists."
    read -p "Do you want to remove and recreate it? (y/N): " RECREATE
    if [[ "${RECREATE:-N}" =~ ^[yY]$ ]]; then
      echo "Removing existing environment '${ENV_NAME}'..."
      conda env remove -y -n "${ENV_NAME}" || { echo "❌ Failed to remove existing environment."; exit 1; }
      echo "✅ Existing environment removed."
    else
      echo "Aborting setup. Choose a different name, or manually use the existing environment."
      exit 0
    fi
  fi

  echo "Creating new conda environment '${ENV_NAME}' with Python ${PY_VERSION}..."
  conda create -y -n "${ENV_NAME}" "python=${PY_VERSION}" || { echo "❌ Failed to create conda environment."; exit 1; }
  echo "✅ Environment '${ENV_NAME}' created."

  echo "Activating '${ENV_NAME}'..."
  conda activate "${ENV_NAME}" || { echo "❌ Failed to activate environment."; exit 1; }
  echo "✅ Environment activated."

  echo "Installing packages (pandas, streamlit)..."
  conda install -y pandas || { echo "❌ Failed to install pandas."; exit 1; }
  conda install -y -c conda-forge streamlit || { 
    echo "⚠️  Conda streamlit install failed. Trying pip as fallback..."
    pip install --upgrade pip
    pip install --upgrade streamlit || { echo "❌ Failed to install streamlit with pip."; exit 1; }
  }
  echo "✅ Packages installed."

  print_final_instructions "conda" "${ENV_NAME}"
  exit 0
fi

# -------------------- venv FALLBACK (Conda not found) --------------------
echo "⚠️  Conda not found. Switching to Python venv setup."

# Check for python3
if ! command -v python3 &> /dev/null; then
  echo "❌ Error: 'python3' is not installed or not on PATH."
  echo "Please install Python ${PY_VERSION} or newer, then re-run this script."
  echo ""
  echo "Quick tips:"
  echo "  • macOS (Homebrew):  brew install python"
  echo "  • Ubuntu/Debian:     sudo apt-get update && sudo apt-get install -y python3 python3-venv python3-pip"
  exit 1
fi

# Ask for venv directory (default: .venv)
read -p "Enter a directory name for your virtual environment [default: .venv]: " VENV_DIR
VENV_DIR=${VENV_DIR:-.venv}

if [[ -d "${VENV_DIR}" ]]; then
  echo "⚠️  Virtual environment directory '${VENV_DIR}' already exists."
  read -p "Do you want to remove and recreate it? (y/N): " RECREATE_VENV
  if [[ "${RECREATE_VENV:-N}" =~ ^[yY]$ ]]; then
    rm -rf "${VENV_DIR}"
    echo "✅ Removed existing '${VENV_DIR}'."
  else
    echo "Aborting setup to avoid overwriting your existing venv."
    exit 0
  fi
fi

echo "Creating virtual environment at '${VENV_DIR}'..."
python3 -m venv "${VENV_DIR}" || { echo "❌ Failed to create virtual environment."; exit 1; }
echo "✅ Virtual environment created."

echo "Activating virtual environment..."
# shellcheck disable=SC1090
source "${VENV_DIR}/bin/activate" || { echo "❌ Failed to activate virtual environment."; exit 1; }
echo "✅ Virtual environment activated."

echo "Upgrading pip and installing packages (pandas, streamlit)..."
pip install --upgrade pip
pip install --upgrade pandas streamlit
echo "✅ Packages installed."

print_final_instructions "venv" "${VENV_DIR}"
