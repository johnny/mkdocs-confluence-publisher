import logging
import json
from typing import Dict, Any, List
from requests.exceptions import HTTPError

logger = logging.getLogger('mkdocs.plugins.confluence_publisher.permissions')

def get_current_user_id(confluence) -> Dict[str, Any]:
    """
    Retrieves the current user's identification details.
    For Cloud: returns {'accountId': '...'}
    For Server: returns {'username': '...'} (or userKey)
    """
    # Attempt to get 'current' user directly, which is more reliable for Cloud
    try:
        # Construct full URL for absolute=True
        url = confluence.url_joiner(confluence.url, "rest/api/user/current")
        current_user = confluence.get(url, absolute=True)
        if 'accountId' in current_user:
            return {'accountId': current_user['accountId']}
    except Exception as e:
        logger.debug(f"Failed to fetch current user via rest/api/user/current: {e}")

    # Fallback: Try to use get_user_details_by_username with the configured username
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

def update_page_restrictions(confluence, page_id: str, user_id_dicts: List[Dict[str, str]], restriction_type: str = 'update'):
    """
    Updates the restrictions for a page.
    Sets 'update' (Edit) restrictions for the provided users.

    :param confluence: The Confluence object.
    :param page_id: The ID of the page.
    :param user_id_dicts: A list of dictionaries identifying the users (e.g., [{'accountId': '...'}, ...]).
    :param restriction_type: The operation to restrict (default: 'update').
    """

    user_results = []
    for user_dict in user_id_dicts:
        entry = {"type": "known"}
        entry.update(user_dict)
        user_results.append(entry)

    # Payload structure for experimental/content/{id}/restriction
    # [ { "operation": "...", "restrictions": { "user": [...], "group": [...] } } ]
    payload = [
        {
            "operation": restriction_type,
            "restrictions": {
                "user": user_results,
                "group": [] # Clear group restrictions to disallow others
            }
        }
    ]

    # PUT /rest/experimental/content/{id}/restriction
    path = f"rest/experimental/content/{page_id}/restriction"
    url = confluence.url_joiner(confluence.url, path)

    try:
        logger.debug(f"Updating {restriction_type} restrictions for page {page_id} to users {user_id_dicts}")

        headers = {"Content-Type": "application/json"}
        # Serialize the payload to a JSON string because requests requires 'data' to be a string/bytes
        # when not using the 'json' parameter.

        confluence.put(url, data=json.dumps(payload), headers=headers, absolute=True)

        logger.info(f"Updated {restriction_type} restrictions for page {page_id}")
    except HTTPError as e:
        logger.error(f"Failed to update restrictions for page {page_id}. Status: {e.response.status_code}, Response: {e.response.text}")
    except Exception as e:
        logger.error(f"Failed to update restrictions for page {page_id}: {e}")
