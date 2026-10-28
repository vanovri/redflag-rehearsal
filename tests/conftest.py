"""Shared good/bad rule fixtures for the 27 rehearsal tests."""
import pathlib

GOOD_RULE = pathlib.Path(__file__).resolve().parent.parent.joinpath(
    "example_rules", "rule_vec03_qris.py").read_text(encoding="utf-8")

BAD_IMPORT = "import os\n" + GOOD_RULE.replace("import re", "", 1)
BAD_EVAL = GOOD_RULE + "\nX = eval('1')\n"
BAD_FORMAT = GOOD_RULE + "\nX = '{0}'.format(1)\n"
BAD_DUNDER = GOOD_RULE + "\nX = 'abc__def'\n"
BAD_CLASS = GOOD_RULE + "\nclass Foo:\n    pass\n"
BAD_LOOKAHEAD = GOOD_RULE + "\nBAD_PAT = '(?=transfer)transfer'\n"
BAD_BACKREF = GOOD_RULE + "\nBAD_PAT = '(transfer)\\\\1'\n"
BAD_RE_ATTR = GOOD_RULE + "\nX = re.match('a', 'a')\n"
FEW_TESTS = "import re\ndef evaluate_rf_x(message):\n    return RuleResult('x', True, 0.9, [], 'HIGH: t')\nRULE_TESTS = {'positive': ['a'], 'negative': ['b']}\n"
SLOW_RULE = GOOD_RULE.replace(
    "score = min(1.0, score)",
    "import time as _t\n    _t.sleep(5)\n    score = min(1.0, score)",
)
