"""Regex + keyword-anchor + layout extractor. No AI.

PP-OCR detects whole lines, and a declaration is printed as one line, so the usual case is
"the box that holds the anchor is the declaration". The layout step is the fallback for the
pack that prints the anchor and its value in separate boxes.
"""

from __future__ import annotations

import re

from ..models import Declaration, ScanContext, Word

# Keyword anchors -> canonical field. Value = nearest OCR box to the right of or below the anchor.
# Wordings taken off the packs in eval/dataset, not invented: Indian labels shorten
# "marketed by" to "mkt by" / "mktd by", "net quantity" to "n. qty" / "net content", and name the
# consumer-care contact half a dozen ways. A bare "origin" is deliberately absent: it claimed
# "AND EMULSIFIER OF VEGETABLE ORIGIN 472" as the country of origin.
ANCHORS: dict[str, list[str]] = {
    "mrp": ["mrp", "m.r.p", "maximum retail price"],
    "net_quantity": [
        "net qty",
        "n. qty",
        "net quantity",
        "net wt",
        "net weight",
        "net vol",
        "net volume",
        "net content",
    ],
    "mfg_date": ["mfd", "mfg", "manufactured", "packed", "pkd", "imported on", "date of import"],
    "importer": ["imported by", "importer"],
    "manufacturer": [
        "mfd by",
        "mfg by",
        "mkt by",
        "mktd by",
        "manufactured by",
        "manufactured for",
        "packed by",
        "marketed by",
    ],
    "consumer_care": [
        "customer care",
        "consumer care",
        "customer service",
        "customer services",
        "consumer service",
        "consumer services",
        "consumer response",
        "consumer complaints",
        "helpline",
    ],
    "country_of_origin": ["country of origin", "made in", "product of"],
    "unit_sale_price": ["unit sale price", "per g", "per kg", "per ml", "per l"],
    "best_before": ["best before", "use by", "expiry", "exp"],
    "generic_name": ["generic name", "common name"],
}


# PP-OCR has no ₹ in any dictionary and prints "<" or "?" in its place. Dropping the stand-in
# is a deletion, not a guess: no price line carries these characters before a digit.
NOT_A_RUPEE = re.compile(r"[<>?]\s*(?=\d)")

# A quantity or a price is a number. Packs print the label on its own and the figure beside or
# under it ("MRP (Inclusive of all taxes)" / "486.00"), and they also print labels that point
# somewhere else entirely ("MRP (INCL OF ALL TAXES): SEE BOTTLE"). Requiring a digit tells the
# two apart without reading the wording.
NEEDS_A_NUMBER = {"mrp", "net_quantity", "unit_sale_price"}
DIGIT = re.compile(r"\d")

# Indian packs cross-refer rather than repeat: "MRP (INCL OF ALL TAXES): SEE BOTTLE",
# "ADDRESS: SAME AS MKT BY ADDRESS", "For Mkt. address, scan barcode". The line names the
# declaration but does not carry it, and claiming it hides the real one printed further down.
POINTS_ELSEWHERE = re.compile(
    r"\bsame as\b"
    r"|\bsee\b.{0,24}?\b(neck|cap|bottle|bottom|top|crimp|pack|packet|panel|below|above)\b"
    r"|\bscan\b.{0,24}?\b(qr|barcode|code)\b",
    re.IGNORECASE | re.DOTALL,
)


def clean(text: str) -> str:
    """Trim the stray terminator OCR adds to a line, drop the glyph it prints for ₹."""
    return NOT_A_RUPEE.sub("", text).strip().strip(" .,;:")


def join_lines(block: list[Word]) -> str:
    """One value from the printed lines. Only the last line loses its terminator: the comma
    at the end of "…PVT. LTD.," is how the address carries on, not OCR noise."""
    body = [NOT_A_RUPEE.sub("", w.text).strip() for w in block[:-1]]
    return " ".join(filter(None, [*body, clean(block[-1].text)]))


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
        # `(?![a-z])`, not `\b`: PP-OCR drops the space before a value, so the anchor comes back
        # glued to it ("UNIT SALE PRICE0.20PER g"). A following *letter* is still another word,
        # so "exp" does not claim "export".
        match = re.search(rf"\b{re.escape(anchor)}(?![a-z])", normalized)
        if match:
            return field, match.end() >= len(normalized)
    return None


