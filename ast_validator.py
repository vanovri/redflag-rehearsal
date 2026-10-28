"""AST safety gate for RedFlag Loop rule patches (rehearsal).

Checks a generated rule module source before activation:
- only ``import re`` is allowed
- no class definitions, no dunder names, no '__' inside string literals
- no ``.format`` / ``format_map`` attribute access
- no dangerous names: eval, exec, open, getattr, setattr, compile,
  __import__, type
- only whitelisted ``re`` attributes may be accessed
- regex patterns must be RE2-compatible (no lookaround, no backrefs)
"""
from __future__ import annotations

import ast
import re as _re

ALLOWED_IMPORTS = {"re"}
ALLOWED_RE_ATTRS = {"compile", "search", "findall", "sub", "IGNORECASE"}
BANNED_NAMES = {
    "eval", "exec", "open", "getattr", "setattr", "compile",
    "__import__", "type",
}
BANNED_ATTRS = {"format", "format_map"}
THRESHOLD = 0.55

_RE2_LOOKAROUND = _re.compile(r"\(\?[=!<]")
_RE2_BACKREF = _re.compile(r"\\[1-9]")


def _pattern_is_re2_compatible(pattern: str) -> str | None:
    """Return a reason string when a regex pattern is not RE2-compatible."""
    if _RE2_LOOKAROUND.search(pattern):
        return "lookahead/lookbehind is not RE2-compatible"
    if _RE2_BACKREF.search(pattern):
        return "backreference is not RE2-compatible"
    return None


class ValidationError(Exception):
    pass


def validate_source(source: str) -> dict:
    """Validate rule source. Returns {'ok': True} or raises ValidationError."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ValidationError("syntax error: %s" % exc) from exc

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            raise ValidationError("class definitions are not allowed")
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name.split(".")[0] for a in node.names]
            for name in names:
                if name not in ALLOWED_IMPORTS:
                    raise ValidationError("only 'import re' is allowed, got '%s'" % name)
            if isinstance(node, ast.ImportFrom) and node.module != "re":
                raise ValidationError("only 'import re' is allowed")
        if isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            raise ValidationError("banned name '%s' is not allowed" % node.id)
        if isinstance(node, ast.Attribute):
            if node.attr in BANNED_ATTRS:
                raise ValidationError("'.%s' is not allowed" % node.attr)
            if node.attr.startswith("_"):
                raise ValidationError("private attribute '.%s' is not allowed" % node.attr)
            if isinstance(node.value, ast.Name) and node.value.id == "re":
                if node.attr not in ALLOWED_RE_ATTRS:
                    raise ValidationError(
                        "'re.%s' is not whitelisted" % node.attr
                    )
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if "__" in node.value:
                raise ValidationError("string literal must not contain '__'")
        if isinstance(node, ast.Name) and "__" in node.id:
            raise ValidationError("dunder name '%s' is not allowed" % node.id)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            reason = None
            # Only treat short literals as possible regexes when they look
            # like patterns (contain a regex metachar). Plain words such as
            # "qris" must not trip the backref check via e.g. "\b" escapes.
            val = node.value
            if _re.search(r"[\\^$.|?*+\(\)\[\]{}]", val):
                reason = _pattern_is_re2_compatible(val)
            if reason is not None:
                raise ValidationError("regex %r: %s" % (val, reason))
    return {"ok": True}


def validate_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return validate_source(fh.read())
