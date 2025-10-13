#!/bin/bash

# This script is used to run the example mkdocs project against the current
# development version of the mkdocs-confluence-publisher plugin.
# It records all interactions with the Confluence API using Mockserver.

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
echo "--- Running MkDocs Confluence Publisher Example in Record Mode ---"

# Load environment variables from .env file if it exists
if [ -f "$ENV_FILE" ]; then
  echo "Loading environment variables from ${ENV_FILE}"
  export $(cat "$ENV_FILE" | xargs)
fi

# Check for required environment variables
check_env_var "CONFLUENCE_URL"
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

# Configure Mockserver to proxy and record
echo "Configuring Mockserver to proxy and record..."
curl -v -X PUT "http://localhost:1080/mockserver/clear?type=log"
curl -v -X PUT "http://localhost:1080/mockserver/clear?type=all"
curl -v -X PUT "http://localhost:1080/mockserver/reset"

# Install the plugin in editable mode if not already installed
if ! pip show mkdocs-confluence-publisher > /dev/null 2>&1; then
  echo "Installing the plugin in editable mode..."
  pip install -e .. > /dev/null
fi

# Run the mkdocs build, pointing to the Mockserver proxy
echo "Running mkdocs build..."
export CONFLUENCE_URL_ORIGINAL=$CONFLUENCE_URL
export CONFLUENCE_URL="http://localhost:1080"
mkdocs build

# Save the recorded expectations
echo "Saving recorded expectations to ${MOCKSERVER_EXPECTATIONS_FILE}..."
curl -v -X PUT "http://localhost:1080/mockserver/retrieve?type=recorded_expectations" > "${MOCKSERVER_EXPECTATIONS_FILE}"

# Stop Mockserver
echo "Stopping Mockserver..."
docker-compose down

echo "--- Recording complete ---"