"""gsim v2: same goldfish core as gsim, plus
  1. colored mana: every land/dork/rock produces specific colors; costs need their colored pips (hybrid = either)
  2. opponent interaction: between my turns each opponent may remove my best on-board combo piece (or commander, +2 tax);
     a combo attempt can be answered unless I hold protection I can still pay for
  3. tutors that put the card on top of the library deliver it on the next draw instead of the same turn
Usage: python3 gsim2.py deck.json [deck2.json ...]"""
import json, re, random, collections, sys
sys.argv = sys.argv[:1] + [a for a in sys.argv[1:]]
_args = sys.argv[1:]; sys.argv = ["x"]
import score2 as S
import gsim as G
C = G.C
# --- role fixes over gsim v1 ---
_r1 = G.role
def role(n):
    if n in G._role: return G._role[n]
    c = C.get(n, {"type": "", "text": ""}); x = c["text"]
    if n == "Finale of Devastation": G._role[n] = "tutor"; return "tutor"
    if n == "Utopia Sprawl": G._role[n] = "rock"; return "rock"
    if "Land" in c["type"] and "Add" not in x and re.search(r"[Ss]earch your library for (a|up to two) basic land", x):
        G._role[n] = "tland"; return "tland"   # fetches deliver a tapped basic
    return _r1(n)
G.role = role
_tf = G.tutor_finds
G.tutor_finds = lambda t, p: ("Creature" in C[p]["type"]) if t == "Finale of Devastation" else _tf(t, p)
_mo = G.mana_of
G.mana_of = lambda n: 1 if re.search(r"\{1\}, \{T\}: Add", C[n]["text"]) else _mo(n)
CI_ALL = "WUBRG"

# ---------- colors ----------
def pips(n):
    """list of colored requirements (each a string of acceptable colors) + generic count"""
    cost = C[n]["cost"].split(" // ")[0]
    req, gen = [], 0
    for sym in re.findall(r"\{([^}]+)\}", cost):
        if sym.isdigit(): gen += int(sym)
        elif sym in ("X", "C"): gen += 0 if sym == "X" else 1
        elif "/P" in sym: gen += 1
        elif "/" in sym:
            a, b = sym.split("/"); req.append("".join(x for x in (a, b) if x in CI_ALL)) if not a.isdigit() else req.append(b)
        elif sym in CI_ALL: req.append(sym)
    return req, gen

_src = {}
def produces(n, ci):
    """colors one mana from this permanent can be (string); '' = colorless"""
    if n in _src: return _src[n]
    c = C.get(n, {"type": "", "text": ""}); t, x = c["type"], c["text"]
    col = set()
    for b, s in (("Plains", "W"), ("Island", "U"), ("Swamp", "B"), ("Mountain", "R"), ("Forest", "G")):
        if b in t: col.add(s)
    if re.search(r"any color|any one color|any type", x) or n == "Command Tower": col |= set(ci)
    for m in re.findall(r"Add ([^.]*)\.", x):
        col |= set(re.findall(r"\{([WUBRG])\}", m))
    if "Land" in t and re.search(r"[Ss]earch your library for (a|up to two) basic land", x): col |= set(ci)  # fetch: becomes a basic
    r = "".join(sorted(col & set(ci))) if col else ""
    _src[n] = r; return r

def can_pay(sources, req, gen):
    """sources: list of color strings. bipartite match colored pips, then generic from the rest."""
    if len(req) + gen > len(sources): return None
    order = sorted(range(len(req)), key=lambda i: len(req[i]))
    match = {}  # source idx -> pip idx
    def aug(p, seen):
        for si, s in enumerate(sources):
            if si in seen or not (set(s) & set(req[p])): continue
            seen.add(si)
            if si not in match or aug(match[si], seen):
                match[si] = p; return True
        return False
    for p in order:
        if not aug(p, set()): return None
    rest = [s for i, s in enumerate(sources) if i not in match]
    rest.sort(key=len)  # spend the least flexible first
    return rest[gen:]

def combine(cards):
    req, gen = [], 0
    for n in cards:
        r, g = pips(n); req += r; gen += g
    return req, gen

