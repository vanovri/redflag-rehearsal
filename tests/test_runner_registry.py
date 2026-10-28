"""Tests 19-27: runner isolation, example rules, registry rollback."""
import sys

sys.path.insert(0, "C:/Users/ardhy/redflag-rehearsal")

import pathlib
import pytest
from ast_validator import ValidationError
from rule_runner import (ActiveRulesRegistry, evaluate_message,
                         run_rule_tests)
from tests.conftest import GOOD_RULE, FEW_TESTS, SLOW_RULE

EXAMPLES = sorted(
    (pathlib.Path("C:/Users/ardhy/redflag-rehearsal/example_rules").glob("rule_*.py")))


def test_19_good_rule_tests_pass():
    res = run_rule_tests(GOOD_RULE)
    assert res["passed"] and res["positive"] == "6/6"


def test_20_few_tests_rejected():
    with pytest.raises(ValidationError, match=">= 5"):
        run_rule_tests(FEW_TESTS)


def test_21_flagged_positive_example():
    res = evaluate_message(GOOD_RULE, "transfer aja ke 081234567890")
    assert res.is_flagged and res.risk_score >= 0.55


def test_22_legit_negative_passes():
    res = evaluate_message(GOOD_RULE, "silakan bayar via aplikasi")
    assert not res.is_flagged


def test_23_all_example_rules_pass_gates():
    for path in EXAMPLES:
        res = run_rule_tests(path.read_text(encoding="utf-8"))
        assert res["passed"], path.name


def test_24_latency_list_returned():
    res = run_rule_tests(GOOD_RULE, probe_messages=["transfer ke 0812345"])
    assert len(res["latency_us"]) == 1
    assert all(v >= 0 for v in res["latency_us"])


def test_25_slow_rule_times_out():
    with pytest.raises(Exception):
        run_rule_tests(SLOW_RULE, timeout=0.5)


def test_26_registry_rollback_to_prior():
    reg = ActiveRulesRegistry()
    reg.activate("rf_vec03_qris", "v1")
    reg.activate("rf_vec03_qris", "v2")
    out = reg.rollback_rule("rf_vec03_qris")
    assert out["rolled_back_to_version"] == 1
    assert reg.active_rules() == ["rf_vec03_qris"]


def test_27_registry_rollback_single_removes():
    reg = ActiveRulesRegistry()
    reg.activate("rf_vec01_redirect", "v1")
    out = reg.rollback_rule("rf_vec01_redirect")
    assert out["removed"] is True
    assert reg.active_rules() == []
