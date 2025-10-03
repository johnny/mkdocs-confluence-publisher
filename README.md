# MkDocs Confluence Publisher Plugin

This MkDocs plugin automatically publishes your documentation to Confluence. It creates a hierarchical structure in Confluence that mirrors your MkDocs site structure, updates page content, and handles attachments.

## Features

- Automatically creates and updates pages in Confluence
- Maintains the hierarchy of your MkDocs site in Confluence
- Handles attachments referenced in your markdown files
- Configurable page prefix for easy identification in Confluence

## Installation

Install the plugin using pip:

```bash
pip install mkdocs-confluence-publisher
```

## Configuration

Add the following to your `mkdocs.yml`:

```yaml
plugins:
  - confluence-publisher:
      confluence_prefix: "MkDocs - "  # Optional: Prefix for page titles in Confluence
      space_key: "YOUR_SPACE_KEY"     # Required: Confluence space key
      parent_page_id: 123456          # Required: ID of the parent page in Confluence
```

## Environment Variables

The plugin requires the following environment variables to be set:

- `CONFLUENCE_URL`: The base URL of your Confluence instance
- `CONFLUENCE_USERNAME`: Your Confluence username
- `CONFLUENCE_API_TOKEN`: Your Confluence API token

You can set these in your environment or use a `.env` file.

## Usage

Once configured, the plugin will automatically publish your documentation to Confluence when you build your MkDocs site:

```bash
mkdocs build
```

## How It Works

1. **Initialization**: The plugin connects to Confluence using the provided credentials.
2. **Page Creation**: It creates a structure in Confluence mirroring your MkDocs navigation.
3. **Content Update**: As it processes each page, it updates the content in Confluence.
4. **Attachment Handling**: Any attachments referenced in your markdown are uploaded to the corresponding Confluence page.

## Logging

The plugin uses Python's logging module. You can configure logging in your `mkdocs.yml`:

```yaml
logging:
  level: INFO
```

Set to `DEBUG` for more detailed logging information.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Apache-2.0 license.
