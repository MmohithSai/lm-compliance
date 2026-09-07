"""Regex + keyword-anchor + layout extractor. No AI.

PP-OCR detects whole lines, and a declaration is printed as one line, so the usual case is
"the box that holds the anchor is the declaration". The layout step is the fallback for the
pack that prints the anchor and its value in separate boxes.
"""

from __future__ import annotations

import re

from ..models import Declaration, ScanContext, Word

# Keyword anchors -> canonical field. Value = nearest OCR box to the right of or below the anchor.
ANCHORS: dict[str, list[str]] = {
    "mrp": ["mrp", "m.r.p", "maximum retail price"],
    "net_quantity": ["net qty", "net quantity", "net wt", "net weight", "net vol", "net volume"],
    "mfg_date": ["mfd", "mfg", "manufactured", "packed", "pkd", "imported on", "date of import"],
    "importer": ["imported by", "importer"],
    "manufacturer": ["mfd by", "mfg by", "manufactured by", "packed by", "marketed by"],
    "consumer_care": ["customer care", "consumer care", "consumer complaints", "helpline"],
    "country_of_origin": ["country of origin", "origin", "made in", "product of"],
    "unit_sale_price": ["unit sale price", "per g", "per kg", "per ml", "per l"],
    "best_before": ["best before", "use by", "expiry", "exp"],
    "generic_name": ["generic name", "common name"],
}


# PP-OCR has no ₹ in any dictionary and prints "<" or "?" in its place. Dropping the stand-in
# is a deletion, not a guess: no price line carries these characters before a digit.
NOT_A_RUPEE = re.compile(r"[<>?]\s*(?=\d)")


def clean(text: str) -> str:
    """Trim the stray terminator OCR adds to a line, drop the glyph it prints for ₹."""
    return NOT_A_RUPEE.sub("", text).strip().strip(" .,;:")


def norm(s: str) -> str:
    """Casefold, punctuation to spaces. 'M.R.P.' and 'MRP' become the same anchor."""
    return " ".join(re.sub(r"\W+", " ", s, flags=re.UNICODE).casefold().split())


# Longest anchor first: 'mfd by' has to beat 'mfd' on "Mfd by: Brite Foods Pvt Ltd".
ANCHOR_LIST: list[tuple[str, str]] = sorted(
    ((field, norm(a)) for field, anchors in ANCHORS.items() for a in anchors),
    key=lambda pair: -len(pair[1]),
)


def claim(text: str) -> tuple[str, bool] | None:
    """(field, anchor_is_the_whole_box) for the longest anchor in this box, or None."""
    normalized = norm(text)
    for field, anchor in ANCHOR_LIST:
        match = re.search(rf"\b{re.escape(anchor)}\b", normalized)
        if match:
            return field, match.end() >= len(normalized)
    return None


def nearest(anchor: Word, words: list[Word]) -> Word | None:
    """The value box for a bare anchor: same line to the right, else directly below."""
    same_image = [w for w in words if w.image_id == anchor.image_id and w.id != anchor.id]
    right = [
        w
        for w in same_image
        if w.x >= anchor.x + anchor.w and abs(w.y - anchor.y) < max(anchor.h, w.h)
    ]
    if right:
        return min(right, key=lambda w: w.x)
    below = [
        w
        for w in same_image
        if w.y >= anchor.y + anchor.h and w.x < anchor.x + anchor.w and w.x + w.w > anchor.x
    ]
    return min(below, key=lambda w: w.y) if below else None


class RegexLayoutExtractor:
    name = "regex_layout"

    def extract(self, words: list[Word], ctx: ScanContext) -> list[Declaration]:
        found: dict[str, Declaration] = {}
        for word in sorted(words, key=lambda w: (w.image_id, w.y, w.x)):
            hit = claim(word.text)
            if hit is None:
                continue
            field, bare_anchor = hit
            if field in found:  # first box in reading order wins
                continue
            value, ids = clean(word.text), [word.id]
            if bare_anchor and (value_box := nearest(word, words)) is not None:
                value, ids = f"{value} {clean(value_box.text)}", [word.id, value_box.id]
            if not value:
                continue
            found[field] = Declaration(
                field=field,
                value=value,
                confidence=word.confidence,
                word_ids=ids,
                image_id=word.image_id,
                extractor=self.name,
            )
        return list(found.values())
