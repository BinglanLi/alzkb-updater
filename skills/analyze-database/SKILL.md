---
name: analyze-database
description: Extract essential information about a biomedical database to evaluate its inclusion or to help generate a specialized database parser. Use this skill when asked to review, critique, or extract metadata for databases, including investigating their availability, update frequencies, access methods (API, FTP, web), and identifying the biomedical entities (nodes) and relationships (edges) they provide.
---

# Analyze Database

## Core Analysis Requirements

When analyzing a database, extract and explicitly document the following parameters:

- **Excerpt**: Summarize the database's purpose and major features based on published peer-reviewed papers or its official website.
- **Biomedical Content**: Identify the specific biomedical entities (node types) and biomedical relationships (edge types) provided by the source.
- **Update Frequency & Version**: Document how frequently the data is updated and the most recent version available.
- **Data Details**: Determine the underlying data format (e.g., CSV, TSV, JSON, SQL, Neo4j), data size (node and edge counts), and specific data types.
- **Access Approach**: Determine the access protocol (e.g., RESTful API, public FTP, web-based static downloads, credential-gated access).
- **Availability Validation**: Do not blindly rely on provided text assertions. Independently identify the exact downloadable dataset links and programmatically validate their availability.

## Workflow

1. **Review Source Materials**
   Read provided context documents (like update tracker spreadsheets, parser review documents) and supplement with independent searches of the database's website or peer-reviewed publications.
   
2. **Decompose Composite Databases**
   If analyzing a composite database (e.g., Hetionet), do not treat the aggregate as a single source. Investigate and separate it into its individual constituent source datasets.

3. **Validate Downloads Programmatically**
   - Identify the exact dataset download URLs or API endpoints.
   - Write and execute a lightweight script (e.g., using Python's `requests` or `urllib` libraries) to ping the endpoints.
   - Verify HTTP status codes to accurately report if the resource is freely available (200 OK), requires user credentials/login (401/403), requires API keys (400/401), or is completely inaccessible/dead (404/Connection Error).
   - Document the *tested* download links alongside the validation status.

4. **Format and Deliver**
   Compile the gathered insights into the requested format—typically a structured CSV file or a comprehensive Markdown critique document—ensuring every metric from the core requirements is addressed.
