#!/bin/sh
# Download card and combo data, then build the compact databases the tools read (bulk/cards.json, bulk/variants_small.json).
# Scryfall: every printing with prices, color identity, legality and the Game Changer flag. Commander Spellbook: all combos.
set -e
cd "$(dirname "$0")"; mkdir -p bulk
URI=$(curl -s https://api.scryfall.com/bulk-data/default-cards | python3 -c "import json,sys;print(json.load(sys.stdin)['download_uri'])")
echo "Scryfall default cards: $URI"
curl -sL "$URI" -o bulk/default_cards.json
curl -sL https://json.commanderspellbook.com/variants.json -o bulk/variants.json
python3 build_db.py
