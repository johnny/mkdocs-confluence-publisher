import os
import posixpath
import logging
from typing import List, Tuple
import re
import mistune
from md2cf.confluence_renderer import ConfluenceRenderer
from .types import MD_to_Page, ConfluencePage

logger = logging.getLogger('mkdocs.plugins.confluence_publisher.store_page')
#logger.setLevel(logging.DEBUG)

confluence_mistune = mistune.Markdown(renderer=ConfluenceRenderer(use_xhtml=True))

# Define the replacements for incompatible code macros
MACRO_REPLACEMENTS = {
    'json': 'yaml',
    # Add more replacements here as needed
    # 'incompatible_language': 'compatible_language',
}

def replace_incompatible_macros(content: str) -> str:
    """
    Replace incompatible code macros in the content.
    """
    for incompatible, compatible in MACRO_REPLACEMENTS.items():
        pattern = f'<ac:parameter ac:name="language">{incompatible}</ac:parameter>'
        replacement = f'<ac:parameter ac:name="language">{compatible}</ac:parameter>'
        content = content.replace(pattern, replacement)

    logger.debug("Replaced incompatible code macros")
    return content

def generate_confluence_content(markdown: str, md_to_page: MD_to_Page, page) -> Tuple[str, List[str]]:
    # Scan markdown for image tags and collect filenames
    attachments = []
    image_pattern = r'!\[.*?\]\((.*?)\)'
    for match in re.finditer(image_pattern, markdown):
        image_path = match.group(1)
        logger.debug(f"Found image reference: {image_path}")
        if not image_path.startswith(('http://', 'https://')):
            full_path = os.path.join(os.path.dirname(page.file.abs_src_path), image_path)
            if os.path.exists(full_path):
                attachments.append(full_path)
                logger.debug(f"Added image to attachments list: {full_path}")
            else:
                logger.warning(f"Referenced image not found: {full_path}")

    logger.debug(f"Found {len(attachments)} image references")

    # Render markdown to Confluence storage format
    confluence_content = confluence_mistune(markdown)
    logger.debug("Converted markdown to Confluence storage format")

    # Fix links to relative markdown pages
    def replace_link(match):
        href = match.group(2)
        if href.endswith('.md'):
            if href.startswith('/'):
                target_path = href.lstrip('/')
            else:
                current_dir = posixpath.dirname(page.file.src_path)
                target_path = posixpath.normpath(posixpath.join(current_dir, href))

            if target_path in md_to_page:
                target_page = md_to_page[target_path]
                logger.debug(f"Replaced link to {href} with Confluence page {target_page}")
                return f'<ac:link><ri:page ri:content-title="{target_page.title}" /></ac:link>'
        return match.group(0)

    confluence_content = re.sub(r'<a (.*?)href="(.*?)"(.*?)>(.*?)</a>', replace_link, confluence_content)
    logger.debug("Fixed links to relative markdown pages")

    # Replace incompatible code macros
    confluence_content = replace_incompatible_macros(confluence_content)

    return confluence_content, attachments

def update_page(markdown: str, page, confluence, md_to_page: MD_to_Page) -> List[str]:
    logger.debug(f"Starting to process page for Confluence: {page.file.src_path}")

    confluence_content, attachments = generate_confluence_content(markdown, md_to_page, page)

    # Update the page content in Confluence
    confluence_page: ConfluencePage = md_to_page.get(page.file.src_path)
    if confluence_page:
        logger.debug(f"Updating Confluence page: {confluence_page.title}")
        confluence.update_page(
            page_id=confluence_page.id,
            body=confluence_content,
            title=confluence_page.title,
        )
        logger.info(f"Updated Confluence page: {confluence_page.title}")
    else:
        logger.warning(f"No Confluence page ID found for {page.file.src_path}")

    logger.debug(f"Finished processing page for Confluence: {page.file.src_path}")
    return attachments
