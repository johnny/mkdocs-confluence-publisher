## Example Project

This repository includes a sample `mkdocs` project in the `example-docs/` directory that demonstrates a wide range of features, including:

- A multi-level page structure
- Embedded images
- Internal and external links
- Code blocks

### Running the Example

To run the example project and test the development version of the plugin:

1. **Navigate to the example directory:**
   ```bash
   cd example-docs
   ```

2. **Set up your Confluence environment:**
   Create a `.env` file in the project root with your Confluence credentials:
   ```
   # Option 1: API token mode (takes precedence if set)
   CONFLUENCE_URL=<your_confluence_url>
   CONFLUENCE_API_TOKEN=<your_api_token>

   # Option 2: username/password mode
   CONFLUENCE_USERNAME=<your_username>
   # CONFLUENCE_PASSWORD=<your_password>
   ```

3. **Update `mkdocs.yml`:**
   In `example-docs/mkdocs.yml`, update the `space_key` and `parent_page_id` with your Confluence details.

4. **Run the build script:**
   ```bash
   ./run-example.sh
   ```

This will install the plugin in editable mode and build the site, publishing the content to your Confluence instance.
