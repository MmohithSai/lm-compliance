# docs/law

Put the source PDFs here (not committed to Storage, just the repo):

- `pc_rules_2011_consolidated.pdf` — Legal Metrology (Packaged Commodities) Rules, 2011, as amended.
- `amendment_<year>.pdf` — each amendment (2017, 2022, 2025, 2026 …).
- `lm_act_2009.pdf` — Legal Metrology Act, 2009 (Section 36 penalties).

Source: https://consumeraffairs.gov.in/pages/legal-metrology-act

Then ask Claude Code to cross-check `rules/pc_rules_2011.yaml` and `docs/RULES.md` against these PDFs. Every `rule_ref` marked `verify: true` in the YAML needs that check.
