# ImportGuard roadmap

Completed: local CSV/JSON validation, required fields, scalar types, bounded row diagnostics and failure tests.

Proposed next work to confirm against intended use:

- Unique IDs and cross-file references with explicit missing/duplicate rules.
- Date formats, ranges and schema versions without silent coercion.
- Streaming large files with bounded memory and failure recovery.
- Local review interface and report export.
- Packaging, workload coverage and practical documentation.

Acceptance criteria: detect concrete bad imports, identify row/field failures, preserve source files and test malformed inputs and limits. These proposals are not hours worked or guaranteed programme eligibility.