# A wrapped address is one declaration, not three. A continuation line sits directly under the
# previous one, starts at the same left margin, and carries no anchor of its own. MAX_LINES is
# the address block on the packs in eval/dataset: "name, / street, / city - pin, state."
#
# Only the fields the law prints as an address block wrap. "Net Qty: 200 g" and "MADE IN INDIA"
# are one line by construction, and letting them absorb the next line cost 4.5 points of field
# accuracy on the real set (2026-09-07_p2-real-continuations).
WRAPS = {"manufacturer", "importer", "consumer_care"}
MAX_LINES = 6


def continuations(block: list[Word], words: list[Word]) -> list[Word]:
    """The printed lines that continue `block`, in reading order. Layout only, no wording."""
    same_image = sorted(
        (w for w in words if w.image_id == block[0].image_id and w not in block),
        key=lambda w: (w.y, w.x),
    )
    out: list[Word] = []
    last = block[-1]
    while len(block) + len(out) < MAX_LINES:
        gap = last.h  # one blank line's worth: past that it is a different part of the panel
        margin = last.h  # a wrapped line starts under the one above, not in the next column
        below = [
            w
            for w in same_image
            if w not in out
            and last.y < w.y <= last.y + last.h + gap
            and abs(w.x - block[0].x) <= margin
            and claim(w.text) is None
        ]
        if not below:
            return out
        last = min(below, key=lambda w: (w.y, w.x))
        out.append(last)
    return out


def nearest(anchor: Word, words: list[Word], needs_number: bool = False) -> Word | None:
    """The value box for a bare anchor: same row to the right, else the line directly below.

    Three guards, each one a mistake seen on the real packs:
    * same *row*, not "within a line height" — PP-OCR boxes are tall enough on a 1600 px photo
      that "MRP" claimed the net weight printed on the line above it;
    * nothing further away than a few lines — a bare "MRP" took a storage instruction from the
      far side of the panel;
    * never a box that is a declaration itself — the line under a bare "MRP" is often the next
      declaration, and swallowing it loses both.
    """
    # A label and its value can sit far apart across a printed table, so the sideways reach is
    # generous (about thirty characters); downwards it is a line or two. Both are line-height
    # multiples, so they scale with the photo.
    reach_x, reach_y = 12 * anchor.h, 2 * anchor.h
    candidates = [
        w
        for w in words
        if w.image_id == anchor.image_id
        and w.id != anchor.id
        and claim(w.text) is None
        and (not needs_number or DIGIT.search(w.text))
    ]
    right = [
        w
        for w in candidates
        if 0 <= w.x - (anchor.x + anchor.w) <= reach_x
        and abs((w.y + w.h / 2) - (anchor.y + anchor.h / 2)) < min(anchor.h, w.h) / 2
    ]
    if right:
        return min(right, key=lambda w: w.x)
    below = [
        w
        for w in candidates
        if 0 <= w.y - (anchor.y + anchor.h) <= reach_y
        and w.x < anchor.x + anchor.w
        and w.x + w.w > anchor.x
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
            if POINTS_ELSEWHERE.search(word.text):
                continue
            # A label with no figure in it is a label: go looking for the figure.
            needs_number = field in NEEDS_A_NUMBER and not DIGIT.search(word.text)
            block = [word]
            value_box = nearest(word, words, needs_number) if bare_anchor or needs_number else None
            if value_box is not None:
                block.append(value_box)
            elif needs_number:
                continue  # nothing on this panel carries the figure
            if field in WRAPS:
                block += continuations(block, words)
            value = join_lines(block)
            ids = [w.id for w in block]
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
