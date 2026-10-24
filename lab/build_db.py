import json,gzip,collections
cards={}
import os
def _rows():
    if os.path.exists("bulk/default_cards.jsonl.gz"):
        with gzip.open("bulk/default_cards.jsonl.gz","rt") as f:
            for line in f: yield json.loads(line)
    else:  # Scryfall bulk download is one JSON array
        for c in json.load(open("bulk/default_cards.json")): yield c
if True:
    for c in _rows():
        if c.get("lang")!="en" or c.get("layout") in ("token","art_series","emblem","double_faced_token"): continue
        n=c["name"]; usd=c.get("prices",{}).get("usd") or c.get("prices",{}).get("usd_foil")
        e=cards.get(n)
        if not e:
            faces=c.get("card_faces") or [c]
            txt=c.get("oracle_text") or " // ".join(x.get("oracle_text","") for x in faces)
            e=cards[n]=dict(mv=c.get("cmc",0),ci="".join(c.get("color_identity",[])),type=c.get("type_line",""),
               text=txt,gc=bool(c.get("game_changer")),legal=c.get("legalities",{}).get("commander")=="legal",
               keywords=c.get("keywords",[]),usd=None,front=n.split(" // ")[0],cost=c.get("mana_cost") or faces[0].get("mana_cost",""))
        if c.get("game_changer"): e["gc"]=True
        if usd:
            u=float(usd); e["usd"]=u if e["usd"] is None else min(e["usd"],u)
# also index by front face
front={}
for n,e in cards.items(): front[e["front"]]=n
print("cards",len(cards))
json.dump(cards,open("bulk/cards.json","w"))
v=json.load(open("bulk/variants.json"))["variants"]
WIN=("win the game","loses the game","infinite damage","infinite lifeloss","near-infinite damage","near-infinite lifeloss","infinite combat damage","infinite turns","infinite mill","each opponent loses","infinite combat phases","infinitely large creature","infinite power")
out=[];skip=collections.Counter()
for x in v:
    if x.get("status")!="OK": skip["status"]+=1; continue
    if x.get("requires"): skip["templates"]+=1; continue
    names=[u["card"]["name"] for u in x["uses"]]
    if len(names)>4: skip["big"]+=1; continue
    prods=[p["feature"]["name"].lower() for p in x["produces"]]
    decisive=any(any(w in p for w in WIN) for p in prods)
    mana=any("infinite" in p and "mana" in p for p in prods)
    cmdr=[u["card"]["name"] for u in x["uses"] if u.get("mustBeCommander")]
    leg=(x.get("legalities") or {}).get("commander",True)
    if leg is False: skip["illegal"]+=1; continue
    out.append(dict(id=x["id"],cards=names,dec=decisive,mana=mana,cmdr=cmdr,prod=prods[:4],pop=x.get("popularity") or 0))
print("variants kept",len(out),dict(skip))
json.dump(out,open("bulk/variants_small.json","w"))
