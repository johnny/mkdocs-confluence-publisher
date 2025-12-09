import logging
from typing import Dict, Any

logger = logging.getLogger('mkdocs.plugins.confluence_publisher.permissions')

def get_current_user_id(confluence) -> Dict[str, Any]:
    """
    Retrieves the current user's identification details.
    For Cloud: returns {'accountId': '...'}
    For Server: returns {'username': '...'} (or userKey)
    """
    # Try to determine if Cloud or Server from confluence object or config
    # The 'atlassian-python-api' Confluence object has 'cloud' attribute if initialized properly,
    # or we can check the URL.

    # We can try to use get_user_details_by_username with the configured username
    username = confluence.username

    try:
        user_details = confluence.get_user_details_by_username(username)
        if 'accountId' in user_details:
            return {'accountId': user_details['accountId']}
        elif 'userKey' in user_details:
             return {'userKey': user_details['userKey']}
        else:
             return {'username': username}
    except Exception as e:
        logger.warning(f"Failed to fetch user details for {username}: {e}. Falling back to username.")
        return {'username': username}

def update_page_restrictions(confluence, page_id: str, user_id_dict: Dict[str, str], restriction_type: str = 'update'):
    """
    Updates the restrictions for a page.
    Currently only supports setting 'update' (Edit) restrictions for a single user (the publisher).

    :param confluence: The Confluence object.
    :param page_id: The ID of the page.
    :param user_id_dict: A dictionary identifying the user (e.g., {'accountId': '...'} or {'username': '...'}).
    :param restriction_type: The operation to restrict (default: 'update').
    """

    # Construct the restrictions payload
    # For Cloud and Server REST API, the structure for PUT is similar

    user_entry = {"type": "known"}
    user_entry.update(user_id_dict)

    payload = {
        "operation": restriction_type,
        "restrictions": {
            "user": {
                "results": [user_entry]
            },
            "group": {
                "results": [] # Clear group restrictions to disallow others
            }
        }
    }

    # PUT /rest/api/content/{id}/restriction/byOperation/{operationKey}
    # Note: confluence.put automatically prepends 'rest/api', so we start with 'content'
    url = f"content/{page_id}/restriction/byOperation/{restriction_type}"

    try:
        logger.debug(f"Updating {restriction_type} restrictions for page {page_id} to user {user_id_dict}")
        confluence.put(url, data=payload)
        logger.info(f"Updated {restriction_type} restrictions for page {page_id}")
    except Exception as e:
        logger.error(f"Failed to update restrictions for page {page_id}: {e}")
