#!/bin/sh
# Clone Forge at the tested commit, apply the deck-lab patches, and build the headless jar.
# Needs Java 17+ and Maven. Usage: sh forge/setup_forge.sh [target dir, default ~/forge]
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"; DEST="${1:-$HOME/forge}"
COMMIT="$(cat "$HERE/FORGE_COMMIT")"
if [ ! -d "$DEST/.git" ]; then
  git clone --filter=blob:none https://github.com/Card-Forge/forge "$DEST"
fi
cd "$DEST"
git fetch --depth 1 origin "$COMMIT" 2>/dev/null || true
git checkout -q "$COMMIT"
git apply --check "$HERE/patches/forge-referee.patch" && git apply "$HERE/patches/forge-referee.patch" || echo "patch already applied?"
mvn -q -B -pl forge-gui-desktop -am package -DskipTests -Dcheckstyle.skip -Dmaven.javadoc.skip=true
ls forge-gui-desktop/target/*jar-with-dependencies.jar
echo "Forge ready at $DEST  (export FORGE_DIR=$DEST for pods.py)"
