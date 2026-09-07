"""Regex + keyword-anchor + layout extractor (P2). No AI."""

from __future__ import annotations

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


class RegexLayoutExtractor:
    name = "regex_layout"

    def extract(self, words: list[Word], ctx: ScanContext) -> list[Declaration]:
        raise NotImplementedError("P2")
