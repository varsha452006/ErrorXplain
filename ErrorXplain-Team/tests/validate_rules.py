import json, re, pathlib

rules_path = pathlib.Path(__file__).parent.parent / "rules" / "c" / "rules.json"
tests_path = pathlib.Path(__file__).parent / "error_examples.json"

rules = json.loads(rules_path.read_text(encoding="utf-8"))
tests = json.loads(tests_path.read_text(encoding="utf-8"))

def matches(pattern, text):
    # engine: case-insensitive substring first, then regex
    lt = text.lower()
    lp = pattern.lower()
    if lp in lt:
        return True
    try:
        return re.search(pattern, text, re.IGNORECASE) is not None
    except re.error:
        return False

def first_match(text):
    for r in rules:
        for p in r["patterns"]:
            if matches(p, text):
                return r["id"]
    return None

ok = 0
for t in tests:
    got = first_match(t["error"])
    exp = t["expected_rule"]
    status = "PASS" if got == exp else "FAIL"
    if status == "PASS": ok += 1
    print(f"{status}: expected {exp}, got {got} | {t['error']}")

print(f"\n{ok}/{len(tests)} passed")
if ok != len(tests):
    exit(1)
