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
| `referee.py` | Scores Forge logs: awards combo wins Forge's AI can't execute (strict and realistic modes) |
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

## Forge patches (`forge/patches/forge-referee.patch`)

1. **Battlefield logging:** Forge only logged permanents *leaving* play. Now it logs any permanent entering from anywhere but the stack
   (Green Sun's Zenith, Chord, reanimation), plus bounces, so the referee sees tutored combo pieces.
2. **Sacrifice hints:** `SacMe` on Eldrazi Spawn, Goat, Servo, Thopter and Squirrel tokens and Hangarback Walker, so the AI sacrifices fodder, not Blood Artist.
3. **Sacrifice in response:** a new AI rule. When an opponent's removal is about to hit a creature, sacrifice it first to a free outlet
   (Viscera Seer, Carrion Feeder, Yahenni… or Ashnod's Altar), so death triggers still happen. Applies to all AI players.

## Lessons (read before trusting a number)

- **The fast simulator only measures combo speed.** Twice it recommended changes that lost in refereed games (upgraded tutors; cutting Woe Strider).
  Use it to search, and Forge plus the referee to decide.
- **Check card rules the simulators gloss over.** Basking Broodscale is *devoid* (colorless), so "green creature" tutors
  (Summoner's Pact, Green Sun's Zenith) can't find it. That's fixed in `gsim.py` (`card_colors`).
- **Forge's AI can't run loops or pick tutor targets.** That's why the referee and `KeyCards` exist. It also never sacrifices for mana proactively.
  Cards whose value is a clever sacrifice decision are still undervalued.
- **Prices move.** Ashnod's Altar went from $8 to $14 during the project. Run `chk.py` before finalizing.
- **Compare versions on the same pods** (`pods.py` does this) and read the paired difference, not just raw win rates.
