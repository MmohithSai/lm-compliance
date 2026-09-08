"""Which pack is this? The identity a scan is filed under, so the second photograph of a
product joins the first one's history instead of starting its own.

Two declarations decide it and nothing else does: who made it, and what the pack says it is.
Both are read off the pack. A pack that declares no maker — which is a D1 violation in its own
right — gets no product row at all: an unnamed pack from an unnamed company is not an identity,
and guessing one would put another pack's scans in its history.
"""

from __future__ import annotations

from typing import Any, cast

from supabase import Client

from .extractors.regex_layout import ANCHORS, norm
from .models import Declaration

# The extractor keeps the anchor box in the value it stores, so a manufacturer reads
# "Mfd by: Parle Products Pvt Ltd, Mumbai". Those first words are the printed label; they are
# the same on every pack in the country and so say nothing about which pack this is.
LABEL_WORDS = (
    {
        word
        for field in ("manufacturer", "importer", "generic_name")
        for anchor in ANCHORS[field]
        for word in norm(anchor).split()
    }
    | {"by", "for", "and", "brand", "owned", "name"}
    # PP-OCR glued a stray glyph to "by" on the Reynolds pen in eval/dataset — "Brand Owned bye
    # Reynolds Pens India" — and left it heading the company. Read off a pack, not invented.
    | {"bye"}
)

# Legal form, not identity: "Parle Products Pvt Ltd" and "Parle Products Limited" are one company.
LEGAL_FORMS = {
    "pvt",
    "private",
    "ltd",
    "limited",
    "llp",
    "inc",
    "co",
    "corp",
    "corporation",
    "plc",
}

# Two words of the company, four of the name. The company is cut short on purpose: what ends its
# name in the address block is a comma, and the comma is the first thing a photograph loses —
# the same Reynolds pack reads "…Private Limited, Plot No. C-21" in one shot and
# "…Private Limited Plot No. C-21" in the next. Two words survive both. Names carry no address
# behind them, so they keep four.
COMPANY_WORDS = 2
NAME_WORDS = 4
# For the *displayed* name of a pack that printed no generic name. Same missing comma, but this
# one a person reads, so it keeps the pack's own spelling and only stops before the street:
# five words is a company ("Reynolds Pens India Private Limited"), the sixth is "Plot No. C-21".
DISPLAY_WORDS = 5


def _tokens(value: str) -> list[str]:
    """Words and commas, in reading order, the comma its own token. It has to be: it ends the
    company's name, and it also turns up *inside* the label — "Manufactured,Marketed and Brand
    Owned by" is one pack's printed wording, and cutting at that comma leaves nothing at all."""
    return value.replace(",", " , ").split()


def _strip_label(tokens: list[str]) -> list[str]:
    """Drop the printed label from the front. Leading only: a company really called "Name
    Brands" keeps its name, because only the first words of a declaration are its label."""
    out = list(tokens)
    while out and (out[0] == "," or norm(out[0]) in LABEL_WORDS):
        out.pop(0)
    return out


def company_key(value: str) -> str:
    """The company, normalised, from the head of its address block.

    An address block is "company, street, city, pin", so the company is what stands before the
    first comma once the label is off the front. Where the photograph lost the commas the street
    runs on into the name, and the two word cap is what keeps both readings the same key.
    """
    tokens = _strip_label(_tokens(value))
    head = tokens[: tokens.index(",")] if "," in tokens else tokens
    words = [w for w in norm(" ".join(head)).split() if w not in LEGAL_FORMS]
    return " ".join(words[:COMPANY_WORDS])


def name_key(value: str) -> str:
    """What the pack says it is, normalised. Empty when the pack printed no generic name."""
    words = norm(" ".join(_strip_label(_tokens(value)))).split()
    return " ".join(words[:NAME_WORDS])


def match_key(company: str, generic_name: str) -> str:
    """The identity, or "" when there is no company to hang it on."""
    key = company_key(company)
    return f"{key}|{name_key(generic_name)}" if key else ""


def display(value: str) -> str:
    """The declaration without its printed label, casing and punctuation kept. This is the text
    a person reads in the repository, so it stays as the pack printed it."""
    return " ".join(_strip_label(_tokens(value))).replace(" ,", ",").strip(":;-–— ").strip()


def link_product(sb: Client, scan_id: str, declarations: list[Declaration]) -> str | None:
    """Upsert the product this scan shows and point the scan at it. Returns the product id.

    An imported pack names an importer where a domestic one names a manufacturer; either is the
    company that answers for the pack, so either identifies it.
    """
    found = {d.field: d.value for d in declarations}
    company = found.get("manufacturer") or found.get("importer")
    if company is None:
        return None
    key = match_key(company, found.get("generic_name", ""))
    if not key:
        return None

    # No generic name on the pack: the maker's own first line is the most honest name there is
    # for it, and it is still text the pack printed. Brand and category stay empty — no
    # declaration carries them, and a repository that invents a category is worse than one that
    # says nothing.
    generic_name = found.get("generic_name")
    name = (
        display(generic_name)
        if generic_name
        else " ".join(display(company).split(",")[0].split()[:DISPLAY_WORDS])
    )
    rows = cast(
        list[dict[str, Any]],
        sb.table("products")
        .upsert(
            {"match_key": key, "name": name, "manufacturer": display(company)},
            on_conflict="match_key",
        )
        .execute()
        .data,
    )
    product_id = str(rows[0]["id"])
    sb.table("scans").update({"product_id": product_id}).eq("id", scan_id).execute()
    return product_id
