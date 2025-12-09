import unittest
from unittest.mock import MagicMock, call, patch
from mkdocs_confluence_publisher.plugin import ConfluencePublisherPlugin
from mkdocs_confluence_publisher.permissions import update_page_restrictions

class TestProtectedMode(unittest.TestCase):
    @patch('mkdocs_confluence_publisher.plugin.Confluence')
    def test_protected_mode_enabled_cloud(self, MockConfluence):
        plugin = ConfluencePublisherPlugin()
        plugin.config = {
            'confluence_prefix': '',
            'confluence_suffix': '',
            'space_key': 'SPACE',
            'parent_page_id': '123',
            'protected_mode': True
        }

        # Setup the mock Confluence instance
        mock_confluence_instance = MockConfluence.return_value
        mock_confluence_instance.username = 'testuser'
        mock_confluence_instance.get_user_details_by_username.return_value = {'accountId': 'account-123'}

        # Mock environment variables
        import os
        with unittest.mock.patch.dict(os.environ, {
            'CONFLUENCE_URL': 'http://test',
            'CONFLUENCE_USERNAME': 'testuser',
            'CONFLUENCE_API_TOKEN': 'token'
        }):
            plugin.on_config(plugin.config)

            self.assertEqual(plugin.current_user_id, {'accountId': 'account-123'})

            # Mock update_page to avoid processing markdown
            with unittest.mock.patch('mkdocs_confluence_publisher.plugin.update_page') as mock_update_page:
                mock_update_page.return_value = []

                # Mock create_pages (via md_to_page)
                plugin.md_to_page = {'page.md': MagicMock(id='111', title='Page Title')}

                mock_page = MagicMock()
                mock_page.file.src_path = 'page.md'

                # Mock update_page_restrictions to verify call
                with unittest.mock.patch('mkdocs_confluence_publisher.plugin.update_page_restrictions') as mock_update_restrictions:
                    plugin.on_page_markdown("", mock_page, {}, {})

                    mock_update_restrictions.assert_called_once_with(
                        mock_confluence_instance, '111', {'accountId': 'account-123'}
                    )

    @patch('mkdocs_confluence_publisher.plugin.Confluence')
    def test_protected_mode_enabled_server(self, MockConfluence):
        plugin = ConfluencePublisherPlugin()
        plugin.config = {
            'confluence_prefix': '',
            'confluence_suffix': '',
            'space_key': 'SPACE',
            'parent_page_id': '123',
            'protected_mode': True
        }

        mock_confluence_instance = MockConfluence.return_value
        mock_confluence_instance.username = 'testuser'
        mock_confluence_instance.get_user_details_by_username.return_value = {'username': 'testuser', 'userKey': 'key-123'}

        import os
        with unittest.mock.patch.dict(os.environ, {
            'CONFLUENCE_URL': 'http://test',
            'CONFLUENCE_USERNAME': 'testuser',
            'CONFLUENCE_API_TOKEN': 'token'
        }):
            plugin.on_config(plugin.config)

            # Should prefer userKey if available
            self.assertEqual(plugin.current_user_id, {'userKey': 'key-123'})

            with unittest.mock.patch('mkdocs_confluence_publisher.plugin.update_page') as mock_update_page:
                mock_update_page.return_value = []
                plugin.md_to_page = {'page.md': MagicMock(id='111', title='Page Title')}
                mock_page = MagicMock()
                mock_page.file.src_path = 'page.md'

                with unittest.mock.patch('mkdocs_confluence_publisher.plugin.update_page_restrictions') as mock_update_restrictions:
                    plugin.on_page_markdown("", mock_page, {}, {})

                    mock_update_restrictions.assert_called_once_with(
                        mock_confluence_instance, '111', {'userKey': 'key-123'}
                    )

    def test_update_page_restrictions_impl(self):
        mock_confluence = MagicMock()
        update_page_restrictions(mock_confluence, '111', {'accountId': 'acc-123'})

        mock_confluence.put.assert_called_once_with(
            'content/111/restriction/byOperation/update',
            data={
                "operation": "update",
                "restrictions": {
                    "user": {
                        "results": [{"type": "known", "accountId": "acc-123"}]
                    },
                    "group": {
                        "results": []
                    }
                }
            }
        )

if __name__ == '__main__':
    unittest.main()
