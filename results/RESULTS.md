# Experiment log: Grand Audit (Long Feng, Grand Secretariat)

Rules: Commander, 100 cards, every card ≤ $10 at its cheapest printing (exception by choice: Ashnod's Altar, ~$14), no Game Changers.
Pods: our deck + Plunder Loop + 2 random opponents from 9 EDHREC average decks ($290–$3,700). 25% = an average seat.

## Commander search
- Scored every budget commander for combo consistency (Spellbook combos, Monte Carlo), cross-checked with EDHTop16 and EDHREC popularity (< 5,000 decks).
- Finalists: **Long Feng** (Grand Audit, Broodscale aristocrats) and **Malcolm + Tana** (Plunder Loop, Glint-Horn Treasure loop).

## Fast simulator (goldfish + interaction model)
| List | Combo by T10, casual | Combo by T10, high power |
|---|---|---|
| Budget (lf4) | 63% | 19% |
| Upgraded (+GSZ, Finale, Diabolic Intent, Emeritus, ramp, protection; ~$240) | 73% | 28% |
| Plunder Loop | 63% | 23% |
Caveat: this simulator treated Broodscale as green, which overrated Summoner's Pact and GSZ. Fixed afterwards.

## Refereed Forge pods
| Test | Result |
|---|---|
| Forge AI alone (no referee), 20 games | combos were on board 6 times and never used. The AI can't run loops |
| Referee v1, 72 games | blind to tutored creatures (fixed with the logging patch) |
| Referee + logging, 48 games each | Budget 29%, Upgraded 29%, Value 25%, Plunder 12%. AI tutored for its biggest creature, not combo pieces |
| + `KeyCards` tutor priority, 24 paired pods | **Budget 46% (±12)** vs Upgraded 35% (±11); paired −0.33 wins/pod (se 0.25) |
| Budget + Veil of Summer & Blossoming Defense (cut Woe Strider, Insatiable Avarice) | 28% vs budget 46%: cutting Woe Strider, a free outlet, hurt |
| Budget + High Market (+ Ashnod's / Husk variants), partial | AI never activated Ashnod's and sacrificed its own payoffs to High Market; inconclusive → led to patches 2 and 3 |

Loss analysis (budget, 42 losses): 17 never found Broodscale · 13 had Broodscale but were missing an outlet or payoff · 12 had Broodscale removed.
Basking Broodscale was in 27 of 30 combo wins.

## Current recommendation
**Budget list + Ashnod's Altar (for Insatiable Avarice), ~$141** — `decks/lists/lf_ash.json`.
Ashnod's was chosen on judgment: it's the free outlet those 13 losses lacked. Pending: three-way test (budget vs Ashnod's vs recursion build
with Unearth, Gravedigger and Cauldron of Essence) using the sacrifice-in-response AI.
