"""Regex + keyword-anchor + layout extractor. No AI.

PP-OCR detects whole lines, and a declaration is printed as one line, so the usual case is
"the box that holds the anchor is the declaration". The layout step is the fallback for the
pack that prints the anchor and its value in separate boxes.
"""

from __future__ import annotations

import re

from ..models import Declaration, ScanContext, Source, Word

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
    "mfg_date": [
        "mfd",
        "mfg",
        "manufactured",
        "packed",
        "pkd",
        "imported on",
        "date of import",
        # The wording Rule 6(1)(d) itself uses, and what a pack that sets its declarations in a
        # table prints in the label cell: "Month & Year | of Manufacture" beside "02/2026".
        "month & year",
        "month and year",
    ],
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
        # "Manufactured, Marketed and Brand Owned by", "Manufactured & Marketed by" — one
        # anchor covers the family, and it has to beat the bare "manufactured" that anchors
        # the date, which it does by being longer.
        "manufactured, marketed",
        # The noun on its own. Every e-commerce listing labels the field this way
        # ("Manufacturer : Parle Biscuits Pvt Ltd") and so do packs that set their declarations
        # in a table. "importer" was already here on its own; this one was the oversight.
        # It cannot steal the date: "Manufacture" in "Month & Year of Manufacture" is a
        # different word, and a longer anchor still wins the box it is in.
        "manufacturer",
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

# A quantity, a price and a date are all numbers. Packs print the label on its own and the figure
# beside or under it ("MRP (Inclusive of all taxes)" / "486.00", "Month & Year of Manufacture" /
# "02/2026"), and they also print labels that point somewhere else entirely ("MRP (INCL OF ALL
# TAXES): SEE BOTTLE"). Requiring a digit tells the two apart without reading the wording.
#
# mfg_date is here because "manufactured" anchors it: on a pack whose declarations are a table,
# "Manufactured, Marketed and Brand Owned by" was claimed as the month and year, and the report
# then quoted that line back at the inspector as an unreadable date.
NEEDS_A_NUMBER = {"mrp", "net_quantity", "unit_sale_price", "mfg_date"}
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


# Anchors that are a bare noun rather than a phrase, and so only count where a *label* would
# stand: at the start of the box. "Manufacturer : Parle Biscuits Pvt Ltd" is a declaration; on the
# same listing "Is Discontinued By Manufacturer : No" and the heading "From the manufacturer" are
# not, and both stand before it in reading order, where first box wins.
AT_START = {"manufacturer"}

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
        start = "^" if anchor in AT_START else r"\b"
        match = re.search(rf"{start}{re.escape(anchor)}(?![a-z])", normalized)
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
MAX_LINES = 7
# A label cell is a label, not an address: "MRP" over "(incl. of all taxes)" is the shape,
# and two lines is as far as one goes on the packs in eval/dataset.
MAX_LABEL_LINES = 2


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
            and (
                abs(w.x - block[0].x) <= margin
                # or the block is centred, which is how packs set an address under a heading
                or abs((w.x + w.w / 2) - (block[0].x + block[0].w / 2)) <= margin
            )
            and claim(w.text) is None
            and not POINTS_ELSEWHERE.search(w.text)
        ]
        if not below:
            return out
        last = min(below, key=lambda w: (w.y, w.x))
        out.append(last)
    return out


def level(anchor: Word, w: Word) -> float:
    """How far off `anchor`'s row `w` sits, in lines. 0 is dead level."""
    return abs((w.y + w.h / 2) - (anchor.y + anchor.h / 2)) / min(anchor.h, w.h)


def overlaps_row(anchor: Word, w: Word) -> bool:
    """The two boxes share at least half a line of height."""
    return min(anchor.y + anchor.h, w.y + w.h) - max(anchor.y, w.y) >= min(anchor.h, w.h) / 2