# ---------- tutor delivery ----------
def tutor_mode(t):
    x = C[t]["text"]
    if re.search(r"onto the battlefield", x): return "field"
    if re.search(r"on top", x): return "top"
    return "hand"

# ---------- the game ----------
def game(rng, b, inter):
    r_remove, p_answer, n_opp = inter
    deck = b["deck"][:]; rng.shuffle(deck); ci = b["ci"]
    cmds = b["cmds"]; tax = {c: 0 for c in cmds}
    hand = deck[:7]; lib = deck[7:]; mul = 0
    isl = lambda n: G.role(n) in ("land", "tland")
    while not (2 <= sum(map(isl, hand)) <= 5) and mul < 3:
        lib += hand; rng.shuffle(lib); hand = lib[:7]; lib = lib[7:]; mul += 1
        for _ in range(max(0, mul - 1)):
            nl = [n for n in hand if not isl(n)]
            x = max(nl, key=lambda n: C[n]["mv"]) if nl else hand[0]; hand.remove(x); lib.append(x)
    lands, rocks, dorks, dork_new, tapped_next = [], [], [], [], []
    field = set(); out = set(); combos = b["combos"]; prot = b["prot"]
    weight = collections.Counter(n for s in combos for n in s)
    for turn in range(1, 16):
        lands += tapped_next; tapped_next = []; dorks += dork_new; dork_new = []
        if turn > 1 and lib: hand.append(lib.pop(0))
        ls = [n for n in hand if isl(n)]
        if ls:
            p = next((n for n in ls if G.role(n) == "land"), ls[0]); hand.remove(p)
            (tapped_next if G.role(p) == "tland" else lands).append(produces(p, ci))
        pool = lands + dorks + rocks
        # ---- win check ----
        tut = [n for n in hand if G.role(n) == "tutor" and tutor_mode(n) != "top"]
        for s in combos:
            need = [c for c in cmds if c not in out]
            req, gen = combine(need); gen += sum(tax[c] for c in need)
            avail = list(tut); good = True
            for pc in s:
                if pc in field: continue
                if pc in hand:
                    r, g = pips(pc); req += r; gen += g; continue
                t = next((t for t in avail if G.tutor_finds(t, pc)), None)
                if not t: good = False; break
                avail.remove(t); r, g = pips(t); req += r; gen += g
                if tutor_mode(t) == "field": gen += int(C[pc]["mv"])
                else:
                    r, g = pips(pc); req += r; gen += g
            if not good or len(req) + gen > len(pool): continue
            left = can_pay(pool, req, gen)
            if left is None: continue
            # opponents get a chance to answer the combo
            answered = any(rng.random() < p_answer for _ in range(n_opp)) if p_answer else False
            if answered:
                ph = next((p for p in hand if p in prot and C[p]["mv"] <= len(left)), None)
                if ph: hand.remove(ph); return turn
                # the answer lands on the most important piece we just committed; its mana is spent
                committed = [pc for pc in s if pc not in field]
                victim = max(committed, key=lambda n: weight[n]) if committed else None
                for pc in committed:
                    if pc in hand: hand.remove(pc)
                    if pc != victim: field.add(pc)
                for c in need: out.add(c)
                pool = []; break
            return turn
        # ---- develop ----
        prog = True
        while prog and pool is not None:
            prog = False
            for n in sorted(hand, key=lambda n: ({"rock": 0, "dork": 1, "landramp": 2}.get(G.role(n), 9), C[n]["mv"])):
                r = G.role(n)
                if r not in ("rock", "dork", "landramp"): continue
                left = can_pay(pool, *pips(n))
                if left is None: continue
                pool = left; hand.remove(n)
                if r == "rock":
                    k = G.mana_of(n); src = produces(n, ci)
                    rocks += [src] * k; pool += [src] * k; field.add(n)
                elif r == "dork": dork_new.append(produces(n, ci)); field.add(n)
                else:
                    have = collections.Counter(c for s in lands + tapped_next for c in s)
                    col = "G" if "Forest card" in C[n]["text"] else min(ci, key=lambda c: have[c]) if ci else ""
                    tapped_next.append(col)
                prog = True; break
            if prog: continue
            for c in cmds:
                if c in out: continue
                r, g = pips(c); left = can_pay(pool, r, g + tax[c])
                if left is not None: pool = left; out.add(c); prog = True; break
            if prog: continue
            # top-of-library tutor: set up next turn's missing piece
            tops = [n for n in hand if G.role(n) == "tutor" and tutor_mode(n) == "top"]
            if tops:
                for s in combos:
                    miss = [pc for pc in s if pc not in field and pc not in hand]
                    if len(miss) != 1: continue
                    t = next((t for t in tops if G.tutor_finds(t, miss[0])), None)
                    if not t: continue
                    req, gen = pips(t)
                    if t == "Insatiable Avarice": gen += 2
                    left = can_pay(pool, req, gen)
                    if left is None: continue
                    pool = left; hand.remove(t); lib.insert(0, miss[0])
                    if miss[0] in lib[1:]: lib.pop(lib.index(miss[0], 1))
                    prog = True; break
                if prog: continue
            pcs = [n for n in hand if n in b["pieces"] and not ("Instant" in C[n]["type"] or "Sorcery" in C[n]["type"])]
            for n in sorted(pcs, key=lambda n: C[n]["mv"]):
                left = can_pay(pool, *pips(n))
                if left is not None: pool = left; hand.remove(n); field.add(n); prog = True; break
            if prog: continue
            cheap = [n for n in hand if G.role(n) == "other" and n not in b["pieces"] and C[n]["mv"] <= 2
                     and ("Instant" in C[n]["type"] or "Sorcery" in C[n]["type"]) and re.search(r"[Dd]raw (a|two) card", C[n]["text"])]
            for n in cheap:
                left = can_pay(pool, *pips(n))
                if left is None: continue
                pool = left; hand.remove(n)
                for _ in range(2 if "two cards" in C[n]["text"] else 1):
                    if lib: hand.append(lib.pop(0))
                prog = True; break
        # ---- opponents' turns: removal on my best piece ----
        if r_remove:
            for _ in range(n_opp):
                if rng.random() >= r_remove: continue
                cands = [(weight[n], n) for n in field if weight[n] and ("Creature" in C[n]["type"] or "Artifact" in C[n]["type"] or "Enchantment" in C[n]["type"])]
                cands += [(10 ** 6, c) for c in out]
                if not cands: continue
                _, v = max(cands)
                if v in out: out.discard(v); tax[v] += 2
                else: field.discard(v)
    return None

