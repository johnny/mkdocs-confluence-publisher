import unittest
from unittest.mock import MagicMock, call

from mkdocs.structure.nav import Page, Section

from mkdocs_confluence_publisher.create_pages import PageCreator
from mkdocs_confluence_publisher.types import ConfluencePage


class TestCreatePages(unittest.TestCase):
    def _mock_page(self, title, src_path, is_index=False, file_name=None):
        page_file = MagicMock()
        page_file.src_path = src_path
        page_file.name = file_name if file_name is not None else src_path.rsplit('/', 1)[-1].removesuffix('.md')

        page = MagicMock(spec=Page)
        page.title = title
        page.file = page_file
        page.children = None
        page.url = src_path.replace('.md', '/')
        page.is_index = is_index
        return page

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
        mock_page.is_index = False


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

    def test_create_pages_in_space_root_index_does_not_reparent_siblings(self):
        mock_confluence_client = MagicMock()
        mock_confluence_client.get_page_by_title.return_value = None
        mock_confluence_client.create_page.side_effect = [
            {'id': '1000'},
            {'id': '2000'},
            {'id': '3000'},
        ]

        page_creator = PageCreator(
            confluence_client=mock_confluence_client,
            prefix="",
            suffix="",
            space_key="TEST"
        )
        items = [
            self._mock_page("Home", "index.md", is_index=True, file_name="index"),
            self._mock_page("Page 1", "page1.md"),
            self._mock_page("Page 2", "page2.md"),
        ]
        md_to_page = {}

        page_creator.create_pages_in_space(items, '123', md_to_page)

        mock_confluence_client.create_page.assert_has_calls([
            call(space='TEST', title='Home', body='', parent_id='123'),
            call(space='TEST', title='Page 1', body='', parent_id='123'),
            call(space='TEST', title='Page 2', body='', parent_id='123'),
        ])

    def test_create_pages_in_space_collapses_section_children_under_index(self):
        mock_confluence_client = MagicMock()
        mock_confluence_client.get_page_by_title.return_value = None
        mock_confluence_client.create_page.side_effect = [
            {'id': '9000'},
            {'id': '9001'},
            {'id': '9002'},
        ]

        page_creator = PageCreator(
            confluence_client=mock_confluence_client,
            prefix="",
            suffix="",
            space_key="TEST"
        )

        section = MagicMock(spec=Section)
        section.title = "Sub-pages"
        section.children = [
            self._mock_page("Sub-pages", "sub-pages/index.md", is_index=True, file_name="index"),
            self._mock_page("Sub-page 1", "sub-pages/sub-page1.md"),
            self._mock_page("Sub-page 2", "sub-pages/sub-page2.md"),
        ]

        page_creator.create_pages_in_space([section], '123', {})

        mock_confluence_client.create_page.assert_has_calls([
            call(space='TEST', title='Sub-pages', body='', parent_id='123'),
            call(space='TEST', title='Sub-page 1', body='', parent_id='9000'),
            call(space='TEST', title='Sub-page 2', body='', parent_id='9000'),
        ])


if __name__ == '__main__':
    unittest.main()
