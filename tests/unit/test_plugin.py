import os
import unittest
from unittest.mock import patch

from mkdocs_confluence_publisher.plugin import ConfluencePublisherPlugin


class TestConfluencePublisherPluginConfig(unittest.TestCase):
    def test_on_config_prefers_api_token_auth(self):
        with patch('mkdocs_confluence_publisher.plugin.Confluence') as mock_confluence:
            plugin = ConfluencePublisherPlugin()
            with patch.dict(
                os.environ,
                {
                    'CONFLUENCE_URL': 'https://confluence.example.com',
                    'CONFLUENCE_API_TOKEN': 'api-token-123',
                },
                clear=True,
            ):
                plugin.on_config({})

            mock_confluence.assert_called_once_with(
                url='https://confluence.example.com',
                token='api-token-123'
            )

    def test_on_config_uses_username_password_when_api_token_and_cloud_url(self):
        with patch('mkdocs_confluence_publisher.plugin.Confluence') as mock_confluence:
            plugin = ConfluencePublisherPlugin()
            with patch.dict(
                os.environ,
                {
                    'CONFLUENCE_URL': 'https://company.atlassian.net',
                    'CONFLUENCE_API_TOKEN': 'api-token-123',
                    'CONFLUENCE_USERNAME': 'user@example.com',
                },
                clear=True,
            ):
                plugin.on_config({})

            mock_confluence.assert_called_once_with(
                url='https://company.atlassian.net',
                username='user@example.com',
                password='api-token-123'
            )
            self.assertTrue(plugin.enabled)

    def test_on_config_disables_cloud_api_token_without_username(self):
        with patch('mkdocs_confluence_publisher.plugin.Confluence') as mock_confluence:
            plugin = ConfluencePublisherPlugin()
            with patch.dict(
                os.environ,
                {
                    'CONFLUENCE_URL': 'https://company.atlassian.net',
                    'CONFLUENCE_API_TOKEN': 'api-token-123',
                },
                clear=True,
            ):
                plugin.on_config({})

            mock_confluence.assert_not_called()
            self.assertFalse(plugin.enabled)

    def test_on_config_falls_back_to_username_password(self):
        with patch('mkdocs_confluence_publisher.plugin.Confluence') as mock_confluence:
            plugin = ConfluencePublisherPlugin()
            with patch.dict(
                os.environ,
                {
                    'CONFLUENCE_URL': 'https://confluence.example.com',
                    'CONFLUENCE_USERNAME': 'user@example.com',
                    'CONFLUENCE_PASSWORD': 'super-secret',
                },
                clear=True,
            ):
                plugin.on_config({})

            mock_confluence.assert_called_once_with(
                url='https://confluence.example.com',
                username='user@example.com',
                password='super-secret'
            )

    def test_on_config_disables_when_credentials_missing(self):
        with patch('mkdocs_confluence_publisher.plugin.Confluence') as mock_confluence:
            plugin = ConfluencePublisherPlugin()
            with patch.dict(
                os.environ,
                {
                    'CONFLUENCE_URL': 'https://confluence.example.com',
                },
                clear=True,
            ):
                plugin.on_config({})

            mock_confluence.assert_not_called()
            self.assertFalse(plugin.enabled)

    def test_on_config_prefers_api_token_auth_when_both_provided(self):
        with patch('mkdocs_confluence_publisher.plugin.Confluence') as mock_confluence:
            plugin = ConfluencePublisherPlugin()
            with patch.dict(
                os.environ,
                {
                    'CONFLUENCE_URL': 'https://confluence.example.com',
                    'CONFLUENCE_API_TOKEN': 'api-token-123',
                    'CONFLUENCE_USERNAME': 'user@example.com',
                    'CONFLUENCE_PASSWORD': 'super-secret',
                },
                clear=True,
            ):
                plugin.on_config({})

            mock_confluence.assert_called_once_with(
                url='https://confluence.example.com',
                token='api-token-123'
            )
            self.assertTrue(plugin.enabled)


if __name__ == '__main__':
    unittest.main()
