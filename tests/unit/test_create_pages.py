import unittest
from unittest.mock import MagicMock, call

from mkdocs.structure.nav import Page, Section

from mkdocs_confluence_publisher.create_pages import PageCreator
from mkdocs_confluence_publisher.custom_types import ConfluencePage


class TestCreatePages(unittest.TestCase):
    def test_create_pages_in_space(self):
        mock_confluence_client = MagicMock()
        mock_confluence_client.get_page_by_title.return_value = None
        mock_confluence_client.create_page.side_effect = [
            {'id': '1234'},
            {'id': '5678'},
        ]

        page_creator = PageCreator(
            confluence_client=mock_confluence_client,
            prefix="PREFIX_",
            suffix="_SUFFIX",
            space_key="TEST"
        )

        mock_page_file = MagicMock()
        mock_page_file.src_path = "test.md"

        mock_page = MagicMock(spec=Page)
        mock_page.title = "Test Page"
        mock_page.file = mock_page_file
        mock_page.children = None
        mock_page.url = "test/"


        mock_section = MagicMock(spec=Section)
        mock_section.title = "Test Section"
        mock_section.children = [mock_page]

        items = [mock_section]
        md_to_page = {}

        result = page_creator.create_pages_in_space(items, '123', md_to_page)

        mock_confluence_client.get_page_by_title.assert_has_calls([
            call('TEST', 'PREFIX_Test Section_SUFFIX'),
            call('TEST', 'PREFIX_Test Page_SUFFIX'),
        ])

        mock_confluence_client.create_page.assert_has_calls([
            call(space='TEST', title='PREFIX_Test Section_SUFFIX', body='<ac:structured-macro ac:name="children" />', parent_id='123'),
            call(space='TEST', title='PREFIX_Test Page_SUFFIX', body='', parent_id='1234'),
        ])

        self.assertEqual(result, {"test.md": ConfluencePage(id='5678', title='PREFIX_Test Page_SUFFIX')})


if __name__ == '__main__':
    unittest.main()