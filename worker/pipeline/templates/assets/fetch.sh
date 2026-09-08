#!/bin/sh
# Re-download the vendored report assets. Run from this directory.
# The files are committed, so this is for auditing or upgrading them, not for a build step.
# Licences and the reasoning are in README.md next to this script.
set -eu

PLEX=https://raw.githubusercontent.com/IBM/plex/master/packages/plex-sans/fonts/complete/ttf
LUCIDE=https://raw.githubusercontent.com/lucide-icons/lucide/main

curl -fsSL -o fonts/IBMPlexSans-Regular.ttf "$PLEX/IBMPlexSans-Regular.ttf"
curl -fsSL -o fonts/IBMPlexSans-SemiBold.ttf "$PLEX/IBMPlexSans-SemiBold.ttf"
curl -fsSL -o fonts/OFL.txt https://raw.githubusercontent.com/IBM/plex/master/LICENSE.txt

for icon in circle-check circle-x circle-question-mark triangle-alert scale; do
  curl -fsSL -o "icons/$icon.svg" "$LUCIDE/icons/$icon.svg"
done
curl -fsSL -o icons/LICENSE "$LUCIDE/LICENSE"

echo "assets refreshed; check git diff before committing"
