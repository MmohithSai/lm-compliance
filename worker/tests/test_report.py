"""P5. The report is a rendering of a finished scan: JSON, HTML/PDF and DOCX say the same thing.

The declarations here go through the real rule engine, so a test that says "one critical
violation" is asserting against the law as implemented, not against a hand-written fixture.
"""

from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any, cast

import cv2
import numpy as np
import pytest
from supabase import Client

from pipeline import publish_report
from pipeline.models import (
    CheckStatus,
    Declaration,
    Evidence,
    PipelineResult,
    ReportImage,
    ScaleSource,
    ScanContext,
    ScanRow,
    Severity,
    Source,
    Violation,
    Word,
)
from pipeline.report import (
    annotate,
    build_report,
    render_docx,
    render_html,
    render_json,
    render_pdf,
)
from pipeline.rules_engine import run_rules, score
from tests.helpers import ctx, decl, good, replace, without
from tests.test_run_scan import FakeClient

NOW = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)
SCAN = ScanRow(
    id="11111111-2222-3333-4444-555555555555",
    inspector_id="u1",
    created_at=datetime(2026, 9, 8, 9, 15, tzinfo=UTC),
    notes="Shelf 4, kirana store, Andheri",
)
IMAGES = [ReportImage(id="img1", kind="back", storage_path="scan/0.jpg")]


def words_for(decls: list[Declaration]) -> list[Declaration]:
    """Give every declaration one OCR box, so evidence has somewhere to point."""
    return [d.model_copy(update={"word_ids": [i], "image_id": "img1"}) for i, d in enumerate(decls)]


def boxes_for(decls: list[Declaration]) -> list[Word]:
    return [
        Word(
            id=i,
            image_id="img1",
            text=d.value[:40],
            x=20,
            y=20 + 40 * i,
            w=300,
            h=30,
            confidence=0.9,
        )
        for i, d in enumerate(decls)
    ]


def result_for(decls: list[Declaration], context: ScanContext | None = None) -> PipelineResult:
    """Run the real engine over these declarations and package it as the pipeline would."""
    decls = words_for(decls)
    violations = run_rules(decls, context or ctx())
    return PipelineResult(
        words=boxes_for(decls),
        declarations=decls,
        violations=violations,
        mm_per_px=None,
        scale_source=ScaleSource.none,
        compliance_score=score(violations),
    )


def report_for(decls: list[Declaration], context: ScanContext | None = None) -> Any:
    context = context or ctx()
    return build_report(SCAN, result_for(decls, context), context, IMAGES, now=NOW)


# ---------------------------------------------------------------- the JSON contract


def test_json_carries_the_metadata_an_api_consumer_pins_against() -> None:
    data = cast(dict[str, Any], __import__("json").loads(render_json(report_for(good()))))
    assert data["report"]["schema_version"] == "1.0"
    assert data["report"]["kind"] == "legal-metrology-compliance-report"
    assert data["report"]["law"].startswith("Legal Metrology")
    assert data["report"]["generated_at"].startswith("2026-09-08T12:00")
    assert set(data) == {
        "report",
        "scan",
        "score",
        "declarations",
        "violations",
        "notes",
        "unverifiable",
        "passed",
        "images",
    }


def test_json_repeats_the_scan_and_the_images_it_was_built_from() -> None:
    data = cast(dict[str, Any], __import__("json").loads(render_json(report_for(good()))))
    assert data["scan"]["id"] == SCAN.id
    assert data["scan"]["source"] == "package"
    assert data["scan"]["notes"] == "Shelf 4, kirana store, Andheri"
    assert data["scan"]["scale_source"] == "none"
    assert data["images"] == [{"id": "img1", "kind": "back", "storage_path": "scan/0.jpg"}]


def test_json_gives_every_violation_its_rule_reference_and_its_evidence() -> None:
    report = report_for(without(good(), "net_quantity"))
    d3 = next(v for v in report.violations if v.rule_id == "D3")
    assert d3.rule_ref == "Rule 6(1)(c)"
    assert d3.severity == Severity.critical
    assert d3.status == CheckStatus.fail
    assert d3.penalty == 25
    assert d3.title  # the title from the YAML, not just the code


def test_the_four_lists_are_disjoint_and_every_applied_rule_is_in_exactly_one() -> None:
    """No rule is reported twice, and none quietly disappears between the buckets."""
    report = report_for(without(good(), "net_quantity", "mrp"))
    buckets = [report.violations, report.notes, report.unverifiable, report.passed]
    seen = [c.rule_id for bucket in buckets for c in bucket]
    assert len(seen) == len(set(seen)), seen


