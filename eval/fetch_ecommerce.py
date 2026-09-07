"""Screenshot real Indian e-commerce listings into `eval/dataset/` as `source: ecommerce` cases.

Rule 6(10) makes the *listing* carry the declarations, so the eval image is a page screenshot,
not a package photo. Headless Chrome (already on any dev machine — no new dependency) renders
the public product page; the capture is sliced into phone-sized tiles because that is what an
inspector actually uploads: a couple of screenshots, not one 6000 px strip. Tiles keep the text
at its rendered size, so nothing is lost to downscaling.

Run:  cd worker && uv run python ../eval/fetch_ecommerce.py
Then: write `gold.json` per case from what the listing shows (see eval/dataset/README.md).

Listings change. `source.json` records the URL and the capture date, so a case that no longer
matches its live page is still a valid fixed test image.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from datetime import date
from pathlib import Path

from PIL import Image

DATASET = Path(__file__).resolve().parent / "dataset"

CHROME = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]

WIDTH = 1000  # a desktop listing column; narrower and Amazon serves the mobile layout
PAGE_HEIGHT = 9000  # some listings push the product-details table below an A+ banner
TILE = 1600  # one tile ~ one phone screenshot; also the frontend's upload cap
MAX_TILES = 6  # the declarations are always above the review section

# name -> public product page. Chosen for coverage, not for brand:
# two that carry the full Rule 6(10) block, two that leave parts out, one imported good.
LISTINGS = {
    "ecom_amazon_parle_g_800g": "https://www.amazon.in/Parle-G-Glucose-Biscuit-800g/dp/B0754HP7X2",
    "ecom_amazon_figaro_olive_oil": "https://www.amazon.in/Figaro-Extra-Virgin-Olive-500ml/dp/B00X7RJPSG",
    "ecom_amazon_tata_salt_1kg": "https://www.amazon.in/Flowing-Iodised-Namak-Vacuum-Evaporated/dp/B07575FPC3",
    "ecom_flipkart_tata_salt": "https://www.flipkart.com/tata-salt-1-kg-iodized/p/itm8ec3227ec312d",
    "ecom_amazon_britannia_tiger": "https://www.amazon.in/Britannia-Tiger-Glucose-Biscuit-124/dp/B0CRF29ZJR",
    "ecom_amazon_parle_krackjack": "https://www.amazon.in/Parle-Krackjack-800g/dp/B08KR2Y12D",
}


def chrome() -> str:
    found = next((p for p in CHROME if Path(p).exists()), None) or shutil.which("chromium")
    if not found:
        raise SystemExit("no Chrome/Edge/Chromium found — edit CHROME in this file")
    return found


def capture(url: str, out: Path) -> None:
    """Full-page PNG via headless Chrome. A throwaway profile keeps cookies out of the shot."""
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run(  # noqa: S603 - fixed binary, urls from LISTINGS above
            [
                chrome(),
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                f"--user-data-dir={profile}",
                f"--window-size={WIDTH},{PAGE_HEIGHT}",
                "--virtual-time-budget=20000",
                f"--screenshot={out}",
                url,
            ],
            check=True,
            capture_output=True,
            timeout=180,
        )


def tile(png: Path, case: Path) -> int:
    """Slice the capture into phone-sized JPEGs. Blank tiles (short pages) are dropped."""
    img = Image.open(png).convert("RGB")
    saved = 0
    for index in range(MAX_TILES):
        top = index * TILE
        if top >= img.height:
            break
        piece = img.crop((0, top, img.width, min(top + TILE, img.height)))
        if piece.convert("L").getextrema()[0] > 250:  # all-white: past the end of the content
            break
        piece.save(case / f"{index}_screen{index + 1}.jpg", "JPEG", quality=85, optimize=True)
        saved += 1
    return saved


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="one case name from LISTINGS")
    ap.add_argument("--force", action="store_true", help="recapture cases that already exist")
    args = ap.parse_args()

    for name, url in LISTINGS.items():
        if args.only and name != args.only:
            continue
        case = DATASET / name
        if (case / "source.json").exists() and not args.force:
            print(f"  = {name} (have it)")
            continue
        case.mkdir(parents=True, exist_ok=True)
        png = case / "_full.png"
        try:
            capture(url, png)
        except (subprocess.SubprocessError, OSError) as err:
            shutil.rmtree(case, ignore_errors=True)
            print(f"  ! {name}: {type(err).__name__}")
            continue
        tiles = tile(png, case)
        png.unlink()
        if tiles < 2:
            # A real listing runs past one tile. One short page is a 404 or a bot block,
            # and storing it as a fixture would measure the block page, not the listing.
            for leftover in case.iterdir():
                leftover.unlink()
            case.rmdir()
            print(f"  ! {name}: {tiles} tile — 404 or blocked, not stored")
            continue
        (case / "source.json").write_text(
            json.dumps(
                {
                    "source": "e-commerce listing screenshot",
                    "product_url": url,
                    "captured": date.today().isoformat(),
                    "note": "public listing page, rendered by headless Chrome at "
                    f"{WIDTH}px wide and sliced into {TILE}px tiles",
                    "tiles": tiles,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"  + {name}: {tiles} tiles")


if __name__ == "__main__":
    main()
