#!/usr/bin/env python3
"""Export docs/sprint-3-feasibility.md to docs/Sprint3Deliverable_TeamAdDiagnose.pdf.

Requires: pip install reportlab
Alternative: pandoc docs/sprint-3-feasibility.md -o docs/Sprint3Deliverable_TeamAdDiagnose.pdf
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "sprint-3-feasibility.md"
OUT = ROOT / "docs" / "Sprint3Deliverable_TeamAdDiagnose.pdf"


def main() -> int:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except ImportError:
        print("Install reportlab: pip install reportlab", file=sys.stderr)
        return 1

    md = SRC.read_text()
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="BodySmall", parent=styles["Normal"], fontSize=9.5, leading=12.5, spaceAfter=4
        )
    )
    styles.add(
        ParagraphStyle(
            name="H1Custom", parent=styles["Heading1"], fontSize=13, leading=16, spaceAfter=8
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2Custom", parent=styles["Heading2"], fontSize=11.5, leading=14, spaceAfter=6, spaceBefore=10
        )
    )
    styles.add(
        ParagraphStyle(
            name="H3Custom", parent=styles["Heading3"], fontSize=10.5, leading=13, spaceAfter=4, spaceBefore=8
        )
    )
    styles.add(
        ParagraphStyle(
            name="Quote",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            leftIndent=10,
            textColor="#333333",
            spaceAfter=6,
        )
    )

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
    )
    story: list = []
    in_code = False
    code_lines: list[str] = []

    def flush_code() -> None:
        nonlocal code_lines
        if code_lines:
            story.append(
                Paragraph(
                    '<font face="Courier" size="8">'
                    + html.escape("\n".join(code_lines)).replace("\n", "<br/>")
                    + "</font>",
                    styles["BodySmall"],
                )
            )
            code_lines = []

    def fmt_inline(s: str) -> str:
        s = html.escape(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"`(.+?)`", r'<font face="Courier" size="8">\1</font>', s)
        return s

    for line in md.splitlines():
        if line.startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if line.startswith("# "):
            story.append(Paragraph(fmt_inline(line[2:]), styles["H1Custom"]))
        elif line.startswith("## "):
            story.append(Paragraph(fmt_inline(line[3:]), styles["H2Custom"]))
        elif line.startswith("### "):
            story.append(Paragraph(fmt_inline(line[4:]), styles["H3Custom"]))
        elif line.startswith("|") and re.fullmatch(r"[\|\s:\-]+", line):
            continue
        elif line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            story.append(Paragraph(fmt_inline(" | ".join(cells)), styles["BodySmall"]))
        elif line.startswith("- "):
            story.append(Paragraph("• " + fmt_inline(line[2:]), styles["BodySmall"]))
        elif line.strip() == "---":
            story.append(Spacer(1, 6))
        elif line.strip() == "":
            story.append(Spacer(1, 3))
        elif line.startswith("> "):
            story.append(Paragraph(fmt_inline(line[2:]), styles["Quote"]))
        else:
            story.append(Paragraph(fmt_inline(line), styles["BodySmall"]))

    flush_code()
    doc.build(story)
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
