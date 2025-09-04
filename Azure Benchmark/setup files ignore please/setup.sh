#!/usr/bin/env bash

# Exit if any command fails
set -e

echo "🚀 Setting up Azure + AWS Benchmark Project..."

# --- Python & pip check ---
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.10+ first."
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found. Please install pip for Python3."
    exit 1
fi

# --- Virtual Environment Setup ---
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment (.venv)..."
    python3 -m venv .venv
else
    echo "✔️ Virtual environment already exists."
fi

echo "📂 Activating virtual environment..."
source .venv/bin/activate

# --- Install dependencies ---
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# --- Azure CLI check ---
if ! command -v az &> /dev/null; then
    echo "⚠️ Azure CLI not found. Installing..."
    curl -sL https://aka.ms/InstallAzureCLIDeb | bash
else
    echo "✔️ Azure CLI already installed."
fi

# --- Ensure folders exist ---
echo "📂 Creating required folders..."
mkdir -p JSON-data logs Templates templates routes

# --- Reminder for Azure login ---
echo "🔑 Please run 'az login' to authenticate your Azure account if not already logged in."

echo "✅ Setup complete! You can now run:"
echo "   source .venv/bin/activate"
echo "   python app.py"
