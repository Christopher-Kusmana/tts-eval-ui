#!/bin/bash

# --- Environment Setup Script for Streamlit TTS Evaluation App ---

# Check if Conda is installed
echo "Checking for Conda installation..."
if ! command -v conda &> /dev/null
then
    echo "❌ Error: Conda is not found."
    echo "Please install Anaconda or Miniconda first to manage Python environments."
    echo "You can download Miniconda from: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi
echo "✅ Conda found."

# Ask for environment name
read -p "Enter the name for your new conda environment (e.g., tts_eval_env): " ENV_NAME

# Check if environment already exists
if conda env list | grep -q "\<$ENV_NAME\>"; then
    echo "⚠️ Warning: Conda environment '$ENV_NAME' already exists."
    read -p "Do you want to remove and recreate it? (y/N): " RECREATE
    if [[ "$RECREATE" =~ ^[yY]$ ]]; then
        echo "Removing existing environment '$ENV_NAME'..."
        conda env remove -y -n "$ENV_NAME" || { echo "❌ Failed to remove existing environment."; exit 1; }
        echo "✅ Existing environment removed."
    else
        echo "Aborting setup. Please choose a different name, or manually activate/manage the existing environment if you intend to use it."
        exit 0
    fi
fi

# Create new environment with Python 3.11
echo "Creating new conda environment '$ENV_NAME' with Python 3.11..."
# The 'source' command is used here for correct activation behavior in scripts
source "$(conda info --base)/etc/profile.d/conda.sh" # Initialize conda for the script
conda create -y -n "$ENV_NAME" python=3.11 || { echo "❌ Failed to create conda environment."; exit 1; }
echo "✅ Environment '$ENV_NAME' created."

# Activate the new environment temporarily for installations
echo "Activating '$ENV_NAME' for package installation..."
conda activate "$ENV_NAME" || { echo "❌ Failed to activate environment. Please check your Conda installation."; exit 1; }
echo "✅ Environment activated."

# Install required packages
echo "Installing pandas and streamlit from conda-forge into '$ENV_NAME'..."
conda install -y pandas || { echo "❌ Failed to install pandas."; exit 1; }
conda install -y -c conda-forge streamlit || { echo "❌ Failed to install streamlit. Trying pip as fallback..."; pip install --upgrade streamlit || { echo "❌ Failed to install streamlit with pip."; exit 1; }; }
echo "✅ Required packages installed."

# Final instructions
echo ""
echo "----------------------------------------------------------------------"
echo "🎉 Setup complete for your Streamlit TTS Evaluation App! 🎉"
echo "----------------------------------------------------------------------"
echo "To run the app, follow these two simple steps:"
echo ""
echo "1. Activate your environment:"
echo "   conda activate $ENV_NAME"
echo ""
echo "2. Run the Streamlit app:"
echo "   streamlit run app.py"
echo ""
echo "Don't forget to place your .wav audio files in the 'audios/' directory"
echo "(create it if it doesn't exist) and the 'logs/' directory too."
echo "Enjoy evaluating! 🎶"
echo "----------------------------------------------------------------------"