def run(b, games=10000, seed=5, inter=(0, 0, 3)):
    rng = random.Random(seed); w = collections.Counter(); none = 0
    for _ in range(games):
        t = game(rng, b, inter)
        if t is None: none += 1
        else: w[t] += 1
    cum = 0; rows = []
    for t in range(1, 16): cum += w[t]; rows.append(cum / games)
    med = next((i + 1 for i, c in enumerate(rows) if c >= 0.5), None)
    return dict(median=med, by7=rows[6], by10=rows[9], never=none / games, rows=rows)

def load(path, extra_swaps=()):
    d = json.load(open(path)); cm = d["Commander"]; deck = []; prot = set()
    for g, cs in d.items():
        if g == "Commander": continue
        for x in cs:
            m = re.match(r"(\d+) (.+)", x); q, n = (int(m.group(1)), m.group(2)) if m else (1, x); deck += [n] * q
            if g == "Protection": prot.add(n)
    for cut, add in extra_swaps: deck[deck.index(cut)] = add
    ci = "".join(sorted(set("".join(C[c]["ci"] for c in cm))))
    cs = G.combo_sets(cm, ci); pieces = sorted({n for s in cs for n in s if n in deck})
    return dict(cmds=cm, ci=ci, deck=deck, combos=[s for s in cs if all(n in deck for n in s)], pieces=pieces, prot=prot)

PODS = {"goldfish": (0, 0, 3), "casual": (0.10, 0.15, 3), "high power": (0.25, 0.35, 3)}
if __name__ == "__main__":
    for p in _args:
        b = load(p)
        for name, inter in PODS.items():
            r = run(b, 6000, 21, inter)
            print(f"{p:10} {name:11} median={r['median']} by7={r['by7']:.1%} by10={r['by10']:.1%} never={r['never']:.1%}", flush=True)
