"""Run refereed four-player Forge pods.

Each pod seats every version under test against the same rivals in the same seats, so versions are compared
on identical tables (paired design). Pods are interleaved: pod i is played by every version before pod i+1,
so partial results stay comparable. Re-running the same command resumes and skips finished pods.

usage:
  python3 pods.py --versions Grand_Audit GA_Ashnod --fixed Plunder_Loop --rivals 2 --pods 14 --seed 23 --out runs/t3
    --versions  .dck names (in decks/forge) being compared; each gets its own output folder
    --fixed     decks that sit in every pod alongside the version (optional)
    --rivals    how many random opponents from opp_pool.json fill the remaining seats
    --games     games per pod (default 3); --workers parallel Forge processes (default 2; ~1 per CPU)
Then: python3 referee.py runs/t3/*  (or compare.py for a paired head-to-head)."""
import argparse, json, os, random, subprocess
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--versions", nargs="+", required=True); ap.add_argument("--fixed", nargs="*", default=[])
ap.add_argument("--rivals", type=int, default=2); ap.add_argument("--pods", type=int, default=12)
ap.add_argument("--seed", type=int, default=7); ap.add_argument("--games", type=int, default=3)
ap.add_argument("--workers", type=int, default=2); ap.add_argument("--out", required=True)
ap.add_argument("--forge", default=os.environ.get("FORGE_DIR", os.path.expanduser("~/forge")))
ap.add_argument("--timeout", type=int, default=600, help="Forge per-game time limit in seconds")
a = ap.parse_args()
JAR = os.path.join(a.forge, "forge-gui-desktop/target/forge-gui-desktop-2.0.16-SNAPSHOT-jar-with-dependencies.jar")
if not os.path.exists(JAR):
    import glob; hits = glob.glob(os.path.join(a.forge, "forge-gui-desktop/target/*jar-with-dependencies.jar")); JAR = hits[0]
pool = json.load(open(os.path.join(HERE, "opp_pool.json")))
rng = random.Random(a.seed); jobs = []
for i in range(a.pods):
    seats = ["V"] + a.fixed + rng.sample(pool, a.rivals); rng.shuffle(seats)
    for v in a.versions: jobs.append((i, [v if s == "V" else s for s in seats], os.path.join(a.out, v)))
for v in a.versions: os.makedirs(os.path.join(a.out, v), exist_ok=True)

def run(job):
    i, seats, out = job; path = os.path.join(out, f"pod{i:03d}.log")
    if os.path.exists(path) and "Game Result" in open(path).read(): return
    p = subprocess.run(["java", "-Xmx2g", "-Dfile.encoding=UTF-8", "-jar", JAR, "sim", "-d", *[s + ".dck" for s in seats],
                        "-D", os.path.join(HERE, "decks/forge"), "-f", "Commander", "-c", str(a.timeout), "-n", str(a.games)],
                       cwd=os.path.join(a.forge, "forge-gui"), capture_output=True, text=True)
    keep = [l for l in p.stdout.splitlines() if not l.lstrip().startswith("at ") and "JAVA_TOOL" not in l]
    open(path, "w").write(f"#POD {' / '.join(seats)}\n" + "\n".join(keep))
    print("done pod", i, os.path.basename(out), flush=True)

with ThreadPoolExecutor(a.workers) as ex: list(ex.map(run, jobs))
