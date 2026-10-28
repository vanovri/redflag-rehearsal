# RedFlag Rehearsal

Rehearsal implementation of a regex-rule evaluation workflow. It contains an AST gate, text normalization, subprocess timeouts, four example rules, and rollback support. This is distinct from vanovri/redflag-loop, which guards agent iteration state.

Install pytest in a local Python environment and run `python -m pytest tests -q`. The current suite contains 27 tests. Runtime code uses the Python standard library.

The AST gate restricts imports, attributes, and regex syntax. These checks and subprocess timeouts do not constitute an operating-system security sandbox for untrusted Python. Use only reviewed rule code in an isolated environment. RE2 compatibility checks do not mean the runtime uses an RE2 engine.

Source reconstructed from the original local rehearsal specification with AI coding assistance. Private pitch material and shared agent context are excluded.
