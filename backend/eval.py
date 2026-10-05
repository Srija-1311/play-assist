"""Eval: checks tool selection and answer correctness. Run: python eval.py"""
import re, time, unicodedata
from dotenv import load_dotenv
load_dotenv(override=True)
from agent import run_agent
from tools import init_db
import sys
RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 1

# (question, tools that must be used, regex the answer must match)
CASES = [
    ("How do I get a refund?", {"search_kb"}, r"14\s*days", r"order id|portal|business days|steam|epic|email"),
    ("What is Alex's win rate?", {"get_player_stats", "calculate"}, r"55"),
    ("What is Maya's win rate?", {"get_player_stats", "calculate"}, r"61"),
    ("What is Alex's kill/death ratio?", {"get_player_stats", "calculate"}, r"1\.4"),
    ("What is Ravi's kill/death ratio?", {"get_player_stats", "calculate"}, r"0\.8"),
    ("Who has more wins, Alex or Maya?", {"get_player_stats"}, r"maya"),
    ("Show stats for player zed", {"get_player_stats"}, r"no player|not found|couldn't find|could not find|don't have|unable"),
    ("How do I reset my password?", {"search_kb"}, r"30[\s-]*min"),
    ("Can I get a refund after 5 hours of play?", {"search_kb"}, r"\b(cannot|can't|not|no|ineligible|unable)\b"),
    ("How many matches does ranked placement take?", {"search_kb"}, r"\b10\b|\bten\b"),
    ("I keep lagging in matches, what should I try?", {"search_kb"}, r"nat|wired|restart"),
    ("What is 18% of 2450?", {"calculate"}, r"441"),
]

init_db()
passed = 0
for run in range(RUNS):
    for q, tools, pattern, *rest in CASES:
        forbid = rest[0] if rest else None
        try:
            answer, trace = run_agent([{"role": "user", "content": q}])
        except Exception as e:
            print("ERROR", q, type(e).__name__)
            continue
        used = {t["tool"] for t in trace}
        ok_tools = tools <= used
        answer = unicodedata.normalize("NFKC", answer).replace("’", "'")
        has_fact = bool(re.search(pattern, answer, re.IGNORECASE))
        has_bad = bool(forbid and re.search(forbid, answer, re.IGNORECASE))
        ok_answer = has_fact and not has_bad
        if ok_tools and ok_answer:
            passed += 1
            print("PASS", q)
        else:
            print("FAIL", q, "| tools ok:", ok_tools, "| fact found:", has_fact, "| forbidden found:", has_bad)
            print("   used:", sorted(used), "| answer:", answer[:500])
        time.sleep(1)  # avoid free-tier rate limits
    print(f"{passed}/{len(CASES)} passed")