# mtg-deck-lab

Tools for building and testing budget Commander decks: find a strong commander, build under price rules,
then test the list two ways — a fast goldfish simulator and real four-player Forge games scored by a combo referee.

Built while developing **Grand Audit** (Long Feng, Grand Secretariat), a ~$141 Basking Broodscale aristocrats deck.
See [`results/RESULTS.md`](results/RESULTS.md) for every experiment and what it showed.

## Setup (about 15 minutes)

```sh
sh lab/fetch_data.sh          # Scryfall cards + Commander Spellbook combos -> lab/bulk/
sh forge/setup_forge.sh       # clone Forge at the tested commit, apply patches, build (needs Java 17+, Maven)
export FORGE_DIR=~/forge
```

Run everything below from `lab/`.

## The tools

| Tool | What it does |
|---|---|
| `build_db.py` | Builds `bulk/cards.json` (cheapest price, color identity, legality, Game Changer flag) and `bulk/variants_small.json` (Spellbook combos) |
| `chk.py list.json BG` | Live Scryfall check of a list: total price, and flags any card over $10, off-color, illegal, or a Game Changer |
| `score2.py` | Combo-consistency scoring of commanders (Monte Carlo over Spellbook combos + engine payoffs) |
| `gsim.py` / `gsim2.py` | Goldfish simulator. v2 adds colored mana, an opponent-interaction model (casual / high power) and top-of-library tutors. `python3 gsim2.py decks/lists/lf4.json` |
| `make_dck.py` | JSON list -> Forge `.dck`, with `KeyCards=` (the AI tutors for these first, in order) |
| `opponents.py` | Opponent pool from EDHREC average decks + their decisive combos for the referee |
| `pods.py` | Runs refereed four-player pods; every version plays the same seats and rivals (paired), resumable |
| `export_combos.py` | Writes `combos.txt` for the engine: each deck's combos, key cards, protection spells, opponents' combos |
| `referee.py` | Scores Forge logs: reads the engine's combo wins (or reconstructs them from the log for unpatched runs) |
| `compare.py` | Paired head-to-head between versions with margins of error |

Decks: grouped JSON lists in `lab/decks/lists/`, Forge decks in `lab/decks/forge/`, registry in `lab/decks.json`
(deck name -> list, key card, special rules). Add a deck by writing its list, running `make_dck.py`, and adding a registry line.

### Typical test

```sh
python3 make_dck.py decks/lists/my_new.json "GA New" --keycards "Basking Broodscale;Viscera Seer;Blood Artist"
# add "GA New" to decks.json, then:
python3 pods.py --versions GA_Ashnod GA_New --fixed Plunder_Loop --rivals 2 --pods 14 --seed 31 --out runs/new
python3 compare.py runs/new/GA_Ashnod runs/new/GA_New
```

About 45 seconds per game with 2 workers. 42 games per version gives roughly ±14 points, so only trust big gaps, or run more pods.

**Speed:** the slowest 10% of games (trigger-heavy boards like Ur-Dragon) take ~45% of run time, so `pods.py` caps games at 180 s
(`--timeout`), which cuts total time by about a quarter. Games are CPU-bound (one core per Forge process), so `--workers` should match
your CPU count. A machine with 8 cores runs about 4x faster than the 2-core cloud box.

## Forge patches (`forge/patches/forge-referee.patch`)

Engine:
1. **Combo adjudication** (`RefereeCombos.java`): Forge's AI can't execute loops, so the engine itself declares the win the moment a known
   combo is live on its controller's turn: key card(s) plus every piece on the battlefield and 4+ lands. Opponents have already had their chance
   to answer each piece as it was cast. Games end right there, so runs are about 2.5x faster. Combos come from `combos.txt` (`export_combos.py`),
   passed as `-Dreferee.combos=...`. `-Dreferee.mode=strict` requires the pieces to have survived a full round. Opponents' combos are judged too.
2. **Battlefield logging:** logs permanents entering from anywhere but the stack (tutors, reanimation) and bounces, for the log referee.

AI:
3. **Combo-aware tutoring** (`ComboAwareAi.java`): tutors fetch the card that leaves the fewest pieces missing, given the battlefield and hand.
4. **Sacrifice in response:** when removal is about to hit a creature, sacrifice it first to a free outlet, so death triggers still happen.
5. **Sacrifice hints:** `SacMe` on Spawn, Goat, Servo, Thopter and Squirrel tokens and Hangarback, so the AI sacrifices fodder, not payoffs.
6. **Sacrifice-for-mana:** outlets like Ashnod's Altar count as normal mana sources while spare fodder tokens exist.
7. **Protection discipline:** a deck's protection spells (its list's "Protection" group) are held until an opponent's spell or ability
   targets or threatens a combo piece or the commander (or targets our spell).
8. **Combo-aware mulligans:** a 7-card opening hand with no combo piece and no tutor is mulliganed (free mulligan).
10. **Protect in response:** when an opponent's spell or ability targets or threatens the commander or a combo piece, cast a held
   protection spell (Snakeskin Veil, Heroic Intervention, Veil of Summer, Blossoming Defense) on it, before falling back to sacrificing it.
9. **Combo-aware removal targeting:** removal (destroy, exile, -X/-X) ranks an opponent's known combo pieces and commanders first,
   with a bigger bonus the closer that combo is to done. It applies to every AI, so opponents aim at your engine too.

After changing decks or `decks.json`, rerun `python3 export_combos.py` so the engine knows the combos.

## Lessons (read before trusting a number)

- **The fast simulator only measures combo speed.** Twice it recommended changes that lost in refereed games (upgraded tutors; cutting Woe Strider).
  Use it to search, and Forge plus the referee to decide.
- **Check card rules the simulators gloss over.** Basking Broodscale is *devoid* (colorless), so "green creature" tutors
  (Summoner's Pact, Green Sun's Zenith) can't find it. That's fixed in `gsim.py` (`card_colors`).
- **Forge's AI can't run loops or pick tutor targets.** That's why the referee and `KeyCards` exist. It also never sacrifices for mana proactively.
  Cards whose value is a clever sacrifice decision are still undervalued.
- **Prices move.** Ashnod's Altar went from $8 to $14 during the project. Run `chk.py` before finalizing.
- **Compare versions on the same pods** (`pods.py` does this) and read the paired difference, not just raw win rates.
