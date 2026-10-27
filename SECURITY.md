# Security Policy

This tool runs locally, collects no data, sends nothing anywhere, and needs no API key or secret. Its only destructive action is deleting local git branches, and it is gated by a dry run by default plus a two-flag confirmation for unmerged branches.

If you find a case where it could delete a branch it should keep (for example, the current branch, or an unmerged branch without both confirmation flags), please open an issue describing the exact commands and repo state. Do not include any real secret in the report.
