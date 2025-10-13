#!/bin/bash

# This script is used to replay the recorded interactions between the example
# mkdocs project and the Confluence instance.

# --- Configuration ---
# The script will automatically use a `.env` file in this directory if it exists.
ENV_FILE=".env"
TAPES_DIR="tapes"
PROXAY_PORT=8082

# --- Functions ---
function check_env_var() {
  VAR_NAME=$1
  if [ -z "${!VAR_NAME}" ]; then
    echo "Error: Environment variable ${VAR_NAME} is not set."
    echo "Please set it in your environment or in the ${ENV_FILE} file."
    exit 1
  fi
}

# --- Main Script ---
echo "--- Replaying MkDocs Confluence Publisher Interactions ---"

# Load environment variables from .env file if it exists
if [ -f "$ENV_FILE" ]; then
  echo "Loading environment variables from ${ENV_FILE}"
  export $(cat "$ENV_FILE" | xargs)
fi

# Check for required environment variables
check_env_var "CONFLUENCE_SPACE_KEY"
check_env_var "CONFLUENCE_PARENT_PAGE_ID"

# These variables are not needed for replaying, but the plugin requires them to be set.
export CONFLUENCE_USERNAME="dummy"
export CONFLUENCE_API_TOKEN="dummy"

# Install the plugin in editable mode if not already installed
if ! pip show mkdocs-confluence-publisher > /dev/null 2>&1; then
  echo "Installing the plugin in editable mode..."
  pip install -e .. > /dev/null
fi

# Install proxay if not already installed
if ! npm list -g proxay > /dev/null 2>&1; then
  echo "Installing proxay..."
  npm install -g proxay > /dev/null
fi

# Start proxay in replay mode
echo "Starting proxay in replay mode..."
proxay --mode replay --port ${PROXAY_PORT} --tapes-dir ${TAPES_DIR} &
PROXAY_PID=$!

# Wait for proxay to start
sleep 2

# Run the mkdocs build, pointing to proxay
echo "Running mkdocs build..."
export CONFLUENCE_URL="http://localhost:${PROXAY_PORT}"
mkdocs build

# Stop proxay
echo "Stopping proxay..."
kill ${PROXAY_PID}

echo "--- Replay complete ---"