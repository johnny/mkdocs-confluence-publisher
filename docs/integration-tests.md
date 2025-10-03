# Integration Tests

This project includes integration tests that use Docker to spin up a live Confluence instance and verify the plugin's functionality against it.

### Prerequisites

- Docker
- Docker Compose

### Running the Tests

To run the integration tests, execute the following script from the root of the repository:

```bash
./tests/integration/run_integration_tests.sh
```

The script will handle starting and stopping the Confluence container automatically.

**Note on API Tokens:** The Confluence REST API does not support the programmatic creation of API tokens for users. For this reason, the integration test uses password-based authentication to verify user access after creation.