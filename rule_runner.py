"""Rule runner for RedFlag Loop rehearsal (part 1: helpers + registry)."""
from __future__ import annotations

import re
import subprocess
import sys
import time
from dataclasses import dataclass, field

from ast_validator import THRESHOLD, validate_source, ValidationError

OVERALL_TIMEOUT_S = 2.0
PER_PROBE_BUDGET_MS = 5.0

NUMBER_WORDS = {
    "nol": "0", "kosong": "0",
    "satu": "1", "dua": "2", "tiga": "3", "empat": "4",
    "lima": "5", "enam": "6", "tujuh": "7",
    "delapan": "8", "sembilan": "9",
}

_EMOJI_MAP = {"\U0001F7E2": "ijo", "\U0001F49A": "ijo"}


@dataclass
class RuleResult:
    rule_id: str
    is_flagged: bool
    risk_score: float
    matched_evidence: list = field(default_factory=list)
    audit_reason: str = ""


def normalize_text(message: str) -> str:
    text = message[:2000]
    text = text.lower()
    for emoji, word in _EMOJI_MAP.items():
        text = text.replace(emoji, word)
    for word, digit in NUMBER_WORDS.items():
        text = re.sub(r"\b%s\b" % word, digit, text)
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r"(\d)[\s.\-_]+(\d)", r"\1\2", text)
    return text


class ActiveRulesRegistry:
    def __init__(self) -> None:
        self._history: dict[str, list[dict]] = {}

    def activate(self, rule_id: str, source: str) -> int:
        versions = self._history.setdefault(rule_id, [])
        versions.append({"source": source, "status": "active"})
        if len(versions) > 1:
            versions[-2]["status"] = "superseded"
        return len(versions)

    def rollback_rule(self, rule_id: str) -> dict:
        versions = self._history.get(rule_id)
        if not versions:
            raise KeyError("rule not found: %s" % rule_id)
        if len(versions) == 1:
            del self._history[rule_id]
            return {"rule_id": rule_id, "removed": True}
        versions.pop()
        versions[-1]["status"] = "active"
        return {"rule_id": rule_id,
                "rolled_back_to_version": len(versions)}

    def active_rules(self) -> list[str]:
        return [rid for rid, vs in self._history.items()
                if vs and vs[-1]["status"] == "active"]


def _exec_rule(rule_source):
    ns: dict = {"RuleResult": RuleResult, "normalize_text": normalize_text,
                "re": re}
    exec(compile(rule_source, "<rule>", "exec"), ns)
    return ns


def _subprocess_probe(rule_source, messages, timeout=OVERALL_TIMEOUT_S):
    driver = (
        "import json, sys, time\n"
        "_sys_path = sys.argv[3]\n"
        "sys.path.insert(0, _sys_path)\n"
        "RULE_SOURCE = open(sys.argv[1], encoding='utf-8').read()\n"
        "MSGS = json.loads(open(sys.argv[2], encoding='utf-8').read())\n"
        "from ast_validator import validate_source\n"
        "validate_source(RULE_SOURCE)\n"
        "from rule_runner import RuleResult, normalize_text\n"
        "import re as _r\n"
        "ns = {'RuleResult': RuleResult}\n"
        "ns.update({'normalize_text': normalize_text, 're': _r})\n"
        "exec(compile(RULE_SOURCE, '<rule>', 'exec'), ns)\n"
        "cands = [v for k, v in ns.items() if k.startswith('evaluate_rf_')]\n"
        "cands = [v for v in cands if callable(v)]\n"
        "assert len(cands) == 1, 'expected one evaluate_rf_* function'\n"
        "fn = cands[0]\n"
        "tests = ns.get('RULE_TESTS', {})\n"
        "pos = tests.get('positive', []); neg = tests.get('negative', [])\n"
        "p_ok = sum(1 for m in pos if fn(m).is_flagged)\n"
        "n_ok = sum(1 for m in neg if not fn(m).is_flagged)\n"
        "fn(MSGS[0])\n"
        "lats = []\n"
        "for m in MSGS:\n"
        "    t0 = time.perf_counter_ns()\n"
        "    fn(m)\n"
        "    lats.append((time.perf_counter_ns() - t0) // 1000)\n"
        "out = {'p_ok': p_ok, 'p_n': len(pos), 'n_ok': n_ok}\n"
        "out.update({'n_n': len(neg), 'lat_us': lats})\n"
        "print(json.dumps(out))\n"
    )
    import json as _json
    import os as _os
    import tempfile as _tf
    with _tf.TemporaryDirectory() as tmp:
        src = _os.path.join(tmp, "rule_patch.py")
        msg = _os.path.join(tmp, "msgs.json")
        drv = _os.path.join(tmp, "driver.py")
        with open(src, "w", encoding="utf-8") as fh:
            fh.write(rule_source)
        with open(msg, "w", encoding="utf-8") as fh:
            _json.dump(messages, fh)
        with open(drv, "w", encoding="utf-8") as fh:
            fh.write(driver)
        here = _os.path.dirname(_os.path.abspath(__file__))
        env = dict(_os.environ)
        env["PYTHONPATH"] = here + _os.pathsep + env.get("PYTHONPATH", "")
        proc = subprocess.run(
            [sys.executable, "-I", "-P", drv, src, msg, here],
            capture_output=True, text=True, timeout=timeout, cwd=here,
            env=env,
        )
    if proc.returncode != 0:
        raise RuntimeError("probe failed: %s" % proc.stderr[-2000:])
    return _json.loads(proc.stdout)
def run_rule_tests(rule_source, probe_messages=None,
                   timeout=OVERALL_TIMEOUT_S):
    validate_source(rule_source)
    ns = _exec_rule(rule_source)
    tests = ns.get("RULE_TESTS")
    if not tests or len(tests.get("positive", [])) < 5:
        raise ValidationError("RULE_TESTS needs >= 5 positive cases")
    if len(tests.get("negative", [])) < 5:
        raise ValidationError("RULE_TESTS needs >= 5 negative cases")
    probes = list(probe_messages or tests["positive"][:3]) or ["halo kak"]
    result = _subprocess_probe(rule_source, probes, timeout=timeout)
    passed = (result["p_ok"] == result["p_n"]
              and result["n_ok"] == result["n_n"])
    return {
        "positive": "%d/%d" % (result["p_ok"], result["p_n"]),
        "negative": "%d/%d" % (result["n_ok"], result["n_n"]),
        "latency_us": result["lat_us"],
        "passed": passed,
    }


def evaluate_message(rule_source, message):
    validate_source(rule_source)
    ns = _exec_rule(rule_source)
    fns = [v for k, v in ns.items() if k.startswith("evaluate_rf_")]
    fn = next(v for v in fns if callable(v))
    return fn(message)