def wrapped_label(anchor: Word, value: Word, words: list[Word]) -> list[Word]:
    """The rest of a label cell that wrapped onto a second line, in reading order.

    A bordered table centres the value against the whole label cell, so a two line label
    ("MRP" over "(incl. of all taxes)") has its value straddling both. A continuation line is
    therefore the *next printed line* under the anchor, at the same left margin, carrying no
    anchor of its own, and still sharing a row with the value. Following it line by line is what
    stops the merge: the row below a table row starts past the value's bottom, so the chain ends
    by itself, and off a table nothing shares the value's row and nothing is merged at all.

    Without it a pack that prints "MRP (incl. of all taxes) | Rs 25.00" reads as "MRP 25.00" and
    D5 fails it for not saying "inclusive of all taxes", which it does say.
    """
    out: list[Word] = []
    last = anchor
    while len(out) < MAX_LABEL_LINES:
        below = [
            w
            for w in words
            if w.image_id == anchor.image_id
            and w.id not in (anchor.id, value.id)
            and w not in out
            and last.y < w.y <= last.y + last.h
            and abs(w.x - anchor.x) <= anchor.h
            and claim(w.text) is None
            and not POINTS_ELSEWHERE.search(w.text)
            and min(value.y + value.h, w.y + w.h) > max(value.y, w.y)
        ]
        if not below:
            break
        last = min(below, key=lambda w: (w.y, w.x))
        out.append(last)
    return out


def nearest(
    anchor: Word, words: list[Word], needs_number: bool = False, table: bool = False
) -> Word | None:
    """The value box for a bare anchor: same row to the right, else below, else the table cell.

    Three guards, each one a mistake seen on the real packs:
    * same *row*, not "within a line height" — PP-OCR boxes are tall enough on a 1600 px photo
      that "MRP" claimed the net weight printed on the line above it;
    * nothing further away than a few lines — a bare "MRP" took a storage instruction from the
      far side of the panel;
    * never a box that is a declaration itself — the line under a bare "MRP" is often the next
      declaration, and swallowing it loses both.

    The last resort is the printed table, and it is last on purpose. A pack that sets its
    declarations in a bordered table centres the value against the whole label cell, and a label
    cell of two lines ("MRP" over "(incl. of all taxes)") puts the value half a line below the
    anchor's own centre: a real pen box misses the row test by two pixels and reads as having no
    MRP at all. Relaxing the row test itself was measured twice and cost 1.5 points both times,
    because the leftmost box of a loosened set is often the wrong one — on one pack it was the
    barcode. So the relaxed test only runs where the strict one and the line below have both
    found nothing, and it takes the *best aligned* box rather than the nearest one.
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
    beside = [w for w in candidates if 0 <= w.x - (anchor.x + anchor.w) <= reach_x]
    same_row = [w for w in beside if level(anchor, w) < 0.5]
    if same_row:
        return min(same_row, key=lambda w: w.x)
    below = [
        w
        for w in candidates
        if 0 <= w.y - (anchor.y + anchor.h) <= reach_y
        and w.x < anchor.x + anchor.w
        and w.x + w.w > anchor.x
    ]
    if below:
        return min(below, key=lambda w: w.y)
    if not table:
        return None
    cell = [w for w in beside if overlaps_row(anchor, w)]
    return min(cell, key=lambda w: (level(anchor, w), w.x)) if cell else None


class RegexLayoutExtractor:
    name = "regex_layout"

    def extract(self, words: list[Word], ctx: ScanContext) -> list[Declaration]:
        found: dict[str, Declaration] = {}
        # A printed address wraps onto the next line. A listing's next line is the next row of
        # the specification table — "ASIN", "Item part number" — so on a screenshot the line
        # below a declaration is another declaration, never the rest of this one.
        wrap = ctx.source is not Source.ecommerce
        # Two passes over the panel. The first takes only values that sit squarely beside or
        # under their anchor; the second lets what is left reach into a table cell. A pack that
        # prints "Mfg." twice would otherwise have the first one claim a loosely aligned box and
        # shut out the second, which had the date printed right beside it.
        for table in (False, True):
            found.update(self._pass(words, found, table=table, wrap=wrap))
        return list(found.values())

    def _pass(
        self, words: list[Word], found: dict[str, Declaration], table: bool, wrap: bool
    ) -> dict[str, Declaration]:
        found = dict(found)
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
            look = bare_anchor or needs_number
            value_box = nearest(word, words, needs_number, table) if look else None
            if value_box is not None:
                block += wrapped_label(word, value_box, words)
                block.append(value_box)
            elif needs_number:
                continue  # nothing on this panel carries the figure
            if wrap and field in WRAPS:
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
        return found
