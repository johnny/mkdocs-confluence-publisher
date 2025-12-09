#!/bin/bash

# This script is used to replay the recorded interactions between the example
# mkdocs project and the Confluence instance.

# --- Configuration ---
# The script will automatically use a `.env` file in this directory if it exists.
ENV_FILE=".env"
TAPES_DIR="tapes"
PROXAY_PORT=8082

# --- Argument Parsing ---
DEBUG_MODE=0
for arg in "$@"; do
  if [ "$arg" == "--debug" ]; then
    DEBUG_MODE=1
  fi
done

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

# Kill any existing process on the proxay port
lsof -ti:${PROXAY_PORT} | xargs kill -9 2>/dev/null || true

PROXAY_ARGS="--mode replay --port ${PROXAY_PORT} --tapes-dir ${TAPES_DIR} --exact-request-matching"
if [ $DEBUG_MODE -eq 1 ]; then
    PROXAY_ARGS="$PROXAY_ARGS --debug-matcher-fails"
fi

proxay $PROXAY_ARGS &
PROXAY_PID=$!

# Wait for proxay to start
sleep 2

# Run the mkdocs build, pointing to proxay
echo "Running mkdocs build..."
export CONFLUENCE_URL="http://localhost:${PROXAY_PORT}"
mkdocs build
MKDOCS_EXIT_CODE=$?

# Stop proxay if not in debug mode, or if build succeeded (optional, but requested behavior implies debugging failure)
if [ $DEBUG_MODE -eq 1 ] && [ $MKDOCS_EXIT_CODE -ne 0 ]; then
    echo "Build failed in debug mode. Proxay is still running with PID $PROXAY_PID."
    echo "Inspect the logs above for matcher failures."
    echo "Manually kill proxay when done: kill $PROXAY_PID"
else
    echo "Stopping proxay..."
    kill ${PROXAY_PID}
fi

echo "--- Replay complete ---"
exit $MKDOCS_EXIT_CODE