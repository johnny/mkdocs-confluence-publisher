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
      confluence_suffix: " - MkDocs"  # Optional: Suffix for page titles in Confluence
      space_key: "YOUR_SPACE_KEY"     # Required: Confluence space key
      parent_page_id: 123456          # Required: ID of the parent page in Confluence
```

## Environment Variables

The plugin resolves credentials in this order:

1. If `CONFLUENCE_API_TOKEN` is set:
   - For Cloud Confluence (`atlassian.net` / `jira.com` URLs), set `CONFLUENCE_USERNAME`
     (typically your email) and the token is used as the password.
   - For non-cloud Confluence, `CONFLUENCE_API_TOKEN` is used as a bearer token.
2. If no API token is set, use `CONFLUENCE_USERNAME` + `CONFLUENCE_PASSWORD`.

API token mode:

- `CONFLUENCE_URL`: The base URL of your Confluence instance
- `CONFLUENCE_API_TOKEN`: Your Confluence API token
- `CONFLUENCE_USERNAME` (required only for Cloud URLs): Your Confluence username/email

Username/password mode:

- `CONFLUENCE_URL`: The base URL of your Confluence instance
- `CONFLUENCE_USERNAME`: Your Confluence username
- `CONFLUENCE_PASSWORD`: Your Confluence password

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

## Example how to start from scratch
Assuming you don't have installed mkdoc and just started to work with it.
### Installation
```bash
pip install mkdocs-confluence-publisher
pip install mkdocs
mkdocs new testFolder
cd testFolder
```
### Minimum file set
`mkdocs.yml`
```yaml
site_name: My Docs
site_url: https://someurl

nav:
  - my test: my test.md
  - Somesection:
    - test3: test3.md
    - test4: subdir/test4.md
plugins:
  - confluence-publisher:
      confluence_prefix: "MkDocs - "  # Optional: Prefix for page titles in Confluence
      space_key: "YOUR_SPACE_KEY"     # Required: Confluence space key
      parent_page_id: 123456          # Required: ID of the parent page in Confluence
```
### cd `docs` folder 
create files: `my test.md`, `test3.md`, create folder 'subdir', `subdir\test4.md`
### add some text inside created files using markdown (google mkdocs example like)

```
textTest
Paragraphs are separated by a blank line.```

### Set `Environment Variables` (check above)
```bash
mkdocs build```

## Nuances of work:
1. It doesn't delete corrsponding page if you deleted `my test.md`
2. It doesn't move page if you changed\deleted section, need delete page on adn
3. On exection without changes in file - it will update previosly updated page.  It will not touch other non changed pages/files



## License

This project is licensed under the Apache-2.0 license.
