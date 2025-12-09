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
   CONFLUENCE_URL=<your_confluence_url>
   CONFLUENCE_USERNAME=<your_username>
   CONFLUENCE_API_TOKEN=<your_api_token>
   CONFLUENCE_SPACE_KEY=<your_space_key>
   CONFLUENCE_PARENT_PAGE_ID=<your_parent_page_id>
   ```

   If your Confluence instance uses a self-signed certificate, you can also provide a path to a custom CA bundle:
   ```
   CA_BUNDLE=<path_to_ca_bundle.pem>
   ```

3. **Run the build script:**
   ```bash
   ./run-example.sh
   ```

This will install the plugin in editable mode and build the site, publishing the content to your Confluence instance.

### Recording and Replaying Interactions

For faster and more reliable testing, you can record interactions with the Confluence API and replay them locally.

#### Recording

To record the interactions:

1. **Ensure your `.env` file is configured** as described above.

2. **Run the recording script:**
   ```bash
   ./run-record.sh
   ```

This will start a proxy server, run the `mkdocs build`, and save the interactions to the `tapes/` directory.

#### Replaying

To replay the recorded interactions:

1. **Run the replaying script:**
   ```bash
   ./run-replay.sh
   ```

This will use the recorded interactions from the `tapes/` directory to run the build, without needing to connect to the actual Confluence instance. This is useful for running tests in a CI/CD environment where you may not have access to a live Confluence instance.