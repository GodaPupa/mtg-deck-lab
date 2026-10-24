"""Convert a grouped JSON decklist into a Forge .dck file.
usage: python3 make_dck.py decks/lists/lf_ash.json "GA Ashnod" --keycards "Basking Broodscale;Viscera Seer;Blood Artist"
The JSON is {"Commander": [...], "<group>": ["Card", "10 Forest", ...], ...}."""
import json, re, argparse
ap = argparse.ArgumentParser(); ap.add_argument("list"); ap.add_argument("name"); ap.add_argument("--keycards", default="")
ap.add_argument("--out", default=None); a = ap.parse_args()
d = json.load(open(a.list))
out = ["[metadata]", f"Name={a.name}"] + ([f"KeyCards={a.keycards}"] if a.keycards else []) + ["[Commander]"]
out += [f"1 {c.split(' // ')[0]}" for c in d["Commander"]] + ["[Main]"]
n = 0
for g, cs in d.items():
    if g == "Commander": continue
    for x in cs:
        m = re.match(r"(\d+) (.+)", x); q, c = (int(m.group(1)), m.group(2)) if m else (1, x)
        out.append(f"{q} {c.split(' // ')[0]}"); n += q
path = a.out or f"decks/forge/{a.name.replace(' ', '_')}.dck"
open(path, "w").write("\n".join(out) + "\n")
print(f"wrote {path}: {n + len(d['Commander'])} cards")
