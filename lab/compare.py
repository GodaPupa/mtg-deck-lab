"""Paired head-to-head between versions that played the same pods (from pods.py).
usage: python3 compare.py runs/t3/Grand_Audit runs/t3/GA_Ashnod [...]
Only pods every version finished are counted. Prints win rate with a 95% margin, and the paired
difference versus the first version (wins per pod, with its standard error)."""
import sys, os, glob, math
_argv = sys.argv[1:]; sys.argv = ["x"]
import referee as R
dirs = _argv
done = [set(os.path.basename(f) for f in glob.glob(os.path.join(d, "*.log")) if "Game Result" in open(f).read()) for d in dirs]
pods = sorted(set.intersection(*done))
names = {d: os.path.basename(d.rstrip("/")).replace("_", " ") for d in dirs}
per = {d: {p: R.parse(os.path.join(d, p)) for p in pods} for d in dirs}
print(f"{len(pods)} shared pods")
base = dirs[0]
for d in dirs:
    rs = [r for p in pods for r in per[d][p]]; n = len(rs); me = names[d]
    w = sum(r["real_winner"] == me for r in rs); s = sum(r["winner"] == me for r in rs)
    c = sum(r["real_winner"] == me and r["real_how"] == "combo" for r in rs); pr = w / n if n else 0
    line = f"{me:16} {n:3} games  realistic {pr:4.0%} ±{1.96 * math.sqrt(pr * (1 - pr) / max(n, 1)):.0%}  strict {s / max(n, 1):4.0%}  combo wins {c}"
    if d != base:
        diffs = [sum(r["real_winner"] == me for r in per[d][p]) - sum(r["real_winner"] == names[base] for r in per[base][p]) for p in pods]
        m = sum(diffs) / len(diffs); sd = (sum((x - m) ** 2 for x in diffs) / max(len(diffs) - 1, 1)) ** .5
        line += f"  | vs {names[base]}: {m:+.2f} wins/pod (se {sd / math.sqrt(len(diffs)):.2f})"
    print(line)
