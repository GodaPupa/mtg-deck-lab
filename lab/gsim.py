"""Generic goldfish simulator: auto-builds a budget deck for a commander (or pair) from EDHREC's average deck,
adds its best budget combo pieces, and measures the turn a table-winning combo is castable.
Same rules for every commander: generic mana, free first mulligan, on the play, no opponents."""
import json, re, random, collections, sys, time, urllib.request
sys.path.insert(0, ".")
import score2 as S   # reuse combo extraction (table-winning)

C = S.C
UA = {"User-Agent": "Mozilla/5.0 deckcheck/1.0", "Accept": "application/json"}
def slug(n):
    import unicodedata
    n = n.split(" // ")[0]; n = unicodedata.normalize("NFKD", n).encode("ascii", "ignore").decode()
    n = re.sub(r"[^a-zA-Z0-9 -]", "", n.lower()); return re.sub(r"[\s-]+", "-", n).strip("-")

def avg_deck(cmds):
    names = [slug(c) for c in cmds]
    tries = ["-".join(names), "-".join(reversed(names))] if len(names) == 2 else names
    for s in tries:
        for suffix in ("/budget", ""):
            try:
                d = json.load(urllib.request.urlopen(urllib.request.Request(f"https://json.edhrec.com/pages/average-decks/{s}{suffix}.json", headers=UA), timeout=30))
                cards = []
                for grp, lst in d["deck"]["cards"].items():
                    for n, q in lst: cards += [n] * q
                if cards: return cards, s + suffix
            except Exception:
                time.sleep(0.5)
    return [], None

def ok_card(n, ci):
    c = C.get(n)
    if not c: return False
    if "Basic Land" in c["type"]: return True
    return c["legal"] and not c["gc"] and c["usd"] is not None and c["usd"] <= S.PRICE_CAP and set(c["ci"]) <= set(ci)

def combo_sets(cmds, ci):
    """table-winning budget combo sets for these commanders (same logic as score2)."""
    combos = []; seen = set()
    for c in cmds:
        for i in S.by_card[c]:
            if i in seen: continue
            seen.add(i); v = S.V[i]
            if v["cmdr"] and not set(v["cmdr"]) <= set(cmds): continue
            others = [n for n in v["cards"] if n not in cmds]
            if not others or not all(S.budget(n, ci) and C[n]["mv"] <= S.PIECE_MV for n in others): continue
            if v["dec"]:
                single = all(("target opponent" in p or "target player" in p) for p in v["prod"] if any(w in p for w in ("lose", "damage", "lifeloss")))
                if not single: combos.append(frozenset(others)); continue
                continue
            for p in {p for k in S.engine_kinds(v["prod"]) for p in S.PAYOFF[k] if S.budget(p, ci) and p not in cmds}:
                combos.append(frozenset(others) | {p})
    return list(set(combos))

def build(cmds, max_pieces=18):
    ci = "".join(sorted(set("".join(C[c]["ci"] for c in cmds))))
    raw, src = avg_deck(cmds)
    raw = [n for n in raw if n not in cmds]
    combos = combo_sets(cmds, ci)
    freq = collections.Counter()
    for s in combos:
        for n in s: freq[n] += 1.0 / len(s)
    pieces = [n for n, _ in freq.most_common(max_pieces)]
    deck = []
    for n in raw:
        if ok_card(n, ci) and (n not in deck or "Basic Land" in C.get(n, {}).get("type", "")): deck.append(n)
    lands = [n for n in deck if "Land" in C[n]["type"] and "//" not in n]
    nonl = [n for n in deck if n not in lands]
    for p in pieces:
        if p not in nonl: nonl.append(p)
    # trim non-lands that are neither pieces nor ramp until we fit 99 with >= 34 lands
    target_lands = max(34, min(38, len(lands)))
    def is_ramp(n): return role(n) in ("rock", "dork", "landramp")
    while len(nonl) > 99 - target_lands:
        cut = next((n for n in reversed(nonl) if n not in pieces and not is_ramp(n) and role(n) != "tutor"), None) or \
              next((n for n in reversed(nonl) if n not in pieces), None)
        nonl.remove(cut)
    basics = {"W": "Plains", "U": "Island", "B": "Swamp", "R": "Mountain", "G": "Forest"}
    while len(lands) + len(nonl) < 99:
        col = ci[len(lands) % len(ci)] if ci else None
        lands.append(basics.get(col, "Wastes"))
    while len(lands) + len(nonl) > 99: lands.pop()
    return dict(cmds=cmds, ci=ci, deck=lands + nonl, combos=[s for s in combos if all(n in nonl for n in s)], src=src, pieces=pieces)

