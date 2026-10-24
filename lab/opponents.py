"""Build an opponent pool from EDHREC average decks, plus each deck's decisive Commander Spellbook combos (for the referee).
usage: python3 opponents.py atraxa-praetors-voice:Atraxa krenko-mob-boss:Krenko ...
Writes decks/forge/<Label>.dck, appends labels to opp_pool.json and combos to opp_combos.json. Needs bulk/ (run fetch_data.sh)."""
import json, re, sys, time, urllib.request, os
UA = {"User-Agent": "Mozilla/5.0 deck-lab/1.0"}
C = json.load(open("bulk/cards.json")); V = json.load(open("bulk/variants_small.json"))
full = {k.split(" // ")[0]: k for k in C}
pool = json.load(open("opp_pool.json")) if os.path.exists("opp_pool.json") else []
combos = json.load(open("opp_combos.json")) if os.path.exists("opp_combos.json") else {}
for arg in sys.argv[1:]:
    slug, label = arg.split(":")
    d = json.load(urllib.request.urlopen(urllib.request.Request(f"https://json.edhrec.com/pages/average-decks/{slug}.json", headers=UA), timeout=30))
    cmd = d.get("header", "").replace(" - Average Deck", "") or None
    cards = [(n.split(" // ")[0], q) for g, l in d["deck"]["cards"].items() for n, q in l]
    names = [n for n, q in cards]
    cmdr = next((n for n in names if n.lower().replace(",", "").replace("'", "").replace(" ", "-") == slug), cards[0][0])
    main = [(n, q) for n, q in cards if n != cmdr]
    open(f"decks/forge/{label}.dck", "w").write("\n".join(["[metadata]", f"Name={label}", "[Commander]", f"1 {cmdr}", "[Main]"] + [f"{q} {n}" for n, q in main]) + "\n")
    ds = set(names); cs = set()
    for v in V:
        if not v["dec"] or len(v["cards"]) > 4: continue
        vv = [c.split(" // ")[0] for c in v["cards"]]
        if all(c in ds for c in vv) and not any(re.search(r"Instant|Sorcery", C.get(full.get(c, c), {}).get("type", "Instant")) for c in vv):
            cs.add(tuple(sorted(set(vv))))
    combos[label] = [list(c) for c in cs]
    if label not in pool: pool.append(label)
    print(label, "commander", cmdr, "cards", sum(q for n, q in main) + 1, "combos", len(cs)); time.sleep(0.5)
json.dump(pool, open("opp_pool.json", "w")); json.dump(combos, open("opp_combos.json", "w"))
