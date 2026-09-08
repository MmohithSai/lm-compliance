"""Render the synthetic label set + gold.json into eval/dataset/synthetic_*.

Smoke set for the pipeline: clean print, one panel, every declaration on its own line with its
anchor word. It covers D1-D8, D7 (imported), E1 and the X1/X2/X3 exemptions so the rule engine
has something to fail against before real photos exist. Real photos (40-60, phone camera) are
still the actual test set; these are not the benchmark.

Grouping (P1) is not covered here: it needs a real multi-panel photo, and on these images it
comes back `unverifiable`. Font (F1/F2) and contrast (P2) are covered by the two `_marker_` cases
at the bottom, which print a 50 mm ArUco marker at a known 8 px per mm — so the true scale, and
therefore the true printed height in millimetres, is known by construction rather than measured.
They are the only cases in the set with any scale at all. A rendered marker is not a photograph
of one: `eval/dataset/README.md`'s shot list still asks for real packs with a card in frame.

Run: cd worker && uv run python ../eval/make_synthetic.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2
from PIL import Image, ImageDraw, ImageFont

from pipeline.measure import ARUCO_MARKER_MM

DATASET = Path(__file__).resolve().parent / "dataset"
FONTS = [
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]

# field -> printed line. Gold value = the full printed line, anchor included.
BASE: dict[str, str] = {
    "generic_name": "Generic name: Glucose Biscuits",
    "net_quantity": "Net Qty: 200 g",
    "mrp": "MRP ₹20.00 (Inclusive of all taxes)",
    "mfg_date": "Mfd: 03/2026",
    "manufacturer": "Mfd by: Brite Foods Pvt Ltd, Plot 12, MIDC, Pune 411019",
    "consumer_care": "Consumer care: Brite Foods, Pune, 1800-123-4567, care@britefoods.in",
    "unit_sale_price": "Unit sale price: ₹10.00 per 100 g",
    "best_before": "Best before 6 months from packaging",
}

DROP = None  # override value meaning "this line is not printed on the pack"

# name -> (header, overrides, context, expected non-info violation codes)
CASES: dict[str, tuple[str, dict[str, str | None], dict[str, Any], list[str]]] = {
    # ---- compliant baseline
    "synthetic_compliant": ("BRITE BISCUITS", {}, {}, []),
    # ---- one missing / malformed declaration each
    "synthetic_no_manufacturer": (
        "BRITE BISCUITS",
        {"manufacturer": DROP},
        {},
        ["D1"],
    ),
    "synthetic_no_generic_name": (
        "BRITE BISCUITS",
        {"generic_name": DROP},
        {},
        ["D2"],
    ),
    "synthetic_no_tax_wording": (
        "BRITE BISCUITS",
        {"mrp": "MRP ₹20.00"},
        {},
        ["D5"],
    ),
    "synthetic_approx_no_email": (
        "BRITE BISCUITS",
        {
            "net_quantity": "Net Qty: approx 500 g",
            "consumer_care": "Consumer care: Brite Foods, Pune, 1800-123-4567",
        },
        {},
        ["D3", "D6"],
    ),
    "synthetic_no_date": (
        "BRITE BISCUITS",
        {"mfg_date": DROP},
        {},
        ["D4"],
    ),
    "synthetic_future_date": (
        "BRITE BISCUITS",
        {"mfg_date": "Mfd: 12/2031"},
        {},
        ["D4"],
    ),
    "synthetic_no_unit_price": (
        "BRITE BISCUITS",
        {"unit_sale_price": DROP},
        {},
        ["D8"],
    ),
    "synthetic_missing_three": (
        "BRITE BISCUITS",
        {"manufacturer": DROP, "mrp": DROP, "net_quantity": DROP},
        {},
        ["D1", "D3", "D5"],
    ),
    # ---- imported pack: importer line instead of manufacturer, country of origin required
    "synthetic_imported_no_origin": (
        "OLIVE OIL",
        {
            "manufacturer": DROP,
            "importer": "Imported by: Global Foods India Pvt Ltd, Andheri, Mumbai 400059",
            "generic_name": "Generic name: Olive Oil",
            "net_quantity": "Net Qty: 500 ml",
            "unit_sale_price": "Unit sale price: ₹90.00 per 100 ml",
        },
        {"is_imported": True},
        ["D7"],
    ),
    "synthetic_imported_ok": (
        "OLIVE OIL",
        {
            "manufacturer": DROP,
            "importer": "Imported by: Global Foods India Pvt Ltd, Andheri, Mumbai 400059",
            "country_of_origin": "Country of origin: Spain",
            "generic_name": "Generic name: Olive Oil",
            "net_quantity": "Net Qty: 500 ml",
            "unit_sale_price": "Unit sale price: ₹90.00 per 100 ml",
        },
        {"is_imported": True},
        [],
    ),
    # ---- exemptions: X1 downgrades to info, X2/X3 skip the declaration rules
    "synthetic_small_sachet": (
        "BRITE SACHET",
        {
            "manufacturer": DROP,
            "consumer_care": DROP,
            "unit_sale_price": DROP,
            "net_quantity": "Net Qty: 8 g",
            "mrp": "MRP ₹2.00 (Inclusive of all taxes)",
        },
        {"net_qty_g_or_ml": 8.0},
        [],
    ),
    "synthetic_restaurant_food": (
        "HOT MEAL BOX",
        {"manufacturer": DROP, "mrp": DROP, "unit_sale_price": DROP},
        {"is_restaurant_food": True},
        [],
    ),
    "synthetic_dpco_drug": (
        "PARACETAMOL 500",
        {"manufacturer": DROP, "mrp": DROP, "unit_sale_price": DROP},
        {"is_dpco_drug": True},
        [],
    ),
    # ---- e-commerce listing screenshots: no month/year required, no font checks
    "synthetic_ecom_missing_qty": (
        "Brite Glucose Biscuits - Buy online",
        {"net_quantity": DROP, "mfg_date": DROP},
        {"source": "ecommerce"},
        ["E1"],
    ),
    "synthetic_ecom_complete": (
        "Brite Glucose Biscuits - Buy online",
        {"mfg_date": DROP},
        {"source": "ecommerce"},
        [],
    ),
}


# A rendered label shot "with a reference card": one 50 mm marker, at a scale we choose. The
# text is drawn at font size 34, whose capitals are about 24 px -> 3 mm of print.
MARKER_PX_PER_MM = 8.0
MARKER_CASES: dict[str, tuple[str, dict[str, str | None], dict[str, Any], list[str]]] = {
    # 30 cm2 panel: Table I asks for 1 mm and the pack prints 3 mm.
    "synthetic_marker_font_ok": ("BRITE BISCUITS", {}, {"pdp_area_cm2": 30}, []),
    # 3000 cm2 panel (a sack): Table I asks for 6 mm and the same print is now too small.
    "synthetic_marker_font_small": ("BRITE FLOUR", {}, {"pdp_area_cm2": 3000}, ["F1"]),
}


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONTS:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def render(header: str, lines: list[str], out: Path) -> None:
    height = 200 + 72 * len(lines)
    img = Image.new("RGB", (1200, height), "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle((40, 30, 1160, height - 30), outline="black", width=3)
    draw.text((60, 50), header, font=font(56), fill="black")
    y = 160
    for line in lines:
        draw.text((60, y), line, font=font(34), fill="black")
        y += 72
    img.save(out, quality=92)


def render_with_marker(header: str, lines: list[str], out: Path) -> None:
    """The same label with a 50 mm DICT_4X4_50 marker in the frame, 8 px to the millimetre."""
    marker_px = int(ARUCO_MARKER_MM * MARKER_PX_PER_MM)
    img = Image.new("RGB", (1600, 1200), "white")
    draw = ImageDraw.Draw(img)
    draw.text((60, 50), header, font=font(56), fill="black")
    y = 160
    for line in lines:
        draw.text((60, y), line, font=font(34), fill="black")
        y += 72
    marker = cv2.aruco.generateImageMarker(
        cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50), 0, marker_px
    )
    img.paste(
        Image.fromarray(marker).convert("RGB"), (1600 - marker_px - 40, 1200 - marker_px - 40)
    )
    img.save(out, quality=92)


def declarations(overrides: dict[str, str | None]) -> dict[str, str]:
    """BASE with overrides applied; DROP removes the line. Order follows BASE, extras last."""
    merged = {**BASE, **overrides}
    return {k: v for k, v in merged.items() if v is not None}


def main() -> None:
    for name, (header, overrides, context, violations) in {**CASES, **MARKER_CASES}.items():
        decls = declarations(overrides)
        case_dir = DATASET / name
        case_dir.mkdir(parents=True, exist_ok=True)
        draw_it = render_with_marker if name in MARKER_CASES else render
        draw_it(header, list(decls.values()), case_dir / "front.jpg")
        gold = {
            "context": {"source": "package", **context},
            "declarations": decls,
            "violations": violations,
        }
        (case_dir / "gold.json").write_text(
            json.dumps(gold, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"{name}: {len(decls)} declarations, expect {violations or 'no violations'}")
    print(f"{len(CASES) + len(MARKER_CASES)} synthetic cases in {DATASET}")


if __name__ == "__main__":
    main()
