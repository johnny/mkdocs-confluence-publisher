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

If your Confluence instance uses a self-signed certificate, you can provide a
custom CA bundle. Place a file named `custom-ca-bundle.crt` in the
`example-docs/` directory. The script will automatically detect this file and
configure Mockserver to trust the certificates contained within it.

### Replaying

To replay a previously recorded set of interactions, run the following command:

```bash
./run-replay.sh
```

This will start a Mockserver instance, load the recorded interactions from
`mockserver/expectations.json`, and then run the `mkdocs build` command
against the mocked API.

**Note:** The replay process relies on strict matching of HTTP requests. Any
changes to the documentation source files (even minor typo fixes) will result
in different HTTP request bodies (e.g., page content updates). Since these
new requests won't match the recorded expectations, the build will fail with
an HTTP 404 error from Mockserver. To fix this, you must re-record the
interactions using `./run-record.sh`.

If the replay fails, the script will automatically output the Mockserver logs.
Review these logs to identify why a request did not match the expectations.
Look for "Request not matched" messages which detail the incoming request and
the closest matching expectation. The Mockserver container will be left running
to allow further inspection.