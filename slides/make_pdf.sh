#!/usr/bin/env bash
# Build the HTML deck from results/review.json and print it to PDF with headless Chromium.
set -euo pipefail
cd "$(dirname "$0")"
python3 build_slides.py
CHROME="${CHROME:-$(ls /opt/pw-browsers/chromium-*/chrome-linux/chrome 2>/dev/null | head -1)}"
CHROME="${CHROME:-$(command -v chromium || command -v google-chrome)}"
"$CHROME" --headless --no-sandbox --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="$PWD/San_Pascual_Cell_Site_Review.pdf" "file://$PWD/san_pascual_review_slides.html" 2>/dev/null
ls -la San_Pascual_Cell_Site_Review.pdf
