#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# 1. Start Confluence container
echo "Starting Confluence container..."
sudo docker compose -f tests/integration/docker-compose.yml up -d

# 2. Wait for Confluence to be ready
echo "Waiting for Confluence to be ready..."
while ! curl -s -u admin:admin http://localhost:8090/rest/api/space | grep -q '"results":'; do
  echo "Confluence is not ready yet. Retrying in 10 seconds..."
  sleep 10
done
echo "Confluence is ready."

# 3. Run tests
echo "Running integration tests..."
sudo python -m pytest tests/integration/test_confluence_integration.py

# 4. Stop and remove container
echo "Stopping and removing Confluence container..."
sudo docker compose -f tests/integration/docker-compose.yml down