#!/bin/bash

# This script is used to run the example mkdocs project against the current
# development version of the mkdocs-confluence-publisher plugin.

# --- Configuration ---
# The script will automatically use a `.env` file in this directory if it exists.
ENV_FILE=".env"

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
echo "--- Running MkDocs Confluence Publisher Example ---"

# Load environment variables from .env file if it exists
if [ -f "$ENV_FILE" ]; then
  echo "Loading environment variables from ${ENV_FILE}"
  export $(cat "$ENV_FILE" | xargs)
fi

# Check for required environment variables
check_env_var "CONFLUENCE_URL"

if [ -n "${CONFLUENCE_API_TOKEN}" ]; then
  echo "Using API token mode."
elif [ -n "${CONFLUENCE_USERNAME}" ] && [ -n "${CONFLUENCE_PASSWORD}" ]; then
  echo "Using username/password mode."
elif [ -n "${CONFLUENCE_USERNAME}" ] || [ -n "${CONFLUENCE_PASSWORD}" ]; then
  echo "Error: Username/password mode requires both CONFLUENCE_USERNAME and CONFLUENCE_PASSWORD."
  echo "Please set both values in your environment or in the ${ENV_FILE} file."
  exit 1
else
  echo "Error: No credentials found."
  echo "Set CONFLUENCE_API_TOKEN for token mode,"
  echo "or both CONFLUENCE_USERNAME and CONFLUENCE_PASSWORD for username/password mode."
  exit 1
fi
check_env_var "CONFLUENCE_SPACE_KEY"
check_env_var "CONFLUENCE_PARENT_PAGE_ID"

# Install the plugin in editable mode if not already installed
if ! pip show mkdocs-confluence-publisher > /dev/null 2>&1; then
  echo "Installing the plugin in editable mode..."
  pip install -e .. > /dev/null
fi

# Run the mkdocs build
echo "Running mkdocs build..."
mkdocs build

echo "--- MkDocs build complete ---"
