"""Pull real Indian package photos from the Open *Facts* databases into `eval/dataset/`.

The shot list in `eval/dataset/README.md` wants phone photos of declaration panels. Open Food
Facts is a public database of exactly that: contributors photograph the pack, and the
`ingredients` / `nutrition` / `packaging` shots on an Indian product are the back panel, which
is where the Legal Metrology declarations are printed. Open Beauty Facts and Open Products
Facts are the same API on another host, and they hold the shampoo sachets and the imported
cosmetics the shot list asks for. Photos are CC-BY-SA 3.0; every case folder keeps a
`source.json` with the product URL and the licence.

Run:  cd worker && uv run python ../eval/fetch_openfoodfacts.py --host food --count 45
Then: write `gold.json` per case by reading the printed pack in the photo (see the README).

This only downloads images. It never writes `gold.json` — gold comes from the printed pack,
and a gold file derived from a machine's reading of the pack would measure nothing.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps

DATASET = Path(__file__).resolve().parent / "dataset"
UA = "lm-compliance-eval/0.1 (SIH 26034 Legal Metrology checker)"

# name -> (api host, image host, case-folder prefix)
HOSTS = {
    "food": ("world.openfoodfacts.org", "images.openfoodfacts.org", "off"),
    "beauty": ("world.openbeautyfacts.org", "images.openbeautyfacts.org", "obf"),
    "products": ("world.openproductsfacts.org", "images.openproductsfacts.org", "opf"),
}

# The frontend resizes to 1600 px before upload, so the eval set is measured at the size the
# worker actually sees in production. A 4160 px original would flatter the OCR.
MAX_PX = 1600

# `front` first: eval/dataset/README.md sorts images by name and calls the first one the front.
KINDS = ["front", "ingredients", "nutrition", "packaging"]


def get(url: str, tries: int = 5) -> bytes:
    """GET with backoff. Open Facts rate-limits search to ~10/min and answers 503 past it."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=60) as response:  # noqa: S310 - https hosts
                return bytes(response.read())
        except urllib.error.HTTPError as err:
            if err.code not in (429, 500, 502, 503) or attempt == tries - 1:
                raise
            time.sleep(8 * (attempt + 1))
    raise RuntimeError("unreachable")


def search(api: str, page: int, page_size: int, extra: dict[str, str]) -> list[dict[str, Any]]:
    query = {
        "countries_tags_en": "india",
        "fields": "code,product_name,brands,quantity,images",
        "page": str(page),
        "page_size": str(page_size),
        **extra,
    }
    payload = json.loads(get(f"https://{api}/api/v2/search?{urllib.parse.urlencode(query)}"))
    return list(payload.get("products", []))


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (text or "").casefold()).strip("_")[:40]


def image_urls(product: dict[str, Any], image_host: str) -> dict[str, str]:
    """Full-resolution URL per image kind, deduped by upload id.

    Contributors usually select one back-panel photo as ingredients *and* nutrition *and*
    packaging. `imgid` is the raw upload, so it tells us those three are one photograph.
    """
    images: dict[str, Any] = product.get("images", {})
    code = product["code"]
    folder = f"{code[0:3]}/{code[3:6]}/{code[6:9]}/{code[9:]}" if len(code) > 8 else code

    urls: dict[str, str] = {}
    seen: set[str] = set()
    for key, meta in images.items():
        kind = key.rsplit("_", 1)[0]
        if kind not in KINDS or "rev" not in meta:
            continue
        imgid = str(meta.get("imgid", key))
        if imgid in seen or kind in urls:
            continue
        seen.add(imgid)
        urls[kind] = f"https://{image_host}/images/products/{folder}/{key}.{meta['rev']}.full.jpg"
    return urls


def save_resized(raw: bytes, path: Path) -> tuple[int, int]:
    # exif_transpose first: saving as JPEG drops the EXIF, so an orientation tag left unapplied
    # would bake the wrong rotation into the file. (Open Facts already normalises, other sources
    # do not.) It does not straighten a pack that was held sideways — nothing here does.
    img = ImageOps.exif_transpose(Image.open(BytesIO(raw)))
    img.thumbnail((MAX_PX, MAX_PX), Image.LANCZOS)
    img.convert("RGB").save(path, "JPEG", quality=82, optimize=True)
    return img.size


def fetch(product: dict[str, Any], host: str) -> str | None:
    """Download one product into its case folder. Returns the case name, or None if skipped."""
    api, image_host, prefix = HOSTS[host]
    urls = image_urls(product, image_host)
    if not (set(urls) - {"front"}):
        return None  # front only: no declaration panel, nothing to extract

    name = slug(f"{product.get('brands') or 'x'} {product.get('product_name') or ''}")
    case = DATASET / f"{prefix}_{name}_{product['code']}"[:80]
    if (case / "source.json").exists():
        return None  # already have it
    case.mkdir(parents=True, exist_ok=True)

    saved: dict[str, list[int]] = {}
    for order, kind in enumerate(k for k in KINDS if k in urls):
        try:
            raw = get(urls[kind])
        except OSError as err:
            print(f"  ! {kind}: {err}")
            continue
        width, height = save_resized(raw, case / f"{order}_{kind}.jpg")
        saved[kind] = [width, height]
        time.sleep(0.3)  # be polite to a free public API

    if not (set(saved) - {"front"}):
        for leftover in case.iterdir():
            leftover.unlink()
        case.rmdir()
        return None

    (case / "source.json").write_text(
        json.dumps(
            {
                "source": api,
                "product_url": f"https://{api}/product/{product['code']}",
                "barcode": product["code"],
                "product_name": product.get("product_name"),
                "brands": product.get("brands"),
                "quantity_on_db": product.get("quantity"),
                "license": f"photos CC-BY-SA 3.0, data ODbL — https://{api}/terms-of-use",
                "images": {k: urls[k] for k in saved},
                "resized_to": saved,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"  + {case.name}: {', '.join(sorted(saved))}")
    return case.name


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", choices=sorted(HOSTS), default="food")
    ap.add_argument("--count", type=int, default=45, help="how many case folders to end up with")
    ap.add_argument(
        "--state",
        default="ingredients-photo-selected",
        help="Open Facts state tag, e.g. nutrition-photo-selected",
    )
    ap.add_argument("--extra", default="", help="extra filter, e.g. categories_tags_en=snacks")
    ap.add_argument(
        "--sort-by",
        default="unique_scans_n",
        help="popular products are photographed better; '' for the default order",
    )
    ap.add_argument("--start-page", type=int, default=1)
    args = ap.parse_args()

    extra = {"states_tags_en": args.state}
    if args.sort_by:
        extra["sort_by"] = args.sort_by
    if args.extra:
        key, _, value = args.extra.partition("=")
        extra[key] = value

    api = HOSTS[args.host][0]
    DATASET.mkdir(parents=True, exist_ok=True)
    got, page = 0, args.start_page
    while got < args.count and page < args.start_page + 40:
        products = search(api, page, 50, extra)
        if not products:
            break
        print(f"page {page}: {len(products)} products")
        for product in products:
            if got >= args.count:
                break
            if fetch(product, args.host):
                got += 1
        page += 1
    print(f"\n{got} new cases in {DATASET}")


if __name__ == "__main__":
    main()
