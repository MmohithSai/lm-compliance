"""Eval harness. Measures field extraction (precision/recall per field) and violation accuracy.

Run:  cd worker && uv run python ../eval/run_eval.py --label baseline-v1
Data: eval/dataset/<case>/gold.json + image files (see eval/dataset/README.md).
Out:  eval/results/<date>_<label>.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from pipeline import run_local
from pipeline.models import PipelineResult, ScanContext

ROOT = Path(__file__).resolve().parent
DATASET = ROOT / "dataset"
RESULTS = ROOT / "results"
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def norm(s: str) -> str:
    """Loose text equality: casefold, drop punctuation except ₹ @ . / -, collapse spaces."""
    return " ".join(re.sub(r"[^\w₹@./-]", " ", s).casefold().split())


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
        return run_local(images, ctx)
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
    print(f"field extraction accuracy: {field_accuracy:.1%}")
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
