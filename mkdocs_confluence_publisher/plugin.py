import logging
import os
from dotenv import load_dotenv
from typing import List, Dict

from atlassian import Confluence
from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.nav import Page

from .create_pages import create_pages
from .update_page import update_page
from .upload_attachments import upload_attachments
from .types import MD_to_Page

class ConfluencePublisherPlugin(BasePlugin):
    config_scheme = (
        ('confluence_prefix', config_options.Type(str, default='')),
        ('confluence_suffix', config_options.Type(str, default='')),
        ('space_key', config_options.Type(str, required=True)),
        ('parent_page_id', config_options.OptionallyRequired()),
    )

    def __init__(self):
        load_dotenv()
        self.confluence = None
        self.logger = logging.getLogger('mkdocs.plugins.confluence_publisher')
        self.md_to_page: MD_to_Page = {}
        self.page_attachments: Dict[str, List[str]] = {}
        self.page_anchors: Dict[str, Dict[str, str]] = {}  # Maps page_path -> {markdown_anchor -> confluence_anchor}

    def on_config(self, config):
        if os.environ.get('CONFLUENCE_PUBLISH_DISABLED', 'false').lower() == 'true':
            self.logger.info("Confluence publish is disabled")
            self.enabled = False
            return config

        self.enabled = True
        self.logger.debug("Initializing Confluence connection")
        self.confluence = Confluence(
            url=os.environ.get('CONFLUENCE_URL'),
            username=os.environ.get('CONFLUENCE_USERNAME'),
            password=os.environ.get('CONFLUENCE_API_TOKEN')
        )
        self.logger.debug("Confluence connection initialized")
        return config

    def on_nav(self, nav, config, files):
        if not self.enabled:
            return

        prefix = self.config['confluence_prefix']
        suffix = self.config['confluence_suffix']
        space_key = self.config['space_key']
        parent_raw = self.config.get('parent_page_id')

        if not parent_raw:
            self.logger.error(
                "confluence-publisher: 'parent_page_id' is not set. "
                "Set it in mkdocs.yml or via CONFLUENCE_PARENT_PAGE_ID environment variable. "
                "The plugin will be disabled.")
            self.enabled = False
            return

        try:
            parent_page_id = int(parent_raw)
        except (TypeError, ValueError):
            self.logger.error(
                "confluence-publisher: invalid 'parent_page_id' value: %r. Must be an integer. The plugin will be disabled.",
                parent_raw)
            self.enabled = False
            return

        self.logger.info(
            f"Ensuring pages exist in Confluence with prefix '{prefix}' under parent {parent_page_id} in space: '{space_key}'")
        self.md_to_page = create_pages(self.confluence, nav.items, prefix, suffix, space_key, parent_page_id,
                                          self.md_to_page)
        self.logger.debug(f"URL to Page ID mapping: {self.md_to_page}")
        
        # Preprocess all pages to extract heading anchors
        self.logger.info("Preprocessing pages to extract heading anchors")
        from .update_page import extract_heading_anchors
        for file in files:
            if file.is_documentation_page():
                with open(file.abs_src_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
                    anchors = extract_heading_anchors(markdown_content)
                    self.page_anchors[file.src_path] = anchors
                    self.logger.debug(f"Extracted {len(anchors)} anchors from {file.src_path}")
        self.logger.info(f"Preprocessed {len(self.page_anchors)} pages for anchor resolution")

    def on_page_markdown(self, markdown, page: Page, config, files):
        if not self.enabled:
            return markdown

        self.logger.debug(f"Processing markdown for page: {page.file.src_path}")
        attachments = update_page(markdown, page, self.confluence, self.md_to_page, self.page_anchors)
        self.page_attachments[page.file.src_path] = attachments
        self.logger.debug(f"Stored page in Confluence. Attachments: {attachments}")
        return markdown

    def on_post_page(self, output, page, config):
        if not self.enabled:
            return output

        page_id = self.md_to_page.get(page.file.src_path).id
        attachments = self.page_attachments.get(page.file.src_path, [])
        self.logger.debug(f"Uploading attachments {attachments} for page: {page.file.src_path}, Page ID: {page_id}")
        upload_attachments(page_id, attachments, self.confluence, self.config['space_key'])
        self.logger.debug(f"Uploaded {len(attachments)} attachments for page: {page.file.src_path}")
        return output

    def on_post_build(self, config):
        if not self.enabled:
            return

        self.logger.info("Publish to confluence complete")
