import os
import logging
from typing import List, Tuple
import re
import mistune
import tempfile
import hashlib
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

def normalize_indented_tables(markdown: str) -> str:
    """
    Remove leading whitespace from table lines to fix rendering issues in Confluence.
    Tables indented within lists need to be dedented for proper Confluence rendering.
    """
    lines = markdown.split('\n')
    normalized_lines = []
    in_table = False
    
    for line in lines:
        stripped = line.lstrip()
        # Detect table lines (header, separator, or data rows)
        is_table_line = stripped.startswith('|') and stripped.endswith('|')
        is_separator = is_table_line and re.match(r'^\|[\s\-:|]+\|$', stripped)
        
        if is_table_line:
            in_table = True
            # Remove leading whitespace from table lines
            normalized_lines.append(stripped)
        elif in_table and not stripped:
            # Empty line after table - end of table
            in_table = False
            normalized_lines.append(line)
        elif in_table and not is_table_line:
            # Non-table line after table started - end of table
            in_table = False
            normalized_lines.append(line)
        else:
            normalized_lines.append(line)
    
    return '\n'.join(normalized_lines)

def render_mermaid_to_image(mermaid_code: str) -> str:
    """
    Render mermaid code to an image file using mermaid-py library.
    Returns the path to the generated image file.
    """
    try:
        import mermaid as md
    except ImportError:
        logger.error("mermaid-py library not found. Install it with: pip install mermaid-py")
        return None
    
    # Create a unique filename based on the mermaid code hash
    code_hash = hashlib.md5(mermaid_code.encode()).hexdigest()
    
    # Create temporary file for output
    temp_dir = tempfile.gettempdir()
    png_file = os.path.join(temp_dir, f"mermaid_{code_hash}.png")
    
    # Check if image already exists (cached)
    if os.path.exists(png_file):
        logger.debug(f"Using cached mermaid image: {png_file}")
        return png_file
    
    try:
        # Render mermaid diagram using mermaid.compile
        # The library writes to the output file directly
        sequence = md.Mermaid(mermaid_code)
        output = sequence.to_png(png_file)
        
        if os.path.exists(png_file):
            logger.info(f"Successfully rendered mermaid diagram to {png_file}")
            return png_file
        else:
            logger.error("Failed to render mermaid diagram: output file not created")
            return None
    except Exception as e:
        logger.error(f"Error rendering mermaid diagram: {str(e)}")
        return None

def extract_heading_anchors(markdown: str) -> dict:
    """
    Extract headings from markdown and create a mapping from markdown-style anchors
    to Confluence-style anchors.
    
    Markdown converts: "Grafana (visualizations)" -> "grafana-visualizations"
    Confluence expects: "Grafana (visualizations)" -> "Grafana-(visualizations)"
    """
    anchor_map = {}
    
    # Pattern to match markdown headings
    heading_pattern = r'^#{1,6}\s+(.+)$'
    
    for match in re.finditer(heading_pattern, markdown, re.MULTILINE):
        heading_text = match.group(1).strip()
        
        # Generate markdown-style anchor (lowercase, remove only parentheses but keep content, hyphens for spaces)
        # This is what the markdown renderer actually creates
        markdown_anchor = heading_text.lower()
        # Remove just the parentheses characters, but keep the content inside
        markdown_anchor = markdown_anchor.replace('(', '').replace(')', '')
        # Remove other special characters
        markdown_anchor = re.sub(r'[^\w\s-]', '', markdown_anchor)
        # Replace spaces and multiple hyphens with single hyphen
        markdown_anchor = re.sub(r'[-\s]+', '-', markdown_anchor)
        markdown_anchor = markdown_anchor.strip('-')
        
        # Generate Confluence-style anchor (preserve case, keep parentheses, replace spaces with hyphens)
        confluence_anchor = heading_text
        # Replace spaces with hyphens but keep other characters including parentheses
        confluence_anchor = re.sub(r'\s+', '-', confluence_anchor)
        
        anchor_map[markdown_anchor] = confluence_anchor
        logger.debug(f"Heading: '{heading_text}' -> MD anchor: '{markdown_anchor}' -> Confluence anchor: '{confluence_anchor}'")
    
    return anchor_map