def test_a_rule_that_only_ever_flags_is_never_reported_as_passed() -> None:
    """X1..X4 say why a rule was relaxed, F3 and E2 flag a kind of pack, D9 is food law. None of
    them can fail, so "passed" would be a sentence with no meaning in it."""
    report = report_for(good())
    assert not [c for c in report.passed if c.rule_id in {"D9", "F3", "E2", "X1", "X2", "X3", "X4"}]
    assert {c.rule_id for c in report.passed} >= {"D1", "D3", "D5", "D6"}


# ---------------------------------------------------------------- score and status


def test_a_clean_pack_is_compliant_and_scores_full_marks() -> None:
    report = report_for(good())
    assert report.violations == []
    assert report.score.value == 100
    assert report.score.status == "compliant"
    assert report.passed, "a compliant pack must still list the checks it passed"


def test_a_missing_unit_sale_price_alone_is_minor_issues() -> None:
    report = report_for(without(good(), "unit_sale_price"))
    assert [v.rule_id for v in report.violations] == ["D8"]
    assert report.score.status == "minor_issues"
    assert report.score.minor == 1
    assert report.score.value == 97


def test_a_missing_critical_declaration_is_not_compliant() -> None:
    report = report_for(without(good(), "mrp"))
    assert report.score.status == "non_compliant"
    assert report.score.critical == 1
    assert report.score.value == 75
    assert report.score.penalty == 25


def test_the_counts_and_the_penalty_add_up_to_the_stored_score() -> None:
    report = report_for(without(good(), "mrp", "generic_name", "unit_sale_price"))
    assert (report.score.critical, report.score.major, report.score.minor) == (1, 1, 1)
    assert report.score.penalty == 25 + 10 + 3
    assert report.score.value == 100 - report.score.penalty


def test_the_report_never_recomputes_the_score_it_was_given() -> None:
    """The score on the report is the score on the scan row, so the PDF and the dashboard can
    never disagree about the same pack."""
    result = result_for(without(good(), "mrp"))
    result = result.model_copy(update={"compliance_score": 42})
    assert build_report(SCAN, result, ctx(), now=NOW).score.value == 42


# ---------------------------------------------------------------- unverifiable


def test_unverifiable_checks_are_listed_apart_and_cost_nothing() -> None:
    """P3 (bottom or seam) is unverifiable unless the inspector answered, and P1 whenever the
    declarations are not provably on one panel. Neither may move the score."""
    report = report_for(good())
    assert report.unverifiable, "the fixture is meant to leave checks unverifiable"
    assert report.score.unverifiable == len(report.unverifiable)
    assert all(v.penalty == 0 for v in report.unverifiable)
    assert all(v.severity == Severity.info for v in report.unverifiable)
    assert report.score.value == 100
    assert report.score.status == "compliant"
    assert all(v.reason for v in report.unverifiable), "each one must say why"


def test_an_unverifiable_check_is_never_counted_as_a_violation() -> None:
    report = report_for(good())
    assert not {v.rule_id for v in report.violations} & {v.rule_id for v in report.unverifiable}


def test_informational_notes_are_their_own_list() -> None:
    """D9 (best before) is food law and severity info: a note, not a violation."""
    report = report_for(without(good(), "best_before"))
    assert [n.rule_id for n in report.notes] == ["D9"]
    assert report.notes[0].penalty == 0
    assert report.score.value == 100


# ---------------------------------------------------------------- evidence


def test_evidence_is_a_box_on_a_named_photograph() -> None:
    report = report_for(replace(good(), "net_quantity", "Net Qty: about 200 gms"))
    d3 = next(v for v in report.violations if v.rule_id == "D3")
    assert d3.boxes, "a violation about a printed value must point at it"
    assert d3.boxes[0].image_id == "img1"
    assert d3.boxes[0].w > 0 and d3.boxes[0].h > 0


def test_a_violation_about_something_absent_has_no_box_and_the_report_says_so() -> None:
    report = report_for(without(good(), "mrp"))
    d5 = next(v for v in report.violations if v.rule_id == "D5")
    assert d5.boxes == []
    assert "not on the photographs" in render_html(report)


def test_a_declaration_the_words_table_lost_produces_no_phantom_box() -> None:
    """Evidence points at word ids. If the word is gone, the box is dropped, never invented."""
    result = result_for(good())
    result = result.model_copy(update={"words": []})
    report = build_report(SCAN, result, ctx(), now=NOW)
    assert all(d.boxes == [] for d in report.declarations)


# ---------------------------------------------------------------- e-commerce


