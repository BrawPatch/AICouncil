#!/bin/bash

# --- DevOps Automation Environment Bootstrap Script ---
# Exit immediately if a command exits with a non-zero status
set -e

# Default Parameters - Adjust configuration mappings as needed
REPO_URL="https://github.com"
PROJECT_NAME="my_project"
VENV_DIR=".venv"
SONAR_SCANNER_VER="5.0.1.3006"
SONAR_ZIP="sonar-scanner-cli-${SONAR_SCANNER_VER}-linux.zip"
SONAR_URL="https://sonarsource.com{SONAR_ZIP}"
TOOLS_DIR="$(pwd)/bin/sonar-scanner"

echo "=============================================================="
echo " 🚀 Bootstrapping DevOps QA Pipeline Environment Host..."
echo "=============================================================="

# 1. System Pre-requisite Diagnostic Assessment Checks
echo "[*] Auditing target core framework binaries..."
for cmd in git python3 pip3 node npm curl unzip; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "❌ System Error: Required structural component '$cmd' is not installed."
        echo "    Please install '$cmd' via your host package manager (apt, brew, etc.) and rerun."
        exit 1
    fi
done
echo "✔ Core system binaries discovered successfully."

# 2. Repository Infrastructure Initialization Setup
echo "[*] Synchronising repository source tracking branches..."
if [ -d "$PROJECT_NAME" ]; then
    echo "   -> Target project workspace '$PROJECT_NAME' folder already exists. Checking updates..."
    cd "$PROJECT_NAME"
    git pull origin main
else
    echo "   -> Cloner routing active. Cloning down target repo: $REPO_URL"
    git clone "$REPO_URL" "$PROJECT_NAME"
    cd "$PROJECT_NAME"
fi

# 3. Python Virtual Environment Pipeline Provisioning
echo "[*] Initializing isolated Python virtual runtime workspace..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

echo "   -> Activating local context environment variables..."
source "$VENV_DIR/bin/activate"

echo "   -> Upgrading pip package engine elements..."
pip install --upgrade pip

echo "   -> Installing foundational code assessment frameworks (Pylint)..."
pip install pylint

# 4. JavaScript/TypeScript Linting Suite Initialization
echo "[*] Setting up ecosystem linting requirements (ESLint)..."
if [ ! -f "package.json" ]; then
    echo "   -> package.json missing. Initializing root application package config..."
    npm init -y > /dev/null
fi

echo "   -> Installing structural linter components..."
npm install eslint --save-dev

# 5. SonarQube Scanner Toolchain Automation Download & Setup
echo "[*] Provisioning SonarQube static analytical engine framework..."
if [ ! -d "$TOOLS_DIR" ]; then
    echo "   -> Fetching SonarScanner binary distribution suite from Source Registry..."
    mkdir -p "$(pwd)/bin"
    
    # Download zip file safely to temporary workspace directory
    curl -sS -L "$SONAR_URL" -o "$(pwd)/bin/sonar-scanner.zip"
    
    echo "   -> Unpacking payload compression maps..."
    unzip -q "$(pwd)/bin/sonar-scanner.zip" -d "$(pwd)/bin"
    mv "$(pwd)/bin/sonar-scanner-${SONAR_SCANNER_VER}-linux" "$TOOLS_DIR"
    
    # Clean up archive payload file
    rm "$(pwd)/bin/sonar-scanner.zip"
    echo "✔ SonarScanner successfully deployed to: $TOOLS_DIR"
else
    echo "   -> Verified matching version instance of SonarScanner engine already present."
fi

# 6. Global PATH and Environment Settings Adjustments
echo "[*] Connecting tool binaries to current shell environment context..."
export PATH="$TOOLS_DIR/bin:$PATH"

# Append configuration strings out to the host setup execution trace variables
if [[ :$PATH: != *:"$TOOLS_DIR/bin":* ]]; then
    # Volatile shell environment injection for immediate pipeline execution run loops
    echo "⚠️ Pipeline Context Reminder: Please ensure to append the following path variable string"
    echo "   to your terminal system environment profile setup target rules (.bashrc / .zshrc):"
    echo "   export PATH=\"$TOOLS_DIR/bin:\$PATH\""
fi

echo "=============================================================="
echo " ✨ Bootstrap Process Complete! Workspace verified ready."
echo "     - Virtual Environment active: ($VENV_DIR)"
echo "     - Linters operational: Pylint (pip), ESLint (npm)"
echo "     - SonarScanner location: $TOOLS_DIR/bin/sonar-scanner"
echo "=============================================================="
