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

# Start Mockserver
echo "Starting Mockserver..."
# Ensure previous container is gone
docker rm -f mockserver > /dev/null 2>&1 || true

# Trap to ensure cleanup
trap "echo 'Stopping Mockserver...'; docker stop mockserver > /dev/null 2>&1" EXIT

docker run -d --rm --name mockserver \
  -p 1080:1080 \
  --env-file "$ENV_FILE" \
  mockserver/mockserver:mockserver-5.11.2 \
  -serverPort 1080

# Wait for Mockserver to be ready
echo "Waiting for Mockserver to be ready..."
until curl -s http://localhost:1080/mockserver/status > /dev/null; do
  sleep 1
done

# Load the recorded expectations
if [ ! -f "$MOCKSERVER_EXPECTATIONS_FILE" ]; then
  echo "Error: Expectations file not found at $MOCKSERVER_EXPECTATIONS_FILE"
  exit 1
fi

echo "Loading recorded expectations from ${MOCKSERVER_EXPECTATIONS_FILE}..."
curl -v -X PUT "http://localhost:1080/mockserver/expectation" -d "@${MOCKSERVER_EXPECTATIONS_FILE}"

# Install the plugin in editable mode if not already installed
if ! pip show mkdocs-confluence-publisher > /dev/null 2>&1; then
  echo "Installing the plugin in editable mode..."
  pip install -e .. > /dev/null
fi

# Run the mkdocs build, pointing to the Mockserver
echo "Running mkdocs build..."
# We append a dummy path prefix because run-record.sh uses path preservation logic
# and real Confluence often is at /wiki. However, recorded expectations contain the path.
# If we set CONFLUENCE_URL="http://localhost:1080", the plugin will use that as base.
# If expectations were recorded with /wiki/rest/api/..., we need to ensure the plugin hits that.
# In run-record.sh: export CONFLUENCE_URL="http://localhost:1080${CONF_PATH}"
# But here we don't have CONF_PATH unless we parse original URL again.
# But wait, replay doesn't talk to real confluence.
# The user's request is "Ensure that the replay fails... purely by looking into the http traffic".
# If the expectations have strict matching, we must ensure the plugin sends exact same requests.
# If the plugin is configured with `CONFLUENCE_URL` pointing to mockserver, it will construct URLs.
# If I recorded against `https://confluence.example.com/wiki`, the plugin was using that URL.
# The recorder captures path `/wiki/rest/...`.
# So when replaying, we must ensure the plugin generates `/wiki/rest/...`.
# This requires `CONFLUENCE_URL` to include `/wiki` if the original did.
# I should probably do the same URL parsing to get the path, if `CONFLUENCE_URL` is available.
# But `run-replay.sh` says it needs `CONFLUENCE_USERNAME`, `API_TOKEN` etc.
# It doesn't strictly check `CONFLUENCE_URL` in the original script, but `mkdocs` might need it or the plugin uses it.
# The original script just did `export CONFLUENCE_URL="http://localhost:1080"`.
# If `CONFLUENCE_URL` was `http://localhost:1080`, then plugin appends `/rest/api/...`.
# If the recorded path was `/wiki/rest/api/...`, then we have a mismatch if we don't include `/wiki`.
# But `run-record.sh` changes `CONFLUENCE_URL` to `http://localhost:1080` BEFORE running mkdocs?
# No, in my modified `run-record.sh`:
# `export CONFLUENCE_URL="http://localhost:1080${CONF_PATH}"`
# So `run-record.sh` DOES preserve the path.
# So `run-replay.sh` MUST also preserve the path if it wants to match the recording.
# So I should parse `CONFLUENCE_URL` here too.

# Check CONFLUENCE_URL
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

export CONFLUENCE_URL="http://localhost:1080${CONF_PATH}"
mkdocs build

echo "--- Replay complete ---"
