#!/bin/bash

# This script is used to run the example mkdocs project against a mocked
# Confluence API. It replays all interactions from a previously recorded
# session.

# --- Configuration ---
# The script will automatically use a `.env` file in this directory if it exists.
ENV_FILE=".env"
MOCKSERVER_DIR="mockserver"
MOCKSERVER_EXPECTATIONS_FILE="${MOCKSERVER_DIR}/expectations.json"
CONTAINER_NAME="mockserver"

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

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker is not running."
  exit 1
fi

# Load environment variables from .env file if it exists
if [ -f "$ENV_FILE" ]; then
  echo "Loading environment variables from ${ENV_FILE}"
  export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

# Check for required environment variables
check_env_var "CONFLUENCE_USERNAME"
check_env_var "CONFLUENCE_API_TOKEN"
check_env_var "CONFLUENCE_SPACE_KEY"
check_env_var "CONFLUENCE_PARENT_PAGE_ID"
check_env_var "CONFLUENCE_URL"

# Parse CONFLUENCE_URL to extract path
eval $(python3 -c "
import os, urllib.parse
url_str = os.environ.get('CONFLUENCE_URL')
if url_str:
    url = urllib.parse.urlparse(url_str)
    path = url.path
    print(f\"CONF_PATH='{path}'\")
")

# Start Mockserver
echo "Checking for existing Mockserver..."
STARTED_CONTAINER="false"

if [ "$(docker container inspect -f '{{.State.Running}}' "$CONTAINER_NAME" 2>/dev/null)" = "true" ]; then
  echo "Mockserver '$CONTAINER_NAME' is already running. Resetting..."
  # Reset happens via API later, but we can do a quick check here if we want
else
  echo "Starting Mockserver..."
  # Clean up stopped container if it exists
  docker rm -f "$CONTAINER_NAME" > /dev/null 2>&1 || true

  docker run -d --rm --name "$CONTAINER_NAME" \
    -p 1080:1080 \
    --env-file "$ENV_FILE" \
    mockserver/mockserver:mockserver-5.11.2 \
    -serverPort 1080

  STARTED_CONTAINER="true"
fi

# Trap to ensure cleanup ONLY if we started it
if [ "$STARTED_CONTAINER" = "true" ]; then
  trap "echo 'Stopping Mockserver...'; docker stop $CONTAINER_NAME > /dev/null 2>&1" EXIT
fi

# Wait for Mockserver to be ready
echo "Waiting for Mockserver to be ready..."
until curl -s http://localhost:1080/mockserver/status > /dev/null; do
  sleep 1
done

# Reset to clear any previous state
curl -v -X PUT "http://localhost:1080/mockserver/reset"

# Load the recorded expectations
if [ ! -f "$MOCKSERVER_EXPECTATIONS_FILE" ]; then
  echo "Error: Expectations file not found at $MOCKSERVER_EXPECTATIONS_FILE"
  exit 1
fi

echo "Loading recorded expectations from ${MOCKSERVER_EXPECTATIONS_FILE}..."
# Remove 'secure' field from expectations to ignore SSL mismatches during replay
FILTERED_EXPECTATIONS=$(mktemp)
python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        for exp in data:
            if 'httpRequest' in exp:
                exp['httpRequest'].pop('secure', None)
    elif isinstance(data, dict):
        if 'httpRequest' in data:
            data['httpRequest'].pop('secure', None)
    print(json.dumps(data))
except Exception as e:
    sys.exit(1)
" < "${MOCKSERVER_EXPECTATIONS_FILE}" > "$FILTERED_EXPECTATIONS"

if [ -s "$FILTERED_EXPECTATIONS" ]; then
  curl -v -X PUT "http://localhost:1080/mockserver/expectation" -d "@$FILTERED_EXPECTATIONS"
else
  echo "Error: Failed to process expectations file."
fi
rm "$FILTERED_EXPECTATIONS"

# Install the plugin in editable mode if not already installed
if ! pip show mkdocs-confluence-publisher > /dev/null 2>&1; then
  echo "Installing the plugin in editable mode..."
  pip install -e .. > /dev/null
fi

# Run the mkdocs build, pointing to the Mockserver
echo "Running mkdocs build..."
export CONFLUENCE_URL="http://localhost:1080${CONF_PATH}"
echo "Using CONFLUENCE_URL: $CONFLUENCE_URL"

# Run mkdocs with verbose logging and capture exit code
if ! mkdocs build -v; then
  echo "Error: mkdocs build failed."
  # Disable cleanup trap so user can inspect the running container
  trap - EXIT
  echo "Mockserver container '$CONTAINER_NAME' left running for debugging."
  echo "You can check the logs by running:"
  echo "  docker logs $CONTAINER_NAME"
  exit 1
fi

echo "--- Replay complete ---"
