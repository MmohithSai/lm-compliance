"""Where the real-photo misses come from. Reads a result file and the OCR cache, never OCRs.

    cd worker && uv run python ../eval/error_report.py ../eval/results/<run>.json

For every real case and every field gold or the pipeline names, it puts side by side the gold
value, the OCR line that best covers it, the final extracted value, and a failure category with
the evidence the category rests on. Written to `<run>_errors.json` and `<run>_errors.md` beside
the result file. `diagnose.py reach` says how many misses the OCR text could reach; this says,
per miss, which stage lost it.

Categories are assigned from measurable things (token coverage in the OCR text, whether the gold
sits on one printed line, how the prediction differs from gold), and the rule that fired is
written into `why` so a reader can disagree with it. No confidence is invented: the only score
attached is PP-OCR's own recognition confidence on the boxes the extractor used.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from diagnose import cached_words, gold_of
from run_eval import DATASET, norm

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "worker"))
from pipeline.extractors.regex_layout import ANCHORS  # noqa: E402

CATEGORIES = {
    "ocr_missed": (
        "1. OCR did not detect the text (under half the gold words are anywhere in the output)"
    ),
    "layout": (
        "2. OCR read the words but they span several boxes and the extractor did not group them"
    ),
    "anchor": "3. The gold sits on one OCR line and no anchor / regex claimed it",
    "recognition": (
        "4. OCR read the line with character errors, so the value can never match gold"
    ),
    "wrong_field": "5. The value was assigned to a different field",
    "wrapped": "6. A wrapped / multi-line value was cut short or over-merged",
    "unlabeled": "7. The declaration is printed with no label at all (nothing to anchor on)",
    "association": "11. The anchor fired and took the wrong neighbouring box as its value",
    "spurious": "3b. A box that is not a declaration was claimed (anchor false positive)",
}

# What a label for this field looks like, so "printed with no label" can be told apart from
# "printed with a label the anchor list does not know".
LABELS = {field: [norm(a) for a in anchors] for field, anchors in ANCHORS.items()}


def tokens(value: str) -> list[str]:
    """The gold's words, normalised. Words of one or two letters ("in", "of", "by", "at") are
    dropped unless they are all there is: "MADE IN INDIA" was scoring 67% against a line that
    merely contained "indiahelpline@", and that put an OCR miss down as a layout miss."""
    words = [t for t in (norm(w) for w in value.split()) if t]
    long_enough = [t for t in words if len(t) >= 3]
    return long_enough or words


def coverage(want: list[str], text: str | list[str]) -> float:
    """Share of the gold words present in `text`. Given a token list, a gold word counts when it
    is a whole token, or — for words of five letters or more — the head or tail of one, which is
    what PP-OCR's dropped spaces produce ("SPICEDBUTTERMILK", "MADEIN"). Given a string, plain
    containment, for the page-wide test where the words may be anywhere."""
    if not want:
        return 0.0
    if isinstance(text, str):
        return sum(1 for t in want if t in text) / len(want)
    found = 0
    for t in want:
        if t in text or (
            len(t) >= 5 and any(b.startswith(t) or b.endswith(t) for b in text if b != t)
        ):
            found += 1
    return found / len(want)


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def labelled(field: str, value: str) -> bool:
    text = norm(value)
    return any(label and label in text for label in LABELS.get(field, []))


def analyse(
    case: str, field: str, want: str | None, got: str | None, boxes: list[dict[str, Any]]
) -> dict[str, Any]:
    """One row of the report."""
    page = norm(" ".join(b["text"] for b in boxes))
    row: dict[str, Any] = {"case": case, "field": field, "gold": want, "final": got}

    if want is not None:
        gold_tokens = tokens(want)
        row["ocr_coverage_all_images"] = round(coverage(gold_tokens, page), 2)
        per_image: dict[str, float] = {}
        for image in sorted({b["image_id"] for b in boxes}):
            text = norm(" ".join(b["text"] for b in boxes if b["image_id"] == image))
            per_image[image] = round(coverage(gold_tokens, text), 2)
        row["ocr_coverage_by_image"] = per_image
        best = max(boxes, key=lambda b: coverage(gold_tokens, tokens(b["text"])), default=None)
        if best is not None:
            row["ocr_best_line"] = best["text"]
            row["ocr_best_line_image"] = best["image_id"]
            row["ocr_best_line_coverage"] = round(coverage(gold_tokens, tokens(best["text"])), 2)
            row["ocr_best_line_confidence"] = round(best["confidence"], 3)
        row["gold_is_labelled"] = labelled(field, want)

    if want is not None and got is not None and norm(want) == norm(got):
        row["status"] = "correct"
        row["category"] = None
        return row

    if want is None:
        row["status"] = "spurious"
        row["category"], row["why"] = "spurious", "predicted a field gold does not have"
        return row

    row["status"] = "missed" if got is None else "wrong"
    all_cov = row["ocr_coverage_all_images"]
    line_cov = row.get("ocr_best_line_coverage", 0.0)

    if all_cov < 0.5:
        row["category"] = "ocr_missed"
        row["why"] = f"only {all_cov:.0%} of the gold words are anywhere in the OCR output"
    elif not row["gold_is_labelled"]:
        row["category"] = "unlabeled"
        row["why"] = "gold carries none of the field's label words; nothing to anchor on"
    elif got is None:
        if line_cov >= 0.9:
            row["category"] = "anchor"
            row["why"] = f"{line_cov:.0%} of the gold words sit on one OCR line; nothing claimed it"
        else:
            row["category"] = "layout"
            row["why"] = (
                f"gold words are in the OCR output ({all_cov:.0%}) "
                f"but the best single line holds {line_cov:.0%}"
            )
    else:
        sim = similarity(want, got)
        row["similarity"] = round(sim, 2)
        n_want, n_got = norm(want), norm(got)
        if sim >= 0.85:
            row["category"] = "recognition"
            row["why"] = f"prediction is {sim:.0%} similar to gold: characters OCR misread"
        elif n_want.startswith(n_got) or n_got in n_want:
            row["category"] = "wrapped"
            row["why"] = "prediction is a prefix / part of gold: continuation lines were dropped"
        elif n_want in n_got:
            row["category"] = "wrapped"
            row["why"] = "gold is inside the prediction: neighbouring lines were merged in"
        else:
            row["category"] = "association"
            row["why"] = f"anchor fired but the value came from another box ({sim:.0%} similar)"
    return row


def cell(value: object) -> str:
    return (str(value) if value is not None else "—").replace("|", "\\|").replace("\n", " ")


def main(result_path: Path) -> None:
    result = json.loads(result_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    for entry in result["per_case"]:
        case, pred = entry["case"], entry["pred"]
        if case.startswith("synthetic"):
            continue
        boxes = [
            w
            for image in sorted((DATASET / case).glob("*.jpg"))
            for w in (cached_words(image) or [])
        ]
        gold = gold_of(case)
        for field in sorted(set(gold) | set(pred)):
            rows.append(analyse(case, field, gold.get(field), pred.get(field), boxes))

    # Spurious predictions that are really another field's value.
    by_case: dict[str, dict[str, str]] = {}
    for r in rows:
        if r["gold"] is not None:
            by_case.setdefault(r["case"], {})[r["field"]] = r["gold"]
    for r in rows:
        if r["status"] in ("spurious", "wrong") and r["final"]:
            for other, value in by_case.get(r["case"], {}).items():
                if other != r["field"] and norm(value) == norm(r["final"]):
                    r["category"], r["why"] = "wrong_field", f"the value is gold's {other}"

    misses = [r for r in rows if r["status"] in ("missed", "wrong")]
    counts = Counter(r["category"] for r in misses)
    by_field: dict[str, Counter[str]] = {}
    for r in misses:
        by_field.setdefault(r["field"], Counter())[r["category"]] += 1
    spurious = Counter(r["field"] for r in rows if r["status"] == "spurious")

    out = {
        "source": result_path.name,
        "real_cases": len(by_case),
        "gold_declarations": sum(1 for r in rows if r["gold"] is not None),
        "correct": sum(1 for r in rows if r["status"] == "correct"),
        "misses": len(misses),
        "spurious": sum(spurious.values()),
        "categories": CATEGORIES,
        "miss_counts": dict(counts.most_common()),
        "miss_counts_by_field": {f: dict(c) for f, c in sorted(by_field.items())},
        "spurious_by_field": dict(spurious.most_common()),
        "rows": rows,
    }
    stem = result_path.with_suffix("")
    Path(f"{stem}_errors.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    md = [f"# Real-photo error report — `{result_path.name}`", ""]
    md.append(
        f"{out['real_cases']} real cases, {out['gold_declarations']} gold declarations, "
        f"{out['correct']} correct, {out['misses']} missed or wrong, {out['spurious']} spurious."
    )
    md += ["", "## Misses by category", "", "| Category | Misses | Share |", "|---|---|---|"]
    for cat, n in counts.most_common():
        md.append(f"| {CATEGORIES[cat]} | {n} | {n / len(misses):.0%} |")
    md += ["", "## Misses by field and category", ""]
    md.append("| Field | " + " | ".join(counts) + " | total |")
    md.append("|---|" + "---|" * (len(counts) + 1))
    for field, c in sorted(by_field.items()):
        cells = " | ".join(str(c.get(k, 0)) for k in counts)
        md.append(f"| {field} | {cells} | {sum(c.values())} |")
    md += ["", "## Spurious predictions by field", "", "| Field | Count |", "|---|---|"]
    for field, n in spurious.most_common():
        md.append(f"| {field} | {n} |")
    md += ["", "## Every miss and spurious prediction", ""]
    md.append("| Case | Field | Gold | Best OCR line (coverage, conf) | Final | Category | Why |")
    md.append("|---|---|---|---|---|---|---|")
    for r in rows:
        if r["status"] == "correct":
            continue
        line = r.get("ocr_best_line")
        ocr = "—"
        if line:
            ocr = (
                f"{cell(line)} ({r.get('ocr_best_line_coverage', 0):.0%}, "
                f"{r.get('ocr_best_line_confidence', 0):.2f})"
            )
        md.append(
            f"| {r['case'][:38]} | {r['field']} | {cell(r['gold'])} | {ocr} | "
            f"{cell(r['final'])} | {r['category']} | {cell(r.get('why'))} |"
        )
    Path(f"{stem}_errors.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print(
        f"real cases {out['real_cases']}  gold {out['gold_declarations']}  "
        f"correct {out['correct']}  misses {out['misses']}  spurious {out['spurious']}"
    )
    for cat, n in counts.most_common():
        print(f"  {n:3}  {n / len(misses):4.0%}  {CATEGORIES[cat]}")
    print(f"wrote {stem}_errors.json and .md")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
