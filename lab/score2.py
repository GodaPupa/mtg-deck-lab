"""Consistency score for every budget commander (and EDHTop16 partner pairs).
Score = P(a complete, affordable winning combo is among the first N cards seen), Monte Carlo.
A combo is complete if Spellbook marks it decisive, or if it is an infinite engine plus a payoff card for that engine."""
import json, re, random, collections, sys
import numpy as np

C = json.load(open("bulk/cards.json"))
V = json.load(open("bulk/variants_small.json"))
EDH = json.load(open("edh_counts.json"))
TOP = {r["name"]: r for r in json.load(open("edhtop16.json"))}
PRICE_CAP, PIECE_MV, POOL, TRIALS = 10.0, 5, 30, 3000
TABLE_ONLY = True

def budget(n, ci):
    c = C.get(n)
    return bool(c) and c["legal"] and not c["gc"] and c["usd"] is not None and c["usd"] <= PRICE_CAP and set(c["ci"]) <= set(ci)

PAYOFF = {  # engine feature keyword -> payoff cards
 "death": ["Blood Artist","Zulaport Cutthroat","Cruel Celebrant","Falkenrath Noble","Bastion of Remembrance","Vindictive Vampire",
           "Poison-Tip Archer","Marionette Apprentice","Judith, the Scourge Diva","Syr Konrad, the Grim","Pawn of Ulamog"],
 "etb":   ["Impact Tremors","Witty Roastmaster","Pandemonium","Purphoros, God of the Forge","Warstorm Surge","Reckless Fireweaver",
           "Mirkwood Bats","Blood Artist","Zulaport Cutthroat","Cruel Celebrant","Corpse Knight","Suture Priest"],
 "mana":  ["Walking Ballista","Comet Storm","Crackle with Power","Banefire","Fireball","Exsanguinate","Torment of Hailfire",
           "Debt to the Deathless","Psychosis Crawler"],
 "magecraft": ["Ral, Storm Conduit","Grapeshot","Storm-Kiln Artist","Archmage Emeritus"],
 "draw":  ["Psychosis Crawler","Laboratory Maniac","Jace, Wielder of Mysteries","Niv-Mizzet, Parun","Sheoldred, the Apocalypse"],
 "lifegain": ["Sanguine Bond","Exquisite Blood"],
 "tokens": ["Impact Tremors","Witty Roastmaster","Goblin Bombardment","Purphoros, God of the Forge","Pandemonium","Mirkwood Bats"],
}
def engine_kinds(prods):
    k = set()
    for p in prods:
        if "infinite" not in p and "near-infinite" not in p: continue
        if any(w in p for w in ("death", "sacrifice", "ltb", "dies")): k.add("death")
        if "etb" in p: k.add("etb")
        if "mana" in p: k.add("mana")
        if "magecraft" in p or "storm count" in p: k.add("magecraft")
        if "card draw" in p or "draw trigger" in p: k.add("draw")
        if "lifegain" in p: k.add("lifegain")
        if "creature tokens" in p: k.add("tokens")
    return k

def is_commander(c):
    t = c["type"]; txt = c["text"]
    return ("Legendary Creature" in t or "can be your commander" in txt) and c["legal"]

# index variants by card
by_card = collections.defaultdict(list)
for i, v in enumerate(V):
    for n in v["cards"]: by_card[n].append(i)

def score(cmds):
    """cmds: list of 1-2 commander names. Returns dict."""
    ci = "".join(sorted(set("".join(C[c]["ci"] for c in cmds))))
    cmd_mv = sum(C[c]["mv"] for c in cmds) if len(cmds) == 1 else min(C[c]["mv"] for c in cmds)
    combos = []  # list of (frozenset of pieces needed besides commanders)
    seen = set()
    for c in cmds:
        for i in by_card[c]:
            if i in seen: continue
            seen.add(i); v = V[i]
            if v["cmdr"] and not set(v["cmdr"]) <= set(cmds): continue
            others = [n for n in v["cards"] if n not in cmds]
            if not others or not all(budget(n, ci) and C[n]["mv"] <= PIECE_MV for n in others): continue
            if v["dec"]:
                single = all(("target opponent" in p or "target player" in p) for p in v["prod"] if any(w in p for w in ("lose","damage","lifeloss")))
                if not single or not TABLE_ONLY:
                    combos.append(frozenset(others)); continue
            kinds = engine_kinds(v["prod"])
            pays = {p for k in kinds for p in PAYOFF[k] if budget(p, ci) and p not in cmds}
            for p in pays: combos.append(frozenset(others) | {p})
    combos = list(set(combos))
    if not combos:
        return dict(cmds=cmds, ci=ci, combos=0, p17=0.0, p13=0.0, pieces=0)
    # choose pool: greedy by frequency, weighted toward small combos
    freq = collections.Counter()
    for s in combos:
        for n in s: freq[n] += 1.0 / len(s)
    pool = [n for n, _ in freq.most_common(POOL)]
    idx = {n: i for i, n in enumerate(pool)}
    usable = [s for s in combos if all(n in idx for n in s)]
    cost = lambda s: cmd_mv + sum(C[n]["mv"] for n in s)
    rng = np.random.default_rng(1)
    deck = np.arange(99)  # positions < len(pool) are pieces
    res = {}
    for ncards, maxmana in ((13, 7), (17, 9)):
        cs = [s for s in usable if cost(s) <= maxmana]
        if not cs: res[ncards] = 0.0; continue
        hands = np.zeros((TRIALS, len(pool)), dtype=bool)
        for t in range(TRIALS):
            drawn = rng.choice(99, size=ncards, replace=False)
            drawn = drawn[drawn < len(pool)]
            hands[t, drawn] = True
        hit = np.zeros(TRIALS, dtype=bool)
        for s in cs:
            cols = [idx[n] for n in s]
            hit |= hands[:, cols].all(axis=1)
        res[ncards] = float(hit.mean())
    return dict(cmds=cmds, ci=ci, combos=len(combos), p13=res[13], p17=res[17], pieces=len(pool),
                two=sum(1 for s in combos if len(s) == 1))

if __name__ == "__main__":
    singles = [n for n, c in C.items() if is_commander(c) and not c["gc"] and c["usd"] is not None and c["usd"] <= PRICE_CAP]
    out = []
    for n in singles:
        decks = EDH.get(n, EDH.get(C[n]["front"]))
        if decks is not None and decks >= 5000: continue
        r = score([n]); r["decks"] = decks
        t = TOP.get(n); r["e16"] = t["count"] if t else 0; r["conv"] = t["conversionRate"] if t else None
        out.append(r)
    # partner pairs seen in tournaments
    for name, t in TOP.items():
        if " / " not in name: continue
        a, b = name.split(" / ", 1)
        if a not in C or b not in C: continue
        if any(C[x]["gc"] or C[x]["usd"] is None or C[x]["usd"] > PRICE_CAP for x in (a, b)): continue
        r = score([a, b]); r["decks"] = None; r["e16"] = t["count"]; r["conv"] = t["conversionRate"]
        out.append(r)
    json.dump(out, open("scores_table.json", "w"))
    base = next(r for r in out if r["cmds"] == ["Long Feng, Grand Secretariat"])
    print("scored", len(out), "| Long Feng baseline:", base)
