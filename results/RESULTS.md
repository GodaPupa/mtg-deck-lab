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
Ashnod's was chosen on judgment (the free outlet those 13 losses lacked), and the upgraded simulator backs it up.

## Upgraded simulator (engine combo wins, combo-aware tutors, sacrifice-in-response, protection discipline, combo mulligans)
Three-way test, 24 paired pods, 72 games each, seed 41. Games ran ~45 s on average (vs ~100 s before).
| Version | Win rate | Strict | Combo wins | vs budget (wins/pod) |
|---|---|---|---|---|
| **Budget + Ashnod's Altar (~$141)** | **46% ±12** | 44% | 27 | +0.21 (se 0.23) |
| Budget (~$129) | 39% ±11 | 39% | 25 | - |
| + Ashnod's + recursion (Unearth, Gravedigger, Cauldron; cut Summoner's Pact, Roiling Regrowth, Entish Restoration) | 25% ±10 | 25% | 18 | -0.42 (se 0.25) |
Plunder Loop: 31% across all 216 games (the engine now adjudicates its Glint-Horn loop).
- The recursion package hurt. The AI rarely cast it, and Unearth hit Hammerhead and Yahenni, never Broodscale. The cards it replaced
  (land-sacrifice ramp that triggers Long Feng, and Summoner's Pact for green pieces) were doing work.
- The interim read from the old AI (recursion ahead at 8 pods) was noise. Wait for full runs.
- Protection was cast only twice in 216 games under the new hold rule, so the gate may be too strict. Worth a look before testing protection packages.

**Recommendation stands: budget + Ashnod's Altar (`lf_ash.json`).**

## Redundancy vs interaction (same 24 pods as the Ashnod's baseline, seed 41, 72 games each)
Both cut Three Visits and Harrow.
| Version | Win rate | Combo wins | vs Ashnod's build (wins/pod) |
|---|---|---|---|
| Ashnod's build (baseline) | 46% ±12 | 27 | - |
| + Fatal Push, Tragic Slip | 47% ±12 | 31 | +0.04 (se 0.21) |
| + Phantom Train, Stonecoil Serpent | 33% ±11 | 22 | -0.38 (se 0.22) |
- Redundancy hurt: more combos on paper, but the extra loop pieces are clunky, and losses to Plunder Loop rose from 16 to 22.
- Interaction tied overall but added 4 combo wins. Forge's AI aimed the removal badly (mana elves, Siren Stormtamer), not at Glint-Horn or Malcolm,
  so a human pilot should get more from it. Cutting two ramp spells cost nothing.
- The list looks close to a local optimum for this AI. Single swaps move it within noise.

## Lean vs Shielded (combo-aware removal targeting + looser protection gate; 20 pods, seed 51, 60 games each)
Both cut Arcane Signet and Golgari Signet (ramp 12 to 10).
| Version | Win rate | Combo wins | vs main (wins/pod) |
|---|---|---|---|
| Main (Ashnod's + Fatal Push/Tragic Slip) | 30% ±12 | 15 | - |
| **Lean: + Go for the Throat, Heartless Act** | **44% ±13** | 25 | +0.40 (se 0.27) |
| Shielded: + Veil of Summer, Blossoming Defense | 22% ±10 | 13 | -0.25 (se 0.19) |
- Opponents now aim removal at Long Feng and Broodscale, so every version's rate dropped. That's a tougher, more realistic table.
- Extra cheap removal is the best use of the slots so far. Protection still barely gets cast (1–2 per 60 games): the hold rule passes,
  but Forge's own protection AI rarely chooses to respond. A known gap.
- Confirmation run (24 new pods, seed 61) started to check the Lean lead.

## Confirmation: Lean vs 12-ramp main (24 new pods, seed 61, 72 games each)
Lean 50% vs main 26% (+0.71 wins/pod, se 0.19). **Pooled over both runs (44 pods): Lean 47% (62/131) vs main 28% (37/132),
+0.57 wins/pod, se 0.16, z = 3.5.** The most decisive result so far. **Lean is the new main list** (`lf_lean.json`, ~$135, 10 ramp, 12 removal).
Next test: "Leaner" (8 ramp, 14 removal: -Talisman of Resilience, -Nature's Lore, +Cut Down, +Bone Shards).

## Leaner vs Lean (24 pods, seed 71, 72 games each)
Leaner (-Talisman of Resilience, -Nature's Lore, +Cut Down, +Bone Shards; 8 ramp, 14 removal): 31% vs Lean 33%, -0.08 wins/pod (se 0.25), a tie.
Leaner lost to Plunder Loop less (15 vs 21) but to Ur-Dragon more (11 vs 5), and failed to cast Long Feng in 8 losses vs 6.
**10 ramp / 12 removal (Lean) is the sweet spot. Lean stays main.**
