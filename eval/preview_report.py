"""Render one `eval/dataset` case as a report, for looking at.

The report is the one thing in this project whose "done when" is visual — `docs/PLAN.md` says
"the PDF opens on a phone and looks clean". This runs the real pipeline (with the eval's OCR
cache) over a real case and writes the HTML, the JSON and the DOCX so they can be opened.

Run:  cd worker && uv run --extra ocr python ../eval/preview_report.py <case> [--out DIR]
      cd worker && uv run --extra ocr python ../eval/preview_report.py --list

"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "worker"))

from run_eval import DATASET, IMAGE_EXT, ROOT, cached_ocr  # noqa: E402

from pipeline import context_for, run_local  # noqa: E402
from pipeline.models import ReportImage, ScanRow, Source  # noqa: E402
from pipeline.report import (  # noqa: E402
    TEMPLATES,
    annotate_panels,
    build_report,
    render_docx,
    render_html,
    render_json,
    render_pdf,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("case", nargs="?", help="a folder name under eval/dataset")
    ap.add_argument("--list", action="store_true", help="list the cases and stop")
    ap.add_argument("--out", type=Path, default=ROOT / ".preview")
    args = ap.parse_args()

    if args.list or not args.case:
        for case in sorted(p.name for p in DATASET.iterdir() if p.is_dir()):
            print(case)
        return

    case_dir = DATASET / args.case
    images = sorted(p for p in case_dir.iterdir() if p.suffix.lower() in IMAGE_EXT)
    gold = json.loads((case_dir / "gold.json").read_text(encoding="utf-8"))
    scan = ScanRow(
        id=args.case,
        inspector_id="preview",
        source=Source(gold.get("context", {}).get("source", "package")),
        notes=f"eval/dataset/{args.case}",
    )
    ctx = context_for(scan).model_copy(update=gold.get("context", {}))

    result = run_local(images, ctx, ocr=cached_ocr(images))
    report = build_report(
        scan,
        result,
        ctx,
        [ReportImage(id=p.stem, kind=p.stem, storage_path=str(p)) for p in images],
    )
    panels = annotate_panels({p.stem: p for p in images}, report)

    args.out.mkdir(parents=True, exist_ok=True)
    html = render_html(report, panels)
    # WeasyPrint resolves the font URLs against the template directory. A browser resolves them
    # against wherever this file lands, so for the on-screen preview they are made absolute.
    (args.out / "report.html").write_text(
        html.replace('url("assets/', f'url("{TEMPLATES.as_uri()}/assets/'), encoding="utf-8"
    )
    (args.out / "report.json").write_text(render_json(report), encoding="utf-8")
    (args.out / "report.docx").write_bytes(render_docx(report, panels))
    print(f"score {report.score.value} · {report.score.status}")
    print(
        f"{len(report.violations)} violations · {len(report.unverifiable)} unverifiable · "
        f"{len(report.notes)} notes · {len(report.passed)} passed"
    )
    try:
        (args.out / "report.pdf").write_bytes(render_pdf(html))
    except Exception as e:  # noqa: BLE001 - this machine may have no GTK; the HTML is still there
        print(f"no PDF: {type(e).__name__}: {e}")
    for name in sorted(p.name for p in args.out.iterdir()):
        print(args.out / name)


if __name__ == "__main__":
    main()
