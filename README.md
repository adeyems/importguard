# ImportGuard

Python 3.10+ CLI for checking local synthetic CSV/JSON imports. Standard library only.

Run: `python3 importguard.py examples/schema.json examples/rows.csv --format csv`

The example reports an invalid integer and missing name. Exit codes: 0 all rows pass, 1 row errors, 2 malformed input/schema, encoding, size or access failure. Tests: `python3 -m unittest discover -s tests`.

Schema version 1 supports 1–100 fields with explicit string/integer/number/boolean types and required flags. Unknown input fields are allowed. Missing fields, JSON null and empty CSV cells count as missing; optional missing values pass. Empty JSON strings remain strings. Booleans never count as integers. CSV scalars use JSON spelling without whitespace trimming or permissive number/date inference.

Files require UTF-8 (optional BOM), at most 2 MiB each and 10000 rows. CSV headers must be distinct and nonempty, with consistent record widths. Duplicate JSON keys and non-finite constants are rejected. Row numbers count logical records excluding CSV headers. Empty datasets pass without proving completeness. Reports retain at most 1000 diagnostics with exact totals, field names and no cell values. File/schema failures deliberately use generic errors.

No source modification, database connections or network requests. Streaming, unique IDs, dates, cross-file references and review UI remain unfinished. No programme eligibility or hours claim.
