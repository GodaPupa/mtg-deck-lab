# Long Feng synergy research (Oct 2026)

Sources: EDHREC commander page (980 decks, synergy and inclusion), 97 complete Archidekt Long Feng decks (top by views,
card frequencies in `archidekt_freq.json`), Scryfall oracle-text searches over the bulk card data, and Commander Spellbook combos.
Filter: commander-legal, black-green, ≤ $10, not a Game Changer, not already in Lean. Ranked list in `candidates.json`.

## Key finding: backup engines for Basking Broodscale
Broodscale loops with anything that turns a death or sacrifice into a +1/+1 counter on it. Long Feng is one; these are others:
| Card | Price | How it loops with Broodscale | Needs Long Feng? |
|---|---|---|---|
| **Mazirek, Kraul Death Priest** | $0.31 | Sacrifice a Spawn → counter on each creature → Broodscale makes a Spawn → repeat. 7 new combos with Lean's cards | No |
| **Blade of the Bloodchief** | $6.03 | Equip Broodscale: whenever a creature dies, counter on it → new Spawn → sacrifice → repeat | No |
| Death's Presence | $0.36 | Doesn't work: counters equal the dead creature's power, and Spawn are 0/1 | - |

## What the community plays that Lean doesn't (Archidekt share / EDHREC synergy)
Long Feng is from the Avatar set, and most real lists run its **earthbend** cards (lands become creatures with +1/+1 counters and
return when they die, so they're recurring Long Feng fodder):
Beifong's Bounty Hunters (42% / +50%), Dai Li Agents (43% / +47%), Badgermole, Earthbender Ascension, Earth Village Ruffians,
Dai Li Indoctrination, Toph, Fatal Fissure, Solid Ground, Ba Sing Se (land, $6). Also Putrid Goblin and Rendclaw Trow (persist),
Hardened Scales, Cycle of Renewal, Pitiless Plunderer, Joo Dee. These are value and resilience, not new combos, except
Beifong's Bounty Hunters + Pawn of Ulamog (infinite).

## Plan
Forge test: Lean vs +Mazirek vs +Mazirek + Blade of the Bloodchief (replacing Ugin's Conjurant / Endless One), then combine with the
best land variant from the land experiment.
