#!/bin/bash

# This script is used to run the example mkdocs project against a mocked
# Confluence API. It replays all interactions from a previously recorded
# session.

# --- Configuration ---
# The script will automatically use a `.env` file in this directory if it exists.
ENV_FILE=".env"
MOCKSERVER_DIR="mockserver"
MOCKSERVER_EXPECTATIONS_FILE="${MOCKSERVER_DIR}/expectations.json"

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
echo "--- Running MkDocs Confluence Publisher Example in Replay Mode ---"

# Load environment variables from .env file if it exists
if [ -f "$ENV_FILE" ]; then
  echo "Loading environment variables from ${ENV_FILE}"
  export $(cat "$ENV_FILE" | xargs)
fi

# Check for required environment variables
check_env_var "CONFLUENCE_USERNAME"
check_env_var "CONFLUENCE_API_TOKEN"
check_env_var "CONFLUENCE_SPACE_KEY"
check_env_var "CONFLUENCE_PARENT_PAGE_ID"

# Start Mockserver
echo "Starting Mockserver..."
docker-compose up -d mockserver

# Wait for Mockserver to be ready
echo "Waiting for Mockserver to be ready..."
sleep 5

# Load the recorded expectations
echo "Loading recorded expectations from ${MOCKSERVER_EXPECTATIONS_FILE}..."
curl -v -X PUT "http://localhost:1080/mockserver/expectation" -d "@${MOCKSERVER_EXPECTATIONS_FILE}"

# Install the plugin in editable mode if not already installed
if ! pip show mkdocs-confluence-publisher > /dev/null 2>&1; then
  echo "Installing the plugin in editable mode..."
  pip install -e .. > /dev/null
fi

# Run the mkdocs build, pointing to the Mockserver
echo "Running mkdocs build..."
export CONFLUENCE_URL="http://localhost:1080"
mkdocs build

# Stop Mockserver
echo "Stopping Mockserver..."
docker-compose down

echo "--- Replay complete ---"