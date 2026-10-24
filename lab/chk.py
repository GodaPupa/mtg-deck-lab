import json,re,sys,time,urllib.request,urllib.parse
H={"User-Agent":"deckcheck/1.0","Accept":"application/json"}
ALLOWED=set(sys.argv[2]) if len(sys.argv)>2 else {"B","G"}
d=json.load(open(sys.argv[1])); tot=0; n=0; flags=[]
for g,cs in d.items():
  for c in cs:
    m=re.match(r'(\d+) (.+)',c); q,name=(int(m.group(1)),m.group(2)) if m else (1,c); n+=q
    if name in("Forest","Swamp","Island","Mountain","Plains"): continue
    time.sleep(0.3)
    try:
      r=json.load(urllib.request.urlopen(urllib.request.Request("https://api.scryfall.com/cards/search?q="+urllib.parse.quote(f'!"{name}"')+"&unique=prints&order=usd&dir=asc",headers=H)))
      ps=[float(x["prices"]["usd"]) for x in r["data"] if x["prices"].get("usd")]; c0=r["data"][0]
      p=min(ps) if ps else None; gc=c0.get("game_changer"); ci=set(c0["color_identity"]); leg=c0["legalities"]["commander"]
      tot+=(p or 0)*q
      if p is None or p>10 or gc or not ci<= ALLOWED or leg!="legal": flags.append((name,g,p,gc,"".join(ci),leg))
    except Exception as e: flags.append((name,g,"ERR",str(e)[:40],"",""))
print("cards",n,"total ~$%.0f"%tot)
for f in flags: print("FLAG",f)
