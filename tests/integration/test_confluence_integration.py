import pytest
import docker
import time
import uuid
from atlassian import Confluence

# It is not feasible to retrieve an API token for a user through the Confluence API.
# Instead, this test will use password authentication to verify the new user's access.
# This is a standard and secure approach for integration testing.

@pytest.fixture(scope="module")
def confluence_service():
    """
    Provides the URL for the Confluence service, which is expected
    to be running.
    """
    return "http://localhost:8090"


def test_confluence_integration(confluence_service):
    """
    Tests the full lifecycle of creating a space, a user, and verifying access.
    """
    admin_confluence = Confluence(
        url=confluence_service,
        username="admin",
        password="admin"
    )

    # 1. Create a new space
    space_key = f"TESTSPACE{uuid.uuid4().hex.upper()[:8]}"
    space_name = "Test Space"
    admin_confluence.create_space(space_key, space_name)

    # 2. Create a new user
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    password = "testpassword"
    user_data = {
        "name": username,
        "type": "user",
        "password": {"value": password},
        "email": f"{username}@example.com",
        "displayName": f"Test User {username}",
    }
    admin_confluence.post("rest/api/user", data=user_data)
    admin_confluence.add_user_to_group(username, "confluence-users")

    # 3. Grant permissions to the user
    # Note: The 'read' permission for a space is sufficient for viewing.
    permissions_data = {
        "subjects": {
            "user": {"results": [{"type": "user", "name": username}], "size": 1}
        },
        "operations": [{"key": "read", "target": "space"}],
    }
    admin_confluence.post(f"rest/api/space/{space_key}/permission", data=permissions_data)

    # 4. Verify user access
    user_confluence = Confluence(
        url=confluence_service,
        username=username,
        password=password
    )

    # This call will fail if the user does not have access
    user_confluence.get_space(space_key)