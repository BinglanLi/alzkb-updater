---
name: parser-protocol
description: Use this when running parsers and fixing parser issues
---

<overview>
You work with parser source files and the pipeline tooling.

You are responsible for:
- Running extraction and TSV export steps
- Implementing and fixing parsers when requested
- Ensuring each parser conforms to the BaseParser contract
</overview>


<run-extraction>
## Steps
1. Verify whether the extraction is pending or failed.
2. Extract all enabled database or a single source database.
3. Export to TSV after a successful extract.
</run-extraction>


<fix-extraction>
## When extraction fails
- Check the error in the returned dict's traceback.
- If a download URL has changed, update the parser.
- If credentials are missing, stop and post feedback.
- Never modify `config/databases.yaml`.
</fix-extraction>


<baseparser-contract>
Every parser must implement:
- `download_data() -> bool`
- `parse_data() -> Dict[str, pd.DataFrame]`
- `get_schema() -> Dict[str, Dict[str, str]]`

`parse_data()` must return a non-empty dict for the step to be marked complete.
</baseparser-contract>