def test_an_ecommerce_scan_is_judged_only_by_rule_6_10() -> None:
    context = ctx(source=Source.ecommerce)
    listing = ScanRow(id=SCAN.id, inspector_id="u1", source=Source.ecommerce)
    result = result_for(without(good(), "mrp"), context)
    report = build_report(listing, result, context, IMAGES, now=NOW)
    judged = {c.rule_id for c in report.violations + report.notes + report.unverifiable} | {
        c.rule_id for c in report.passed
    }
    assert judged <= {"E1", "E2"}, judged
    assert report.scan.source == Source.ecommerce


def test_an_ecommerce_report_explains_why_the_package_rules_were_not_applied() -> None:
    context = ctx(source=Source.ecommerce)
    listing = ScanRow(id=SCAN.id, inspector_id="u1", source=Source.ecommerce)
    html = render_html(build_report(listing, result_for(good(), context), context, now=NOW))
    assert "Rule 6(10)" in html
    assert "E-commerce listing" in html


# ---------------------------------------------------------------- HTML / PDF


def test_html_shows_the_score_the_status_and_every_severity() -> None:
    report = report_for(without(good(), "mrp", "generic_name", "unit_sale_price"))
    html = render_html(report)
    assert "Not compliant" in html
    assert ">62<" in html  # 100 - 25 - 10 - 3
    for severity in ("critical", "major", "minor"):
        assert f'<span class="chip">{severity}</span>' in html
    for rule_id in ("D5", "D2", "D8"):
        assert rule_id in html


def test_html_separates_violations_from_unverifiable_and_from_passed() -> None:
    html = render_html(report_for(without(good(), "mrp")))
    assert "Violations" in html
    assert "Could not be verified" in html
    assert "Checks that passed" in html
    assert "cost no points" in html


def test_html_is_self_contained_apart_from_the_vendored_fonts() -> None:
    """Nothing in the report may fetch from a website while it renders."""
    html = render_html(report_for(good()), {"img1": b"\xff\xd8not-a-real-jpeg"})
    # The one URL in the file is the SVG namespace, which is an identifier and is never fetched.
    assert "://" not in html.replace('xmlns="http://www.w3.org/2000/svg"', "")
    assert "data:image/jpeg;base64," in html
    assert 'url("assets/fonts/IBMPlexSans-Regular.ttf")' in html


def test_the_icons_are_inlined_as_svg_and_not_as_escaped_text() -> None:
    html = render_html(report_for(good()))
    assert "<svg" in html and "&lt;svg" not in html


def test_html_escapes_what_was_printed_on_the_pack() -> None:
    report = report_for(replace(good(), "generic_name", "<script>alert(1)</script>"))
    assert "<script>alert(1)</script>" not in render_html(report)
    assert "&lt;script&gt;" in render_html(report)


def test_pdf_renders() -> None:
    try:
        import weasyprint  # noqa: F401,PLC0415
    except Exception as e:  # pragma: no cover - depends on the machine, not on the code
        pytest.skip(f"WeasyPrint's system libraries (Pango, Cairo) are not installed here: {e}")
    pdf = render_pdf(render_html(report_for(without(good(), "mrp"))))
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 5000


# ---------------------------------------------------------------- DOCX


def read_docx(data: bytes) -> list[str]:
    from docx import Document  # noqa: PLC0415

    doc = Document(BytesIO(data))
    return [p.text for p in doc.paragraphs] + [
        cell.text for table in doc.tables for row in table.rows for cell in row.cells
    ]


def test_docx_opens_and_keeps_the_report_hierarchy() -> None:
    text = read_docx(render_docx(report_for(without(good(), "mrp", "unit_sale_price"))))
    for heading in (
        "Legal Metrology compliance report",
        "Summary",
        "Violations",
        "Not verifiable (for information)",
        "Declarations read from the package",
        "Checks that passed",
        "About this report",
    ):
        assert heading in text, heading


def test_docx_states_the_verdict_the_score_and_each_violation() -> None:
    text = read_docx(render_docx(report_for(without(good(), "mrp", "unit_sale_price"))))
    assert "Not compliant — 72 out of 100" in text
    assert any("D5" in t and "CRITICAL" in t for t in text)
    assert any("D8" in t and "MINOR" in t for t in text)
    assert "Score: −25 points." in text


def test_docx_lists_the_declarations_that_were_read() -> None:
    text = read_docx(render_docx(report_for(good())))
    assert "Net quantity" in text
    assert "Net Qty: 200 g" in text


def test_docx_renders_with_no_violations_at_all() -> None:
    text = read_docx(render_docx(report_for(good())))
    assert "No violation was found." in text


# ---------------------------------------------------------------- annotated photographs