_role = {}
def role(n):
    if n in _role: return _role[n]
    c = C.get(n, {"type": "", "text": "", "mv": 0}); t = c["type"]; x = c["text"]; r = "other"
    if "Land" in t and "//" not in n: r = "tland" if re.search(r"enters( the battlefield)? tapped", x) and "unless" not in x else "land"
    elif re.search(r"\{T\}: Add", x) and "Creature" in t: r = "dork"
    elif re.search(r"\{T\}: Add", x) and "Artifact" in t: r = "rock"
    elif re.search(r"[Ss]earch your library for (a|up to (one|two)) (basic land|Forest|Plains|Island|Swamp|Mountain|land)", x) and c["mv"] <= 4 and "Land" not in t: r = "landramp"
    elif re.search(r"[Ss]earch your library for (an?|up to \w+|\w+) ((white|blue|black|red|green|nonlegendary|legendary) )?(card|cards|creature card|creature cards|artifact card|instant or sorcery card|instant card|sorcery card|enchantment card)", x): r = "tutor"
    _role[n] = r; return r

def card_colors(n):
    """actual color (not color identity): from the mana cost, colorless if Devoid"""
    c = C[n]
    if "Devoid" in (c.get("keywords") or []) or "Devoid" in c["text"].split("\n")[0]: return ""
    return "".join(sorted(set(re.findall(r"[WUBRG]", c["cost"].split(" // ")[0]))))

def tutor_finds(t, piece):
    x = C[t]["text"]; pt = C[piece]["type"]
    for col, sym in (("green", "G"), ("black", "B"), ("red", "R"), ("blue", "U"), ("white", "W")):
        if f"for a {col} creature card" in x: return "Creature" in pt and sym in card_colors(piece)
    m = re.search(r"same mana value as this card", x)
    if m: return C[piece]["mv"] == C[t]["mv"]
    if "for a card" in x or "for a card," in x: return True
    for k, w in (("creature card", "Creature"), ("artifact card", "Artifact"), ("enchantment card", "Enchantment"), ("instant or sorcery", None)):
        if k in x:
            return (w in pt) if w else ("Instant" in pt or "Sorcery" in pt)
    return False

def mana_of(n):
    x = C[n]["text"]; m = re.search(r"\{T\}: Add ((\{[^}]+\})+)", x)
    return max(1, len(re.findall(r"\{", m.group(1)))) if m else 1

