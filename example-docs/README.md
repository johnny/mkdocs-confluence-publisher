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
   ```

3. **Update `mkdocs.yml`:**
   In `example-docs/mkdocs.yml`, update the `space_key` and `parent_page_id` with your Confluence details.

4. **Run the build script:**
   ```bash
   ./run-example.sh
   ```

This will install the plugin in editable mode and build the site, publishing the content to your Confluence instance.

## Recording and Replaying API Interactions

For development and testing, you can record and replay interactions with the
Confluence API using Mockserver.

### Recording

To record a new set of interactions, run the following command:

```bash
./run-record.sh
```

This will start a Mockserver instance, proxy requests to the real Confluence
API, and save the interactions to `mockserver/expectations.json`.

### Replaying

To replay a previously recorded set of interactions, run the following command:

```bash
./run-replay.sh
```

This will start a Mockserver instance, load the recorded interactions from
`mockserver/expectations.json`, and then run the `mkdocs build` command
against the mocked API.