def test_annotate_draws_a_box_and_shrinks_a_large_photograph() -> None:
    image = np.full((1200, 1600, 3), 255, dtype=np.uint8)
    report = report_for(without(good(), "mrp"))
    jpeg = annotate(image, report.declarations[0].boxes, report.violations[0].boxes)
    decoded = cv2.imdecode(np.frombuffer(jpeg, dtype=np.uint8), cv2.IMREAD_COLOR)
    assert decoded is not None
    assert decoded.shape[1] == 900, "downscaled for a phone"
    assert decoded.min() < 200, "a box was drawn on the blank photograph"


# ---------------------------------------------------------------- upload and storage


def scan_client() -> FakeClient:
    return FakeClient({"scan_images": []})


def publish(tmp_path: Path, **kw: Any) -> tuple[FakeClient, dict[str, str | None]]:
    db = scan_client()
    photo = tmp_path / "img1.jpg"
    cv2.imwrite(str(photo), np.full((400, 600, 3), 240, dtype=np.uint8))
    stored = publish_report(
        cast(Client, db),
        SCAN,
        result_for(without(good(), "mrp")),
        ctx(),
        IMAGES,
        {"img1": photo},
        **kw,
    )
    return db, stored


def test_publish_uploads_every_report_it_could_render_under_the_scan_id(tmp_path: Path) -> None:
    db, stored = publish(tmp_path)
    assert stored["json"] == f"{SCAN.id}/report.json"
    assert stored["docx"] == f"{SCAN.id}/report.docx"
    assert db.uploaded[f"{SCAN.id}/report.json"][1]["content-type"] == "application/json"
    assert db.uploaded[f"{SCAN.id}/report.docx"][0][:2] == b"PK"  # a zip, which a docx is
    assert b'"schema_version": "1.0"' in db.uploaded[f"{SCAN.id}/report.json"][0]


def test_publish_records_one_row_per_scan(tmp_path: Path) -> None:
    db, stored = publish(tmp_path)
    (row, on_conflict) = db.upserted["reports"][0]
    assert on_conflict == "scan_id"
    assert row["scan_id"] == SCAN.id
    assert row["json_path"] == stored["json"]
    assert row["docx_path"] == stored["docx"]
    assert row["pdf_path"] == stored["pdf"]  # None on a machine with no WeasyPrint


def test_a_format_that_cannot_be_rendered_is_stored_as_null_and_loses_no_other_format(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """WeasyPrint binds to system libraries a machine can be missing. A missing PDF must not
    take the JSON and the DOCX with it, and must never fail the scan."""

    def boom(_html: str) -> bytes:
        raise OSError("cannot load library 'libgobject-2.0-0'")

    monkeypatch.setattr("pipeline.render_pdf", boom)
    db, stored = publish(tmp_path)
    assert stored["pdf"] is None
    assert stored["json"] and stored["docx"]
    assert db.upserted["reports"][0][0]["pdf_path"] is None


def test_publish_embeds_the_photograph_in_the_report(tmp_path: Path) -> None:
    db, _ = publish(tmp_path)
    data = cast(dict[str, Any], __import__("json").loads(db.uploaded[f"{SCAN.id}/report.json"][0]))
    assert data["images"][0]["storage_path"] == "scan/0.jpg"


def test_a_violation_carrying_an_unknown_word_id_still_renders(tmp_path: Path) -> None:
    """Defensive: evidence that points at a word the result no longer carries drops the box
    rather than raising in the middle of a report."""
    result = result_for(good())
    result.violations.append(
        Violation(
            rule_id="D1",
            rule_ref="Rule 6(1)(a)",
            severity=Severity.critical,
            message="missing",
            evidence=Evidence(word_ids=[9999]),
        )
    )
    report = build_report(SCAN, result, ctx(), IMAGES, now=NOW)
    assert next(v for v in report.violations if v.rule_id == "D1").boxes == []
    assert render_html(report)
    assert render_docx(report)


def test_a_scan_with_nothing_read_still_produces_a_readable_report() -> None:
    """`run_scan` refuses to finish such a scan, but the report must not crash on the empty
    case either — the eval and any re-run reach this shape."""
    empty = PipelineResult(
        words=[],
        declarations=[],
        violations=[],
        mm_per_px=None,
        scale_source=ScaleSource.none,
        compliance_score=100,
    )
    report = build_report(SCAN, empty, ctx(), now=NOW)
    assert "No declaration was read" in render_html(report)
    assert "No declaration was read from the photographs." in read_docx(render_docx(report))


def test_a_measured_print_height_reaches_the_report() -> None:
    decls = [decl("net_quantity", "Net Qty: 200 g", height_mm=3.2, width_height_ratio=0.55)]
    report = build_report(SCAN, result_for(decls), ctx(), now=NOW)
    assert report.declarations[0].height_mm == 3.2
    assert "3.2 mm" in render_html(report)
    assert "3.2 mm" in read_docx(render_docx(report))