def game(rng, b):
    deck = b["deck"][:]; rng.shuffle(deck)
    cmds = b["cmds"]; cmd_cost = {c: C[c]["mv"] for c in cmds}
    hand = deck[:7]; lib = deck[7:]; mul = 0
    def ok(h):
        l = sum(1 for n in h if role(n) in ("land", "tland")); return 2 <= l <= 5
    while not ok(hand) and mul < 3:
        lib += hand; rng.shuffle(lib); hand = lib[:7]; lib = lib[7:]; mul += 1
        for _ in range(max(0, mul - 1)):
            nl = [n for n in hand if role(n) not in ("land", "tland")]
            x = max(nl, key=lambda n: C[n]["mv"]) if nl else hand[0]; hand.remove(x); lib.append(x)
    field = set(); lands = 0; nxt = 0; dork = 0; dork_new = 0; rocks = 0; out = set()
    combos = b["combos"]
    for turn in range(1, 16):
        lands += nxt; nxt = 0; dork += dork_new; dork_new = 0
        if turn > 1 and lib: hand.append(lib.pop(0))
        ls = [n for n in hand if role(n) in ("land", "tland")]
        if ls:
            p = next((n for n in ls if role(n) == "land"), ls[0]); hand.remove(p)
            if role(p) == "tland": nxt += 1
            else: lands += 1
        mana = lands + dork + rocks
        # win check
        tut = [n for n in hand if role(n) == "tutor"]
        for s in combos:
            cost = sum(cmd_cost[c] for c in cmds if c not in out)
            avail = list(tut); good = True
            for pc in s:
                if pc in field: continue
                if pc in hand: cost += C[pc]["mv"]; continue
                t = next((t for t in avail if tutor_finds(t, pc)), None)
                if not t: good = False; break
                avail.remove(t); cost += C[t]["mv"] + C[pc]["mv"]
            if good and cost <= mana: return turn
        # develop
        prog = True
        while prog:
            prog = False
            for n in sorted(hand, key=lambda n: ({"rock": 0, "dork": 1, "landramp": 2}.get(role(n), 9), C[n]["mv"])):
                r = role(n)
                if r not in ("rock", "dork", "landramp") or C[n]["mv"] > mana: continue
                mana -= C[n]["mv"]; hand.remove(n)
                if r == "rock": rocks += mana_of(n); mana += mana_of(n); field.add(n)
                elif r == "dork": dork_new += 1; field.add(n)
                else: nxt += 1
                prog = True; break
            if prog: continue
            for c in cmds:
                if c not in out and cmd_cost[c] <= mana: mana -= cmd_cost[c]; out.add(c); prog = True; break
            if prog: continue
            pcs = [n for n in hand if n in b["pieces"] and not ("Instant" in C[n]["type"] or "Sorcery" in C[n]["type"]) and C[n]["mv"] <= mana]
            if pcs:
                n = min(pcs, key=lambda n: C[n]["mv"]); mana -= C[n]["mv"]; hand.remove(n); field.add(n); prog = True; continue
            cheap = [n for n in hand if role(n) == "other" and C[n]["mv"] <= min(mana, 2) and n not in b["pieces"]
                     and ("Instant" in C[n]["type"] or "Sorcery" in C[n]["type"]) and re.search(r"[Dd]raw (a|two) card", C[n]["text"])]
            if cheap:
                n = cheap[0]; mana -= C[n]["mv"]; hand.remove(n)
                for _ in range(2 if "two cards" in C[n]["text"] else 1):
                    if lib: hand.append(lib.pop(0))
                prog = True
    return None

def run(b, games=10000, seed=5):
    rng = random.Random(seed); w = collections.Counter(); none = 0
    for _ in range(games):
        t = game(rng, b)
        if t is None: none += 1
        else: w[t] += 1
    cum = 0; rows = []
    for t in range(1, 16): cum += w[t]; rows.append(cum / games)
    med = next((i + 1 for i, c in enumerate(rows) if c >= 0.5), None)
    return dict(median=med, by7=rows[6], by10=rows[9], never=none / games, rows=rows)

if __name__ == "__main__":
    finalists = json.load(open(sys.argv[1]))
    results = []
    for cmds in finalists:
        if isinstance(cmds, str) and cmds.endswith(".json"):  # hand-tuned list
            d = json.load(open(cmds)); cm = d["Commander"]
            deck = []
            for g, cs in d.items():
                if g == "Commander": continue
                for x in cs:
                    m = re.match(r"(\d+) (.+)", x); q, n = (int(m.group(1)), m.group(2)) if m else (1, x); deck += [n] * q
            ci = "".join(sorted(set("".join(C[c]["ci"] for c in cm))))
            cs = combo_sets(cm, ci); pieces = sorted({n for s in cs for n in s if n in deck})
            b = dict(cmds=cm, ci=ci, deck=deck, combos=[s for s in cs if all(n in deck for n in s)], src=cmds, pieces=pieces)
        else:
            b = build(cmds)
        r = run(b); r.update(cmds=b["cmds"], src=b["src"], ncombos=len(b["combos"]), npieces=len(b["pieces"]), decklen=len(b["deck"]))
        results.append(r)
        print(f'{" / ".join(b["cmds"])[:60]:60} src={b["src"]} combos={r["ncombos"]:4} median={r["median"]} by7={r["by7"]:.0%} by10={r["by10"]:.0%} never={r["never"]:.0%}', flush=True)
        json.dump(results, open("gsim_results.json", "w"))
