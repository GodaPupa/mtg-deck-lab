"""Combo referee for Forge game logs (needs the patched Forge from forge/setup_forge.sh).

Forge plays every game for real: opponents attack, cast removal and counterspells. Forge's AI can't execute
loops, so the referee follows every player's battlefield from the log and awards a combo win:
  strict    - the deck starts its precombat main phase with its key card(s) and every piece of a known combo
              on the battlefield (the combo survived a full round), with at least 4 lands played;
  realistic - the combo completes during the deck's own turn (opponents already had their chance to answer
              the pieces as they were cast). Cards listed in a deck's "no_same_turn" (e.g. Glint-Horn, which
              only works while attacking) can't complete a realistic win the turn they arrive.
Otherwise Forge's real winner stands. Opponents' decisive combos (opp_combos.json) are refereed the same way.

Our decks come from decks.json; their combos come from Commander Spellbook via gsim.combo_sets.
usage: python3 referee.py <log dir> [<log dir> ...]   (prints a per-deck win-rate table)"""
import sys, re, json, glob, collections, os
_argv = sys.argv[1:]; sys.argv = ["x"]
import score2 as _S
_S.PRICE_CAP = float(os.environ.get("PRICE_CAP", "80"))  # combos with pieces up to this price count
import gsim2 as H

REG = {k: v for k, v in json.load(open("decks.json")).items() if not k.startswith("_")}
OURS, KEY, NOSAME = {}, {}, {}
def _ours(name):
    if name not in OURS and name in REG:
        OURS[name] = H.load(REG[name]["list"]); KEY[name] = REG[name]["key"]; NOSAME[name] = set(REG[name].get("no_same_turn", []))
    return name in OURS
OPP = {k: [frozenset(c) for c in v] for k, v in (json.load(open("opp_combos.json")) if os.path.exists("opp_combos.json") else {}).items()}
REF_OPP = True
PERM = re.compile(r"Resolve Stack: (.+?) - [^\n]*?\b(Creature|Artifact|Enchantment|Planeswalker|Battle)\b")

def live(d, f, lands):
    if not _ours(d):
        if not REF_OPP or d not in OPP or lands[d] < 4: return None
        for s in OPP[d]:
            if all(f[p] > 0 for p in s): return sorted(s)
        return None
    if lands[d] < 4 or not all(f[k] > 0 for k in KEY[d]): return None
    for s in OURS[d]["combos"]:
        if all(f[p] > 0 for p in s): return sorted(s)
    return None

def judged(p): return _ours(p) or p in OPP

ENGINE = re.compile(r"REFEREE COMBO WIN: Ai\(\d\)-(.+?) :: (.+?) :: round (\d+)")

def referee(chunk, winner, mode="strict"):
    m = ENGINE.search(chunk)   # patched engine already adjudicated the combo and ended the game
    if m:
        return dict(winner=m.group(1), how="combo", round=int(m.group(3)), combo=m.group(2).split(" + "))
    bf = collections.defaultdict(collections.Counter)   # player -> names on battlefield
    pending = collections.defaultdict(list)            # name -> casters of spells on the stack
    active = None; lands = collections.Counter(); rnd = collections.Counter()
    def arrived(p, n):
        if mode == "realistic" and judged(p) and p == active and n not in NOSAME.get(p, ()):
            hit = live(p, bf[p], lands)
            if hit: return dict(winner=p, how="combo", round=rnd[p], combo=hit)
    for line in chunk.splitlines():
        m = re.match(r"Turn: Turn \d+ \(Ai\(\d\)-(.+)\)", line)
        if m: rnd[m.group(1)] += 1; active = m.group(1); continue
        m = re.match(r"Land: Ai\(\d\)-(.+?) played (.+?) \(\d+\)", line)
        if m: lands[m.group(1)] += 1; bf[m.group(1)][m.group(2)] += 1; continue
        m = re.match(r"Add To Stack: Ai\(\d\)-(.+?) cast (.+)$", line)
        if m: pending[m.group(2).strip()].append(m.group(1)); continue
        m = PERM.match(line)
        if m and pending.get(m.group(1)):
            p = pending[m.group(1)].pop(0); bf[p][m.group(1)] += 1
            r = arrived(p, m.group(1))
            if r: return r
            continue
        m = re.match(r"Zone Change: ENTER Ai\(\d\)-(.+?) :: (.+?) from \w+$", line)   # patched Forge: tutored/reanimated
        if m:
            p, n = m.groups(); bf[p][n] += 1
            r = arrived(p, n)
            if r: return r
            continue
        m = re.match(r"Zone Change: (.+?) \(\d+\) was put into (\w+) from Battlefield", line)
        if m:
            n = m.group(1)
            for p in sorted(bf, key=lambda p: not _ours(p)):
                if bf[p][n] > 0: bf[p][n] -= 1; break
            continue
        m = re.match(r"Phase: Ai\(\d\)-(.+?)'s Main phase, precombat", line)
        if m and judged(m.group(1)):
            d = m.group(1); hit = live(d, bf[d], lands)
            if hit: return dict(winner=d, how="combo", round=rnd[d], combo=hit)
    return dict(winner=winner, how="forge", round=max(rnd.values()) if rnd else 0, combo=None)

def parse(path):
    txt = open(path, encoding="utf-8", errors="ignore").read()
    winners = re.findall(r"Game Result: Game \d+ ended in \d+ ms\. Ai\(\d\)-(.+?) has won", txt)
    chunks = re.split(r"Game Result: [^\n]*\n", txt)
    pod = re.search(r"#POD (.+)", txt)
    out = []
    for i, w in enumerate(winners):
        r = referee(chunks[i], w, "strict"); r2 = referee(chunks[i], w, "realistic")
        r.update(real_winner=r2["winner"], real_how=r2["how"], real_round=r2["round"], real_combo=r2["combo"],
                 file=path, game=i + 1, pod=pod.group(1) if pod else "")
        out.append(r)
    return out

def table(dirs):
    """Win rate per appearance, both referee modes."""
    res = [r for d in dirs for f in sorted(glob.glob(os.path.join(d, "*.log"))) for r in parse(f)]
    app = collections.Counter(); w = collections.Counter(); ws = collections.Counter(); cw = collections.Counter()
    for r in res:
        for s in r["pod"].split(" / "): app[s.replace("_", " ")] += 1
        w[r["real_winner"]] += 1; ws[r["winner"]] += 1
        if r["real_how"] == "combo": cw[r["real_winner"]] += 1
    print(f"{len(res)} games")
    print(f"{'deck':16} {'games':>5} {'realistic':>10} {'strict':>7} {'combo wins':>10}")
    for k in sorted(app, key=lambda k: -w[k] / app[k]):
        print(f"{k:16} {app[k]:5} {w[k] / app[k]:10.0%} {ws[k] / app[k]:7.0%} {cw[k]:10}")
    return res

if __name__ == "__main__":
    table(_argv or ["logs"])
