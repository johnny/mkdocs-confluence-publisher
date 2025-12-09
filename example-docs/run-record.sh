#!/bin/bash

# This script is used to run the example mkdocs project against the current
# development version of the mkdocs-confluence-publisher plugin.
# It records all interactions with the Confluence API using Mockserver.

# --- Configuration ---
# The script will automatically use a `.env` file in this directory if it exists.
ENV_FILE=".env"
MOCKSERVER_DIR="mockserver"
MOCKSERVER_EXPECTATIONS_FILE="${MOCKSERVER_DIR}/expectations.json"
CUSTOM_CA_BUNDLE="custom-ca-bundle.crt"

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

# Check if docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker is not running."
  exit 1
fi

# Load environment variables from .env file if it exists
if [ -f "$ENV_FILE" ]; then
  echo "Loading environment variables from ${ENV_FILE}"
  # We export them so the python script can see them later
  # Using awk to avoid xargs issues with quotes/spaces if simple
  export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

# Check for required environment variables
check_env_var "CONFLUENCE_URL"
check_env_var "CONFLUENCE_USERNAME"
check_env_var "CONFLUENCE_API_TOKEN"
check_env_var "CONFLUENCE_SPACE_KEY"
check_env_var "CONFLUENCE_PARENT_PAGE_ID"

# Parse CONFLUENCE_URL to extract host, port, scheme, path
eval $(python3 -c "
import os, urllib.parse
url_str = os.environ.get('CONFLUENCE_URL')
if url_str:
    url = urllib.parse.urlparse(url_str)
    scheme = url.scheme
    host = url.hostname
    port = url.port
    path = url.path
    if port is None:
        port = 80 if scheme == 'http' else 443
    print(f\"CONF_SCHEME='{scheme.upper()}'\")
    print(f\"CONF_HOST='{host}'\")
    print(f\"CONF_PORT='{port}'\")
    print(f\"CONF_PATH='{path}'\")
")

# Start Mockserver
echo "Starting Mockserver..."
DOCKER_ARGS=""
if [ -f "$CUSTOM_CA_BUNDLE" ]; then
  echo "Detected $CUSTOM_CA_BUNDLE, configuring Mockserver to use it..."
  DOCKER_ARGS="$DOCKER_ARGS -v $(pwd)/$CUSTOM_CA_BUNDLE:/custom-ca-bundle.crt"
  DOCKER_ARGS="$DOCKER_ARGS -e MOCKSERVER_FORWARD_PROXY_TLS_X509_CERTIFICATES_TRUST_MANAGER_TYPE=CUSTOM"
  DOCKER_ARGS="$DOCKER_ARGS -e MOCKSERVER_FORWARD_PROXY_TLS_CUSTOM_TRUST_X509_CERTIFICATES=/custom-ca-bundle.crt"
fi

# Ensure previous container is gone
docker rm -f mockserver > /dev/null 2>&1 || true

# Trap to ensure cleanup
trap "echo 'Stopping Mockserver...'; docker stop mockserver > /dev/null 2>&1" EXIT

docker run -d --rm --name mockserver \
  -p 1080:1080 \
  --env-file "$ENV_FILE" \
  $DOCKER_ARGS \
  mockserver/mockserver:mockserver-5.11.2 \
  -serverPort 1080

# Wait for Mockserver to be ready
echo "Waiting for Mockserver to be ready..."
until curl -s http://localhost:1080/mockserver/status > /dev/null; do
  sleep 1
done

# Configure Mockserver to proxy and record
echo "Configuring Mockserver to proxy and record..."
curl -v -X PUT "http://localhost:1080/mockserver/clear?type=log"
curl -v -X PUT "http://localhost:1080/mockserver/clear?type=all"
curl -v -X PUT "http://localhost:1080/mockserver/reset"

# Create forwarding expectation
echo "Creating forwarding expectation to $CONF_HOST:$CONF_PORT..."
curl -v -X PUT "http://localhost:1080/mockserver/expectation" -d "{
  \"httpRequest\": {
    \"path\": \".*\"
  },
  \"httpForward\": {
    \"host\": \"$CONF_HOST\",
    \"port\": $CONF_PORT,
    \"scheme\": \"$CONF_SCHEME\"
  }
}"

# Install the plugin in editable mode if not already installed
if ! pip show mkdocs-confluence-publisher > /dev/null 2>&1; then
  echo "Installing the plugin in editable mode..."
  pip install -e .. > /dev/null
fi

# Run the mkdocs build, pointing to the Mockserver proxy
echo "Running mkdocs build..."
export CONFLUENCE_URL_ORIGINAL=$CONFLUENCE_URL
# Construct the proxy URL, keeping the original path
export CONFLUENCE_URL="http://localhost:1080${CONF_PATH}"
mkdocs build

# Save the recorded expectations
echo "Saving recorded expectations to ${MOCKSERVER_EXPECTATIONS_FILE}..."
curl -v -X PUT "http://localhost:1080/mockserver/retrieve?type=recorded_expectations" > "${MOCKSERVER_EXPECTATIONS_FILE}"

echo "--- Recording complete ---"
