"""Tests 01-09: AST safety gate (import/class/dunder/format bans)."""
import sys

sys.path.insert(0, "C:/Users/ardhy/redflag-rehearsal")

import pytest
from ast_validator import validate_source, ValidationError
from tests.conftest import (GOOD_RULE, BAD_IMPORT, BAD_EVAL, BAD_FORMAT,
                            BAD_DUNDER, BAD_CLASS, BAD_RE_ATTR)


def test_01_good_rule_passes():
    assert validate_source(GOOD_RULE) == {"ok": True}


def test_02_non_re_import_rejected():
    with pytest.raises(ValidationError, match="only 'import re'"):
        validate_source(BAD_IMPORT)


def test_03_eval_rejected():
    with pytest.raises(ValidationError, match="banned name 'eval'"):
        validate_source(BAD_EVAL)


def test_04_format_rejected():
    with pytest.raises(ValidationError, match="'.format'"):
        validate_source(BAD_FORMAT)


def test_05_dunder_literal_rejected():
    with pytest.raises(ValidationError, match="must not contain '__'"):
        validate_source(BAD_DUNDER)


def test_06_class_rejected():
    with pytest.raises(ValidationError, match="class definitions"):
        validate_source(BAD_CLASS)


def test_07_format_map_rejected():
    src = GOOD_RULE + "\nX = '{0}'.format_map({})\n"
    with pytest.raises(ValidationError, match="format_map"):
        validate_source(src)


def test_08_getattr_rejected():
    src = GOOD_RULE + "\nX = getattr(re, 'search')\n"
    with pytest.raises(ValidationError, match="banned name 'getattr'"):
        validate_source(src)


def test_09_non_whitelisted_re_attr_rejected():
    with pytest.raises(ValidationError, match="not whitelisted"):
        validate_source(BAD_RE_ATTR)
