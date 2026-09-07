"""Eval harness. Measures field extraction (precision/recall per field) and violation accuracy.

Run:  cd worker && uv run python ../eval/run_eval.py --label baseline-v1
Data: eval/dataset/<case>/gold.json + image files (see eval/dataset/README.md).
Out:  eval/results/<date>_<label>.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import date
from importlib import import_module
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from pipeline import run_local
from pipeline.models import PipelineResult, ScanContext, Word
from pipeline.ocr import ocr_words

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "dataset"
RESULTS = ROOT / "results"
CACHE = ROOT / ".ocr_cache"
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def pipeline_fingerprint() -> str:
    """Hash of the code that produces the boxes. Edit preprocess or ocr and the cache misses.

    `import_module`, not `pipeline.preprocess`: the package re-exports a *function* of that name,
    which shadows the module it lives in.
    """
    src = b"".join(
        Path(import_module(f"pipeline.{name}").__file__ or "").read_bytes()
        for name in ("preprocess", "ocr")
    )
    return hashlib.sha256(src).hexdigest()[:12]


FINGERPRINT = pipeline_fingerprint()


def cached_ocr(images: list[Path]) -> Any:
    """`run_local`'s OCR step, memoised on disk per image.

    PaddleOCR on the real set is about 15 s a case, which makes "one variable per run" cost an
    hour a run. The boxes only depend on the file and on preprocess/ocr, so they are cached on
    (path, mtime, size, languages, code fingerprint) — change any of those and it re-reads.
    """
    by_id = {p.stem: p for p in images}  # run_local hands us image_id, not the path

    def run(_img: NDArray[np.uint8], image_id: str, langs: list[str]) -> list[Word]:
        path = by_id[image_id]
        stat = path.stat()
        key = f"{path}|{stat.st_mtime_ns}|{stat.st_size}|{','.join(langs)}|{FINGERPRINT}"
        entry = CACHE / f"{hashlib.sha256(key.encode()).hexdigest()[:32]}.json"
        if entry.exists():
            return [Word.model_validate(w) for w in json.loads(entry.read_text(encoding="utf-8"))]
        words = ocr_words(_img, image_id, langs)
        CACHE.mkdir(exist_ok=True)
        entry.write_text(
            json.dumps([w.model_dump() for w in words], ensure_ascii=False), encoding="utf-8"
        )
        return words

    return run


# None of PP-OCR's 56 dictionaries contains ₹, so no model it ships can ever emit one. Held
# against gold it fails every price line identically and says nothing about extraction, so the
# marker is folded away on both sides: "MRP ₹20.00" and "MRP 20.00" compare equal.
CURRENCY = re.compile(r"(?:₹|rs\.?|inr)\s*(?=\d)", re.IGNORECASE)


# A dot between digits is a decimal point and has to match; any other dot is punctuation,
# which eval/dataset/README.md says is ignored. Without this "MIDC. Pune" (OCR read the comma
# as a stop) fails a manufacturer address that is otherwise word for word correct.
SENTENCE_DOT = re.compile(r"(?<!\d)\.|\.(?!\d)")


def norm(s: str) -> str:
    """Loose text equality: casefold, fold the currency marker, drop punctuation and spacing.

    eval/dataset/README.md has said from the start that spacing is ignored, but *collapsing* runs
    of spaces is not the same as ignoring them: gold "NET WEIGHT 64 g" failed a correct read of
    "NET WEIGHT 64g", because PP-OCR does not put a space back where the print had one. Dropping
    every space is what the README promises. It cannot merge two different values: "1C g" and
    "10 g" stay different.
    """
    text = SENTENCE_DOT.sub(" ", CURRENCY.sub("", s))
    return re.sub(r"[^\w@./-]", " ", text).casefold().replace(" ", "")


def load_cases() -> list[tuple[str, list[Path], dict[str, Any]]]:
    cases = []
    for case_dir in sorted(p for p in DATASET.iterdir() if p.is_dir()):
        gold_path = case_dir / "gold.json"
        if not gold_path.exists():
            continue
        images = sorted(p for p in case_dir.iterdir() if p.suffix.lower() in IMAGE_EXT)
        cases.append((case_dir.name, images, json.loads(gold_path.read_text(encoding="utf-8"))))
    return cases


def predict(images: list[Path], gold: dict[str, Any]) -> PipelineResult | None:
    ctx = ScanContext.model_validate(gold.get("context", {}))
    try:
        return run_local(images, ctx, ocr=cached_ocr(images))
    except NotImplementedError:
        return None  # pipeline not built yet: counts as "predicted nothing"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, help="what changed, e.g. baseline-v1")
    args = ap.parse_args()

    cases = load_cases()
    tp: Counter[str] = Counter()
    fp: Counter[str] = Counter()
    fn: Counter[str] = Counter()
    v_tp = v_fp = v_fn = 0
    exact_violation_sets = 0
    ran = 0  # cases where the pipeline actually produced a result
    split: dict[str, Counter[str]] = {"real": Counter(), "synthetic": Counter()}
    per_case: list[dict[str, Any]] = []

    for name, images, gold in cases:
        result = predict(images, gold)
        ran += result is not None
        pred_fields = {d.field: d.value for d in result.declarations} if result else {}
        gold_fields: dict[str, str] = gold.get("declarations", {})
        for field, value in gold_fields.items():
            if field in pred_fields and norm(pred_fields[field]) == norm(value):
                tp[field] += 1
            else:
                fn[field] += 1
        for field in pred_fields:
            if field not in gold_fields or norm(pred_fields[field]) != norm(gold_fields[field]):
                fp[field] += 1

        pred_v = {v.rule_id for v in result.violations if v.severity != "info"} if result else set()
        gold_v = set(gold.get("violations", []))
        v_tp += len(pred_v & gold_v)
        v_fp += len(pred_v - gold_v)
        v_fn += len(gold_v - pred_v)
        exact_violation_sets += pred_v == gold_v
        hits = sum(
            1
            for f, v in gold_fields.items()
            if f in pred_fields and norm(pred_fields[f]) == norm(v)
        )
        split[  # a rendered label and a phone photo are different problems; report them apart
            "synthetic" if name.startswith("synthetic") else "real"
        ] += Counter({"tp": hits, "gold": len(gold_fields)})
        per_case.append({"case": name, "pred": pred_fields, "pred_violations": sorted(pred_v)})

    fields = sorted(set(tp) | set(fp) | set(fn))
    table = {
        f: {
            "precision": tp[f] / (tp[f] + fp[f]) if tp[f] + fp[f] else 0.0,
            "recall": tp[f] / (tp[f] + fn[f]) if tp[f] + fn[f] else 0.0,
            "tp": tp[f],
            "fp": fp[f],
            "fn": fn[f],
        }
        for f in fields
    }
    total_gold = sum(tp.values()) + sum(fn.values())
    field_accuracy = sum(tp.values()) / total_gold if total_gold else 0.0
    violations = {
        "precision": v_tp / (v_tp + v_fp) if v_tp + v_fp else 0.0,
        "recall": v_tp / (v_tp + v_fn) if v_tp + v_fn else 0.0,
        # denominator = cases the pipeline ran on, so an unbuilt
        # pipeline cannot "pass" the compliant cases
        "exact_set_accuracy": exact_violation_sets / ran if ran else 0.0,
    }

    print(f"cases: {len(cases)} (pipeline ran on {ran})   label: {args.label}")
    print(f"{'field':20} {'prec':>6} {'rec':>6} {'tp':>4} {'fp':>4} {'fn':>4}")
    for f, r in table.items():
        counts = f"{r['tp']:4} {r['fp']:4} {r['fn']:4}"
        print(f"{f:20} {r['precision']:6.2f} {r['recall']:6.2f} {counts}")
    by_source = {k: (c["tp"] / c["gold"] if c["gold"] else 0.0) for k, c in split.items()}
    print(f"field extraction accuracy: {field_accuracy:.1%}")
    for source, acc in by_source.items():
        c = split[source]
        print(f"  {source:10} {acc:6.1%}  ({c['tp']}/{c['gold']} declarations)")
    print(
        f"violations: precision {violations['precision']:.2f}  recall {violations['recall']:.2f}  "
        f"exact-set accuracy {violations['exact_set_accuracy']:.1%}"
    )

    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / f"{date.today().isoformat()}_{args.label}.json"
    out.write_text(
        json.dumps(
            {
                "label": args.label,
                "date": date.today().isoformat(),
                "cases": len(cases),
                "field_accuracy": field_accuracy,
                "field_accuracy_by_source": by_source,
                "fields": table,
                "violations": violations,
                "per_case": per_case,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"wrote {out.relative_to(ROOT.parent)}")
    sys.exit(0)


if __name__ == "__main__":
    main()
