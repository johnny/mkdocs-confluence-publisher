import logging
from mkdocs.structure.nav import Section
from mkdocs.structure.pages import Page
from .types import MD_to_Page, ConfluencePage

logger = logging.getLogger('mkdocs.plugins.confluence_publisher.create_pages')

class ConfluenceClient:
    def __init__(self, confluence):
        self._confluence = confluence

    def get_page_by_title(self, space_key: str, title: str):
        return self._confluence.get_page_by_title(space_key, title)

    def create_page(self, space: str, title: str, body: str, parent_id: int):
        return self._confluence.create_page(
            space=space,
            title=title,
            body=body,
            parent_id=parent_id
        )

class PageCreator:
    def __init__(self, confluence_client: ConfluenceClient, prefix: str, suffix: str, space_key: str, config=None):
        self.confluence_client = confluence_client
        self.prefix = prefix
        self.suffix = suffix
        self.space_key = space_key
        self.config = config

    def create_pages_in_space(self, items, parent_id, md_to_page: MD_to_Page):
        for item in items:
            if isinstance(item, Page) and item.title is None:
                logger.debug(f"Page title is None, attempting to read source for: {item.file.src_path}")
                if self.config:
                    item.read_source(self.config)
                    logger.debug(f"Title extracted: {item.title}")
                else:
                    logger.warning("Config not available, cannot read source to determine title.")

            page_title = f"{self.prefix}{item.title}{self.suffix}"
            logger.debug(f"Processing item: {page_title}")

            existing_page = self.confluence_client.get_page_by_title(self.space_key, page_title)

            if existing_page:
                logger.debug(f"Page already exists: {page_title}")
                page_id = existing_page['id']
            else:
                if isinstance(item, Section):
                    body = '<ac:structured-macro ac:name="children" />'
                    logger.info(f"Creating section page: {page_title}")
                else:
                    body = ""
                    logger.info(f"Creating empty page: {page_title}")

                try:
                    new_page = self.confluence_client.create_page(
                        space=self.space_key,
                        title=page_title,
                        body=body,
                        parent_id=parent_id
                    )
                    page_id = new_page['id']
                except Exception as e:
                    logger.error(f"Error creating page {page_title}: {str(e)}")
                    continue

            if isinstance(item, Page):
                md_to_page[item.file.src_path] = ConfluencePage(id=page_id, title=page_title)
                logger.debug(f"Mapped URL {item.url} to page ID {page_id}")

            if isinstance(item, Section) and item.children:
                logger.debug(f"Processing children of {page_title}")
                self.create_pages_in_space(item.children, page_id, md_to_page)
        return md_to_page

def create_pages(confluence, items, prefix, suffix, space_key, parent_id, md_to_page: MD_to_Page, config=None):
    confluence_client = ConfluenceClient(confluence)
    page_creator = PageCreator(confluence_client, prefix, suffix, space_key, config)
    return page_creator.create_pages_in_space(items, parent_id, md_to_page)