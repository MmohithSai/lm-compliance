"""Look at what the pipeline saw and where a run lost points. Reads the OCR cache, never OCRs.

(Not named inspect.py: that shadows the stdlib module numpy imports on the way up.)

    cd worker && uv run python ../eval/diagnose.py text   kinley          # what PP-OCR read
    cd worker && uv run python ../eval/diagnose.py boxes  kinley 2_nutr   # ...with coordinates
    cd worker && uv run python ../eval/diagnose.py misses ../eval/results/2026-09-07_p2-final.json
    cd worker && uv run python ../eval/diagnose.py reach  ../eval/results/2026-09-07_p2-final.json

`misses` prints gold against prediction for every field a run got wrong. `reach` splits those
misses in two: the ones where the words were in the OCR output and the extractor did not use
them, and the ones PaddleOCR never read at all. That split is what says whether the next hour
belongs in the extractor or in the OCR settings — on 2026-09-07 it was 81 against 7, which is
why `det_limit_side_len` was tried, measured and reverted instead of assumed.

Everything here is a finding aid. Gold is written by reading the photograph — see
eval/dataset/README.md.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from run_eval import CACHE, DATASET, FINGERPRINT, norm


def cached_words(image: Path, langs: str = "en") -> list[dict[str, Any]] | None:
    """The boxes `run_eval` stored for this image, or None if it was never read this way."""
    stat = image.stat()
    key = f"{image}|{stat.st_mtime_ns}|{stat.st_size}|{langs}|{FINGERPRINT}"
    entry = CACHE / f"{hashlib.sha256(key.encode()).hexdigest()[:32]}.json"
    if not entry.exists():
        return None
    words: list[dict[str, Any]] = json.loads(entry.read_text(encoding="utf-8"))
    return words


def cases(match: str = "") -> list[Path]:
    return sorted(p for p in DATASET.iterdir() if p.is_dir() and match in p.name)


def show(match: str, image_match: str, with_boxes: bool) -> None:
    for case in cases(match):
        for image in sorted(case.glob("*.jpg")):
            if image_match and image_match not in image.name:
                continue
            words = cached_words(image)
            if words is None:
                print(f"--- {case.name}/{image.name}: not in the cache; run the eval first")
                continue
            print(f"--- {case.name}/{image.name}")
            if with_boxes:
                for w in words:
                    print(f"  x={w['x']:5} y={w['y']:5} w={w['w']:5} h={w['h']:4}  {w['text']}")
            else:
                print("  " + " | ".join(w["text"] for w in words))


def gold_of(case: str) -> dict[str, str]:
    data = json.loads((DATASET / case / "gold.json").read_text(encoding="utf-8"))
    declarations: dict[str, str] = data.get("declarations", {})
    return declarations


def misses(result_path: Path) -> None:
    result = json.loads(result_path.read_text(encoding="utf-8"))
    for entry in result["per_case"]:
        case, pred = entry["case"], entry["pred"]
        gold = gold_of(case)
        lines = []
        for field in sorted(set(gold) | set(pred)):
            want, got = gold.get(field), pred.get(field)
            if want is not None and got is not None and norm(want) == norm(got):
                continue
            lines.append(f"  {field}\n    gold {want}\n    pred {got}")
        if lines:
            print(case)
            print("\n".join(lines))


def reach(result_path: Path) -> None:
    """Split the misses: did the OCR text hold the answer, or was it never read?

    Real cases only — a rendered label is not the question this answers. `norm` drops spaces, so
    the gold is split into words *before* normalising and each word is looked for in the page's
    normalised text; normalising first would leave one long token that never matches.
    """
    result = json.loads(result_path.read_text(encoding="utf-8"))
    per_field: dict[str, list[int]] = {}
    for entry in result["per_case"]:
        case, pred = entry["case"], entry["pred"]
        if case.startswith("synthetic"):
            continue
        text = norm(
            " ".join(
                w["text"]
                for image in sorted((DATASET / case).glob("*.jpg"))
                for w in (cached_words(image) or [])
            )
        )
        for field, want in gold_of(case).items():
            if field in pred and norm(pred[field]) == norm(want):
                continue
            # a loose test on purpose: half the gold words surviving anywhere in the case is
            # enough to say the extractor had something to work with
            tokens = [t for t in (norm(w) for w in want.split()) if t]
            found = sum(1 for t in tokens if t in text)
            per_field.setdefault(field, [0, 0])[0 if found >= max(1, len(tokens) // 2) else 1] += 1

    print(f"{'field':20} {'extractor could':>15} {'ocr never read it':>19}")
    totals = [0, 0]
    for field, (reachable, blind) in sorted(per_field.items()):
        print(f"{field:20} {reachable:15} {blind:19}")
        totals[0] += reachable
        totals[1] += blind
    print(f"{'TOTAL':20} {totals[0]:15} {totals[1]:19}")


def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        raise SystemExit(2)
    command, target = sys.argv[1], sys.argv[2]
    image_match = sys.argv[3] if len(sys.argv) > 3 else ""
    if command in ("text", "boxes"):
        show(target, image_match, with_boxes=command == "boxes")
    elif command in ("misses", "reach"):
        (misses if command == "misses" else reach)(Path(target))
    else:
        print(__doc__)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
