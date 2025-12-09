import logging
import json
from typing import Dict, Any, List

logger = logging.getLogger('mkdocs.plugins.confluence_publisher.permissions')

def get_current_user_id(confluence) -> Dict[str, Any]:
    """
    Retrieves the current user's identification details.
    For Cloud: returns {'accountId': '...'}
    For Server: returns {'username': '...'} (or userKey)
    """
    # Attempt to get 'current' user directly, which is more reliable for Cloud
    try:
        current_user = confluence.get("rest/api/user/current", absolute=True)
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
    url = f"rest/experimental/content/{page_id}/restriction"

    try:
        logger.debug(f"Updating {restriction_type} restrictions for page {page_id} to users {user_id_dicts}")
        # Serialize payload to JSON string and set content-type header
        # The atlassian-python-api put method forwards data to request, which handles json dumping if it's a dict,
        # but here we have a list, and request method logic for `data` is `data = None if not data else dumps(data)`
        # if `data` is provided. `dumps` comes from `json` usually.
        # But wait, `atlassian-python-api` source shows: `data = None if not data else dumps(data)`
        # If `dumps` is json.dumps, then list is fine.
        # However, it also sets `headers` to default. We should ensure Content-Type is application/json.

        headers = {"Content-Type": "application/json"}
        # We pass the list object directly as data. The library seems to json.dump it if it's not None.
        # But let's be explicit and pass a list, assuming library dumps it.
        # Actually, if I look closely at `request` method: `data = None if not data else dumps(data)`
        # If `dumps` is `json.dumps`, then passing a list works.
        # But to be safe and clear, and ensure headers are right:

        confluence.put(url, data=payload, headers=headers, absolute=True)

        logger.info(f"Updated {restriction_type} restrictions for page {page_id}")
    except Exception as e:
        logger.error(f"Failed to update restrictions for page {page_id}: {e}")
