"""Tests 10-18: RE2 compatibility + normalize_text behavior."""
import sys

sys.path.insert(0, "C:/Users/ardhy/redflag-rehearsal")

import pytest
from ast_validator import validate_source, ValidationError
from rule_runner import normalize_text
from tests.conftest import GOOD_RULE, BAD_LOOKAHEAD, BAD_BACKREF


def test_10_lookahead_rejected():
    with pytest.raises(ValidationError, match="RE2"):
        validate_source(BAD_LOOKAHEAD)


def test_11_backref_rejected():
    with pytest.raises(ValidationError, match="RE2"):
        validate_source(BAD_BACKREF)


def test_12_lookbehind_rejected():
    src = GOOD_RULE.replace("scan qr", "(?<!x)scan qr")
    with pytest.raises(ValidationError, match="RE2"):
        validate_source(src)


def test_13_plain_words_not_treated_as_regex():
    assert validate_source("X = 'qris transfer'\n") == {"ok": True}


def test_14_number_words_mapped():
    out = normalize_text("0812 tiga empat lima")
    assert "0812345" in out.replace(" ", "")


def test_15_digits_separators_collapsed():
    assert normalize_text("0812-3456 7890") == "081234567890"


def test_16_emoji_mapped():
    assert "ijo" in normalize_text("stok hijau \U0001F7E2 ready")


def test_17_truncation_to_2000():
    assert len(normalize_text("x" * 5000)) == 2000


def test_18_lowercase_applied():
    assert normalize_text("TRANSFER QRIS") == "transfer qris"