def convert_mermaid_to_images(content: str, attachments: List[str]) -> str:
    """
    Convert mermaid code blocks to embedded images.
    Generates image files and adds them to attachments list.
    """
    # Pattern to match mermaid code blocks
    mermaid_pattern = r'<ac:structured-macro ac:name="code"[^>]*>.*?<ac:parameter ac:name="language">mermaid</ac:parameter>.*?<ac:plain-text-body><!\[CDATA\[(.*?)\]\]></ac:plain-text-body>.*?</ac:structured-macro>'
    
    def replace_mermaid(match):
        mermaid_code = match.group(1).strip()
        
        # Render mermaid to image
        image_path = render_mermaid_to_image(mermaid_code)
        
        if image_path and os.path.exists(image_path):
            # Add to attachments list
            attachments.append(image_path)
            
            # Get filename
            filename = os.path.basename(image_path)
            
            # Create Confluence image macro
            confluence_image = f'<ac:image><ri:attachment ri:filename="{filename}" /></ac:image>'
            logger.debug(f"Converted mermaid code block to image: {filename}")
            return confluence_image
        else:
            # Fallback: keep as code block if rendering fails
            logger.warning("Failed to render mermaid diagram, keeping as code block")
            return match.group(0)
    
    content = re.sub(mermaid_pattern, replace_mermaid, content, flags=re.DOTALL)
    return content

def generate_confluence_content(markdown: str, md_to_page: MD_to_Page, page, page_anchors: dict) -> Tuple[str, List[str]]:
    # Remove HTML comments that break Confluence formatting
    markdown = re.sub(r'<!--.*?-->', '', markdown, flags=re.DOTALL)
    logger.debug("Removed HTML comments")
    
    # Normalize indented tables before processing
    markdown = normalize_indented_tables(markdown)
    logger.debug("Normalized indented tables")
    
    # Scan markdown for image tags and collect filenames
    attachments = []
    image_pattern = r'!\[.*?\]\((.*?)( \".*?\")?\)'
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
        
        # Skip external URLs (http://, https://, etc.)
        if href.startswith(('http://', 'https://', 'ftp://', '//')):
            return match.group(0)
        
        # Split href into page path and anchor (if present)
        page_path = href
        anchor = None
        if '#' in href:
            page_path, anchor = href.split('#', 1)
        
        # Check if it's a markdown link
        if page_path.endswith('.md'):
            # Resolve relative path based on current page's source path
            current_dir = os.path.dirname(page.file.src_path)
            resolved_path = os.path.normpath(os.path.join(current_dir, page_path))
            # Normalize path separators to forward slashes (consistent with MkDocs)
            resolved_path = resolved_path.replace(os.sep, '/')
            
            logger.debug(f"Resolving link: href={href}, current_dir={current_dir}, resolved_path={resolved_path}")
            logger.debug(f"Available pages in md_to_page: {list(md_to_page.keys())}")
            
            # Check if the resolved path exists in md_to_page
            if resolved_path in md_to_page:
                confluence_page = md_to_page[resolved_path]
                logger.debug(f"Replaced link to {href} (resolved to {resolved_path}) with Confluence page {confluence_page}")
                if anchor:
                    # Convert anchor using the target page's anchor map
                    confluence_anchor = anchor
                    if resolved_path in page_anchors and anchor in page_anchors[resolved_path]:
                        confluence_anchor = page_anchors[resolved_path][anchor]
                        logger.debug(f"Converted anchor '{anchor}' to '{confluence_anchor}' for target page {resolved_path}")
                    # Include anchor in the Confluence link
                    return f'<ac:link ac:anchor="{confluence_anchor}"><ri:page ri:content-title="{confluence_page.title}" /></ac:link>'
                else:
                    return f'<ac:link><ri:page ri:content-title="{confluence_page.title}" /></ac:link>'
            else:
                logger.warning(f"Could not find Confluence page for link {href} (resolved to {resolved_path})")
        return match.group(0)

    confluence_content = re.sub(r'<a (.*?)href="(.*?)"(.*?)>(.*?)</a>', replace_link, confluence_content)
    logger.debug("Fixed links to relative markdown pages")

    # Convert mermaid diagrams to images
    confluence_content = convert_mermaid_to_images(confluence_content, attachments)

    # Replace incompatible code macros
    confluence_content = replace_incompatible_macros(confluence_content)

    return confluence_content, attachments

def update_page(markdown: str, page, confluence, md_to_page: MD_to_Page, page_anchors: dict) -> List[str]:
    logger.debug(f"Starting to process page for Confluence: {page.file.src_path}")

    confluence_content, attachments = generate_confluence_content(markdown, md_to_page, page, page_anchors)

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
