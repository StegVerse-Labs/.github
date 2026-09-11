#!/usr/bin/env python3
"""Build the MIR x StegVerse evaluator-facing test presentation.

The builder always emits a deterministic Markdown source. It can also emit a PDF when
ReportLab is available. Final publication fails closed unless authentic primary
execution, replay, reconstruction, and required screenshot evidence are retained.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

FINAL_REQUIRED = ("primary_execution", "replay", "reconstruction")
AUTHENTIC_STATUS = "AUTHENTIC_RETAINED"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("presentation input must be a JSON object")
    return value


def validate_input(data: dict[str, Any], final: bool = False) -> list[str]:
    errors: list[str] = []
    for field in ("schema", "title", "test_date", "experiment_id", "evidence_epoch", "abstract", "frozen_parameters"):
        if not data.get(field):
            errors.append(f"PRESENTATION_FIELD_MISSING:{field}")

    screenshots = data.get("screenshots")
    if not isinstance(screenshots, list) or not screenshots:
        errors.append("PRESENTATION_SCREENSHOTS_MISSING")
    else:
        purposes: set[str] = set()
        for index, shot in enumerate(screenshots):
            if not isinstance(shot, dict):
                errors.append(f"PRESENTATION_SCREENSHOT_INVALID:{index}")
                continue
            purpose = shot.get("purpose_id")
            if not purpose:
                errors.append(f"PRESENTATION_SCREENSHOT_PURPOSE_MISSING:{index}")
            elif purpose in purposes:
                errors.append(f"PRESENTATION_SCREENSHOT_PURPOSE_DUPLICATE:{purpose}")
            else:
                purposes.add(str(purpose))
            digest = shot.get("artifact_sha256")
            if not isinstance(digest, str) or len(digest) != 64:
                errors.append(f"PRESENTATION_SCREENSHOT_DIGEST_INVALID:{purpose or index}")

    if final:
        for section in FINAL_REQUIRED:
            value = data.get(section)
            if not isinstance(value, dict) or value.get("status") != AUTHENTIC_STATUS:
                errors.append(f"FINAL_AUTHENTIC_EVIDENCE_REQUIRED:{section}")
        required_sequence = data.get("required_screenshot_sequence", [])
        captured = {s.get("sequence_id") for s in screenshots or [] if isinstance(s, dict)}
        for sequence_id in required_sequence:
            if sequence_id not in captured:
                errors.append(f"FINAL_SCREENSHOT_REQUIRED:{sequence_id}")
    return sorted(set(errors))


def lines_for_section(title: str, body: Any) -> list[str]:
    out = [f"## {title}", ""]
    if isinstance(body, str):
        out += [body, ""]
    elif isinstance(body, dict):
        for key, value in body.items():
            label = key.replace("_", " ").title()
            if isinstance(value, (dict, list)):
                out += [f"**{label}:**", "", "```json", json.dumps(value, indent=2, sort_keys=True), "```", ""]
            else:
                out += [f"**{label}:** {value}", ""]
    elif isinstance(body, list):
        out += [f"- {item}" for item in body] + [""]
    return out


def render_markdown(data: dict[str, Any], errors: list[str]) -> str:
    status = "FINAL" if not errors and all(data.get(k, {}).get("status") == AUTHENTIC_STATUS for k in FINAL_REQUIRED) else "DRAFT / EVIDENCE INCOMPLETE"
    out = [
        f"# {data.get('title', 'MIR x StegVerse SDK Test Presentation')}",
        "",
        f"**Presentation status:** {status}",
        f"**Test date:** {data.get('test_date', '')}",
        f"**Experiment:** `{data.get('experiment_id', '')}`",
        f"**Evidence epoch:** `{data.get('evidence_epoch', '')}`",
        f"**Presentation input SHA-256:** `{sha256_json(data)}`",
        "",
    ]
    if errors:
        out += ["> This report is intentionally marked incomplete. Missing authentic evidence is not represented as completed execution.", ""]
    out += lines_for_section("Abstract", data.get("abstract", ""))
    out += lines_for_section("Test Objective and Scope", data.get("objective_and_scope", {}))
    out += lines_for_section("Frozen Test Parameters", data.get("frozen_parameters", {}))
    out += lines_for_section("End-to-End Flow Overview", data.get("flow_overview", []))
    out += lines_for_section("Primary Test Execution and Result", data.get("primary_execution", {}))
    out += lines_for_section("Replay and Result", data.get("replay", {}))
    out += lines_for_section("Reconstruction and Result", data.get("reconstruction", {}))
    out += lines_for_section("Conclusion", data.get("conclusion", {}))

    out += ["## Screenshot Walkthrough", ""]
    for shot in data.get("screenshots", []):
        out += [
            f"### {shot.get('title', shot.get('purpose_id', 'Screenshot'))}",
            "",
            f"- Sequence: `{shot.get('sequence_id', 'UNASSIGNED')}`",
            f"- Purpose ID: `{shot.get('purpose_id', '')}`",
            f"- Artifact: `{shot.get('artifact_ref', '')}`",
            f"- SHA-256: `{shot.get('artifact_sha256', '')}`",
            f"- Capture class: `{shot.get('capture_class', 'UNKNOWN')}`",
            f"- Evaluator note: {shot.get('evaluator_note', '')}",
            "",
        ]

    out += lines_for_section("Appendix A - Evidence Ledger", data.get("evidence_ledger", {}))
    out += lines_for_section("Appendix B - SDK Overview and Usage Guide", data.get("sdk_guide", {}))
    out += lines_for_section("Appendix C - Roadmap and Future Development", data.get("roadmap", {}))

    if errors:
        out += ["## Publication Gate", "", "The following conditions prevent FINAL publication:", ""]
        out += [f"- `{error}`" for error in errors] + [""]
    return "\n".join(out)


def render_pdf(data: dict[str, Any], errors: list[str], output: Path, asset_map: dict[str, str]) -> None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:
        raise SystemExit("PDF generation requires reportlab; Markdown generation remains dependency-free") from exc

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("SVTitle", parent=styles["Title"], alignment=TA_CENTER, spaceAfter=18)
    small = ParagraphStyle("SVSmall", parent=styles["BodyText"], fontSize=8, leading=10)
    doc = SimpleDocTemplate(str(output), pagesize=letter, rightMargin=0.65*inch, leftMargin=0.65*inch, topMargin=0.65*inch, bottomMargin=0.65*inch)
    story = [Paragraph(data.get("title", "MIR x StegVerse SDK Test Presentation"), title_style)]
    status = "FINAL" if not errors else "DRAFT / EVIDENCE INCOMPLETE"
    story += [Paragraph(f"<b>Status:</b> {status}", styles["Heading2"]), Paragraph(f"Experiment: {data.get('experiment_id','')}<br/>Evidence epoch: {data.get('evidence_epoch','')}<br/>Input SHA-256: {sha256_json(data)}", small), Spacer(1, 12)]
    if errors:
        warning = Table([[Paragraph("DRAFT: authentic primary execution/replay/reconstruction evidence is incomplete. No placeholder is represented as a completed result.", styles["BodyText"])]], colWidths=[7.0*inch])
        warning.setStyle(TableStyle([("BOX", (0,0), (-1,-1), 1, colors.black), ("LEFTPADDING",(0,0),(-1,-1),8), ("RIGHTPADDING",(0,0),(-1,-1),8), ("TOPPADDING",(0,0),(-1,-1),8), ("BOTTOMPADDING",(0,0),(-1,-1),8)]))
        story += [warning, Spacer(1, 14)]

    def add_section(title: str, body: Any) -> None:
        story.append(Paragraph(title, styles["Heading1"]))
        if isinstance(body, str):
            story.append(Paragraph(body.replace("\n", "<br/>"), styles["BodyText"]))
        elif isinstance(body, list):
            for item in body:
                story.append(Paragraph(f"- {item}", styles["BodyText"]))
        elif isinstance(body, dict):
            for key, value in body.items():
                label = key.replace("_", " ").title()
                rendered = json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else str(value)
                story.append(Paragraph(f"<b>{label}:</b> {rendered}", styles["BodyText"]))
        story.append(Spacer(1, 8))

    add_section("Abstract", data.get("abstract", ""))
    add_section("Test Objective and Scope", data.get("objective_and_scope", {}))
    add_section("Frozen Test Parameters", data.get("frozen_parameters", {}))
    add_section("End-to-End Flow Overview", data.get("flow_overview", []))
    add_section("Primary Test Execution and Result", data.get("primary_execution", {}))
    add_section("Replay and Result", data.get("replay", {}))
    add_section("Reconstruction and Result", data.get("reconstruction", {}))
    add_section("Conclusion", data.get("conclusion", {}))

    story.append(PageBreak())
    story.append(Paragraph("Screenshot Walkthrough", styles["Heading1"]))
    for shot in data.get("screenshots", []):
        story.append(Paragraph(shot.get("title", shot.get("purpose_id", "Screenshot")), styles["Heading2"]))
        ref = shot.get("artifact_ref", "")
        local = asset_map.get(ref)
        if local and Path(local).exists():
            img = Image(local)
            max_w, max_h = 7.0*inch, 5.6*inch
            scale = min(max_w / img.imageWidth, max_h / img.imageHeight, 1.0)
            img.drawWidth = img.imageWidth * scale
            img.drawHeight = img.imageHeight * scale
            story += [img, Spacer(1, 6)]
        else:
            story.append(Paragraph(f"Image not materialized in this build; retained reference: {ref}", small))
        story.append(Paragraph(f"Purpose: {shot.get('purpose_id','')}<br/>SHA-256: {shot.get('artifact_sha256','')}<br/>Evaluator note: {shot.get('evaluator_note','')}", small))
        story.append(Spacer(1, 12))

    add_section("Appendix A - Evidence Ledger", data.get("evidence_ledger", {}))
    add_section("Appendix B - SDK Overview and Usage Guide", data.get("sdk_guide", {}))
    add_section("Appendix C - Roadmap and Future Development", data.get("roadmap", {}))
    if errors:
        add_section("Publication Gate", errors)
    doc.build(story)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--format", choices=("md", "pdf"), default="md")
    parser.add_argument("--asset-map", type=Path)
    parser.add_argument("--final", action="store_true", help="fail unless authentic primary/replay/reconstruction evidence and required screenshots are retained")
    args = parser.parse_args()

    data = load_json(args.input)
    errors = validate_input(data, final=args.final)
    if args.final and errors:
        print(json.dumps({"valid": False, "errors": errors}, indent=2, sort_keys=True))
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.format == "md":
        args.output.write_text(render_markdown(data, errors), encoding="utf-8")
    else:
        asset_map = load_json(args.asset_map) if args.asset_map else {}
        render_pdf(data, errors, args.output, asset_map)
    print(json.dumps({"valid": not errors, "errors": errors, "output": str(args.output), "input_sha256": sha256_json(data)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
