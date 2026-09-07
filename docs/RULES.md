# RULES — law digest

Legal Metrology (Packaged Commodities) Rules, 2011, as amended. Codes below are the `rule_id`s in `rules/pc_rules_2011.yaml`; every violation cites `rule_ref`.

Clause letters for Rule 6(1) and 6(2) were checked against the Rules text (Indian Kanoon, 2026-09-06). Refs marked **verify** come from the MVP brief and still need the PDFs in `docs/law/`.

Severity → score: critical −25, major −10, minor −3, info 0. Score = max(0, 100 − penalties). A check that cannot be measured is reported as `info` with status `unverifiable` and never costs points.

## D — mandatory declarations (Rule 6)

| Code | Rule ref | Declaration | Pass condition | Severity |
|---|---|---|---|---|
| D1 | Rule 6(1)(a) | Name and address of manufacturer / packer / importer | name + full address present (importer alone satisfies it on an imported pack) | critical |
| D2 | Rule 6(1)(b) | Common or generic name of the commodity | present | major |
| D3 | Rule 6(1)(c) | Net quantity | number + standard unit (g, kg, ml, L, cm, m, N/pcs); no "approx" / "about"; no non-standard units ("gms") | critical |
| D4 | Rule 6(1)(d) | Month and year of manufacture / packing / import | present, parseable, not after the scan date | major |
| D5 | Rule 6(1)(e) read with Rule 2(m) | Retail sale price | "MRP" / "M.R.P." / "Maximum Retail Price", a ₹ / Rs amount, and "inclusive of all taxes" (abbreviation "incl." accepted) | critical |
| D5b | Rule 6(1)(e) | One MRP only | at most one distinct MRP value on the package | critical |
| D6 | Rule 6(2) | Consumer care details | name/address + telephone + e-mail | major |
| D7 | Rule 6(1)(aa) | Country of origin | required when an importer is declared or the inspector marks the pack imported | critical |
| D8 | Rule 6(11) **verify** | Unit sale price | present | minor |
| D9 | FSS (Labelling and Display) Regulations, 2020 | Best before / use by | info only — food law, not Legal Metrology | info |

## F — font size (Rule 7)

| Code | Rule ref | Check | Severity |
|---|---|---|---|
| F1 | Rule 7, Table I **verify** | Height of numerals ≥ Table I minimum for the PDP area. Needs a scale (ArUco / card / inspector PDP mm) and the PDP area; otherwise `unverifiable`. | major |
| F2 | Rule 7 **verify** | Width ≥ ⅓ of height, except the characters 1, i, I, l. | minor |
| F3 | Medical Devices Rules, 2017 (LM PC Rules amendment, Oct 2025) **verify** | Medical device pack: font rules of the Medical Devices Rules apply. Flag and skip F1/F2. | info |

Table I (principal display panel area → minimum numeral height; embossed / blown numerals in brackets):

| PDP area | Height |
|---|---|
| ≤ 100 cm² | 1 mm (2 mm) |
| 100–500 cm² | 2 mm (4 mm) |
| 500–2500 cm² | 4 mm (6 mm) |
| > 2500 cm² | 6 mm (8 mm) |

Rule 8 — PDP area: rectangle → one full side (width × height); cylinder → 40% × height × circumference; other shapes → 40% of total surface. The MVP handles rectangles only; the inspector may type width and height in mm on the upload form.

## P — manner of declaration (Rule 9)

| Code | Rule ref | Check | Severity |
|---|---|---|---|
| P1 | Rule 9(1)(a) **verify** | All mandatory declarations grouped together on one panel | major |
| P2 | Rule 9(1)(a) **verify** | Legible and in contrast with the background (measured contrast ≥ 0.3, else `unverifiable` when not measured) | major |
| P3 | Rule 9(1)(b) **verify** | Not on the bottom, crimp or seam. Only the inspector can say; unasked → `unverifiable` | major |
| P4 | Rule 9(3) **verify** | Declarations in English or Hindi (Devanagari) | major |

## E — e-commerce (Rule 6(10), 6(10A))

| Code | Rule ref | Check | Severity |
|---|---|---|---|
| E1 | Rule 6(10) **verify** | Every declaration except month/year must appear on the listing | critical |
| E2 | Rule 6(10A) **verify** | Country-of-origin filter for imported goods on the platform (info only, from 1 July 2026) | info |

## X — exemptions (Rule 26)

| Code | Rule ref | Condition | Effect |
|---|---|---|---|
| X1 | Rule 26(a) **verify** | Net quantity ≤ 10 g or ≤ 10 ml | partial exemption: D1, D2, D4, D6, D8 downgraded to info; D3 and D5 still apply |
| X2 | Rule 26(b) **verify** | Fast food packed by a restaurant / hotel | D-rules and font rules skipped |
| X3 | Rule 26(c) **verify** | Drug covered by the Drugs (Prices Control) Order | D-rules and font rules skipped |
| X4 | Rule 26 (pan masala amendment, Feb 2026) **verify** | Pan masala | info note only until the amendment text is in `docs/law/` |

## Penalty footer (Section 36, Legal Metrology Act, 2009)

Up to ₹25,000 for a first offence, ₹50,000 for a second, ₹1,00,000 and possible imprisonment thereafter. Net quantity errors: ₹10,000–50,000.

Source: https://consumeraffairs.gov.in/pages/legal-metrology-act
