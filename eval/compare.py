"""Two result files side by side: what moved, per field and per case.

    cd worker && uv run python ../eval/compare.py ../eval/results/<a>.json ../eval/results/<b>.json

Prints the headline numbers, every per-field precision / recall / tp / fp / fn delta, and every
case whose predicted value or violation set changed, marked BETTER / WORSE / neutral against
gold. It is how a labelled run is judged: a change that raises the accuracy line while adding
false fields shows up here as WORSE rows beside the BETTER ones.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from diagnose import gold_of
from run_eval import DATASET, norm


def load(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def gold_violations(case: str) -> set[str]:
    data = json.loads((DATASET / case / "gold.json").read_text(encoding="utf-8"))
    return set(data.get("violations", []))


def main(before: Path, after: Path) -> None:
    a, b = load(before), load(after)
    print(f"{'':28} {'before':>10} {'after':>10} {'delta':>8}")
    for key in ("field_accuracy",):
        print(f"{key:28} {a[key]:10.4f} {b[key]:10.4f} {b[key] - a[key]:+8.4f}")
    for src in ("real", "synthetic"):
        x, y = a["field_accuracy_by_source"][src], b["field_accuracy_by_source"][src]
        print(f"{'  ' + src:28} {x:10.4f} {y:10.4f} {y - x:+8.4f}")
    for key in ("precision", "recall", "exact_set_accuracy"):
        x, y = a["violations"][key], b["violations"][key]
        print(f"{'violations ' + key:28} {x:10.4f} {y:10.4f} {y - x:+8.4f}")

    print(f"\n{'field':20} {'tp':>7} {'fp':>7} {'fn':>7} {'prec':>13} {'rec':>13}")
    for field in sorted(set(a["fields"]) | set(b["fields"])):
        x = a["fields"].get(field, {"tp": 0, "fp": 0, "fn": 0, "precision": 0, "recall": 0})
        y = b["fields"].get(field, {"tp": 0, "fp": 0, "fn": 0, "precision": 0, "recall": 0})
        tp, fp, fn = (f"{x[k]:3}->{y[k]:<3}" for k in ("tp", "fp", "fn"))
        moved = any(x[k] != y[k] for k in ("tp", "fp", "fn"))
        print(
            f"{field:20} {tp:>7} {fp:>7} {fn:>7} "
            f"{x['precision']:5.2f}->{y['precision']:<5.2f} {x['recall']:5.2f}->{y['recall']:<5.2f}"
            + ("   *" if moved else "")
        )

    before_cases = {c["case"]: c for c in a["per_case"]}
    better = worse = neutral = 0
    print()
    for entry in b["per_case"]:
        case = entry["case"]
        old = before_cases.get(case)
        if old is None:
            continue
        gold = gold_of(case)
        for field in sorted(set(old["pred"]) | set(entry["pred"])):
            was, now = old["pred"].get(field), entry["pred"].get(field)
            if was == now:
                continue
            want = gold.get(field)
            was_ok = want is not None and was is not None and norm(was) == norm(want)
            now_ok = want is not None and now is not None and norm(now) == norm(want)
            # a spurious field that disappeared is a win; one that appeared is a loss
            if now_ok and not was_ok:
                mark, better = "BETTER ", better + 1
            elif was_ok and not now_ok:
                mark, worse = "WORSE  ", worse + 1
            elif want is None and now is None:
                mark, better = "BETTER ", better + 1  # spurious prediction gone
            elif want is None and was is None:
                mark, worse = "WORSE  ", worse + 1  # spurious prediction new
            else:
                mark, neutral = "neutral", neutral + 1
            print(f"{mark} {case[:42]:42} {field}")
            print(f"        was  {was!r}")
            print(f"        now  {now!r}")
            print(f"        gold {want!r}")
        gv = gold_violations(case)
        ov, nv = set(old["pred_violations"]), set(entry["pred_violations"])
        if ov != nv:
            tag = "BETTER " if nv == gv else ("WORSE  " if ov == gv else "neutral")
            print(
                f"{tag} {case[:42]:42} violations {sorted(ov)} -> {sorted(nv)}  gold {sorted(gv)}"
            )
    print(f"\nfields: better {better}   worse {worse}   changed but still wrong {neutral}")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
