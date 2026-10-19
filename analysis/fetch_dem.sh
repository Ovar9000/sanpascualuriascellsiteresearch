#!/usr/bin/env bash
# Download the four SRTM 1-arcsec tiles covering Burias Island into ./dem
set -euo pipefail
DEST="${DEM_DIR:-$(dirname "$0")/../dem}"
mkdir -p "$DEST"
for t in N12/N12E122 N12/N12E123 N13/N13E122 N13/N13E123; do
  f="$DEST/$(basename "$t").hgt"
  [ -f "$f" ] || curl -sSf "https://s3.amazonaws.com/elevation-tiles-prod/skadi/$t.hgt.gz" | gunzip > "$f"
done
ls -la "$DEST"
