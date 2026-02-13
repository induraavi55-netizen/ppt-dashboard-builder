import yaml
from pathlib import Path

BASE = Path(__file__).parent

_RULES = None


# --------------------------------------------------
# LOAD RULES
# --------------------------------------------------

def load_rules():
    global _RULES
    if _RULES is None:
        with open(BASE / "chart_rules.yaml") as f:
            data = yaml.safe_load(f) or {}
            _RULES = data.get("rules", [])
    return _RULES


# --------------------------------------------------
# MATCHING ENGINE
# --------------------------------------------------

def _match_value(actual, expected):

    # wildcard
    if expected == "*":
        return True

    # missing actual never matches unless wildcard
    if actual is None:
        return False

    # numeric comparisons: >3, >=2, <5, <=10
    if isinstance(expected, str):
        s = expected.strip()

        if s.startswith(">="):
            return actual >= int(s[2:])

        if s.startswith("<="):
            return actual <= int(s[2:])

        if s.startswith(">"):
            return actual > int(s[1:])

        if s.startswith("<"):
            return actual < int(s[1:])

        # not equal
        if s.startswith("!="):
            return actual != s[2:]

    # list membership
    if isinstance(expected, list):
        return actual in expected

    return actual == expected


# --------------------------------------------------
# RULE PICKER
# --------------------------------------------------

def pick_rule(profile: dict):

    for rule in load_rules():

        when = rule.get("when", {})
        ok = True

        for k, v in when.items():

            actual = profile.get(k)

            if not _match_value(actual, v):
                ok = False
                break

        if ok:
            then = rule.get("then", {})
            print(f"[VALIDATED] Rule Match: {rule.get('name', 'unnamed')} -> Chart: {then.get('chart')}")
            return then

    # safe default
    return {"chart": "column"}
