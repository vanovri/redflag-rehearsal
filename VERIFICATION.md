# Local verification

Verified on 28 October 2026 using `python -m pytest tests -q` in the exported source directory.

Result: 27 tests passed. Tests exercise the AST gate, regex restrictions, text normalization, example rules, subprocess handling and rule-registry rollback.

Passing these tests does not establish operating-system sandboxing or an RE2-backed runtime. No network or external model service was involved.
