"""Render docs/memo.md to the Word version, so the two cannot drift apart.

docs/memo.md is the source of truth. This script reads it and writes
docs/Memo - Massachusetts Homelessness.docx, handling the Markdown subset the
memo actually uses: headings, paragraphs with bold/italic/links, pipe tables,
an image, ordered and unordered lists, and horizontal rules.

Run:  python3 src/make_memo_docx.py
Requires: python-docx  (pip install python-docx)
"""

import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "memo.md"
OUT = ROOT / "docs" / "Memo - Massachusetts Homelessness.docx"

FONT = "Calibri"
ACCENT = "1F3D5C"
MUTED = "666666"

INLINE = re.compile(r"(\*\*.+?\*\*|\*[^*]+?\*|\[[^\]]+\]\([^)]+\))", re.S)


def style(run, size=10.5, bold=False, italic=False, color=None):
    run.font.name = FONT
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color:
        run.font.color.rgb = RGBColor.from_string(color)
    rPr = run._element.get_or_add_rPr()
    rf = rPr.find(qn("w:rFonts"))
    if rf is None:
        rf = parse_xml("<w:rFonts %s/>" % nsdecls("w"))
        rPr.append(rf)
    for attr in ("w:ascii", "w:hAnsi", "w:cs"):
        rf.set(qn(attr), FONT)
    return run


def write_inline(p, text, size=10.5, color=None, base_bold=False):
    """Emit text into paragraph p, honouring **bold**, *italic* and links."""
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            style(p.add_run(part[2:-2]), size, bold=True, color=color)
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            style(p.add_run(part[1:-1]), size, italic=True, color=color)
        elif part.startswith("["):
            label, url = re.match(r"\[([^\]]+)\]\(([^)]+)\)", part).groups()
            style(p.add_run(label), size, italic=True, color=color)
            style(p.add_run(f" ({url})"), size - 1, color=MUTED)
        else:
            style(p.add_run(part), size, bold=base_bold, color=color)


def new_para(doc, before=0, after=7, left=0.0):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    pf.left_indent = Inches(left)
    return p


def add_rule(doc):
    p = new_para(doc, after=8)
    p._p.get_or_add_pPr().append(parse_xml(
        '<w:pBdr %s><w:bottom w:val="single" w:sz="6" w:space="1" w:color="%s"/></w:pBdr>'
        % (nsdecls("w"), ACCENT)))


def add_table(doc, rows):
    header, body = rows[0], rows[2:]          # rows[1] is the --- separator
    aligns = ["right" if c.strip().endswith(":") else "left" for c in rows[1]]
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    for i, cell in enumerate(t.rows[0].cells):
        cell._tc.get_or_add_tcPr().append(parse_xml(
            '<w:shd %s w:val="clear" w:color="auto" w:fill="%s"/>' % (nsdecls("w"), ACCENT)))
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = p.paragraph_format.space_after = Pt(3)
        if aligns[i] == "right":
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        style(p.add_run(header[i].strip()), 9.5, bold=True, color="FFFFFF")
    for r_i, row in enumerate(body):
        cells = t.add_row().cells
        for i, cell in enumerate(cells):
            if r_i % 2 == 1:
                cell._tc.get_or_add_tcPr().append(parse_xml(
                    '<w:shd %s w:val="clear" w:color="auto" w:fill="F2F5F8"/>' % nsdecls("w")))
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = p.paragraph_format.space_after = Pt(3)
            if aligns[i] == "right":
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            write_inline(p, row[i].strip() if i < len(row) else "", 9.5)


def split_row(line):
    return [c for c in line.strip().strip("|").split("|")]


def main() -> int:
    if not SRC.exists():
        raise SystemExit(f"missing {SRC}")
    lines = SRC.read_text(encoding="utf-8").splitlines()

    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    sec.top_margin = sec.bottom_margin = Inches(0.8)
    sec.left_margin = sec.right_margin = Inches(0.9)
    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal.font.size = Pt(10.5)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    normal.paragraph_format.line_spacing = 1.06

    i, n_tables, n_images = 0, 0, 0
    while i < len(lines):
        raw = lines[i]
        line = raw.strip()

        if not line:
            i += 1
        elif line.startswith("|"):                       # table
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(split_row(lines[i]))
                i += 1
            add_table(doc, block)
            new_para(doc, after=2)
            n_tables += 1
        elif line.startswith("!["):                      # image
            path = re.match(r"!\[[^\]]*\]\(([^)]+)\)", line).group(1)
            img = (SRC.parent / path).resolve()
            if not img.exists():
                raise SystemExit(f"figure not found: {img}")
            p = new_para(doc, before=4, after=6)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(str(img), width=Inches(6.5))
            n_images += 1
            i += 1
        elif line == "---":
            add_rule(doc)
            i += 1
        elif line.startswith("# "):
            p = new_para(doc, after=2)
            style(p.add_run(line[2:]), 15, bold=True, color=ACCENT)
            i += 1
        elif line.startswith("## "):
            p = new_para(doc, before=9, after=3)
            style(p.add_run(line[3:]), 11.5, bold=True, color=ACCENT)
            i += 1
        elif re.match(r"^\d+\.\s", line):                # ordered list
            num, text = re.match(r"^(\d+)\.\s+(.*)$", line).groups()
            i += 1
            while i < len(lines) and lines[i].startswith("   ") and lines[i].strip():
                text += " " + lines[i].strip()
                i += 1
            p = new_para(doc, after=3, left=0.28)
            p.paragraph_format.first_line_indent = Inches(-0.28)
            style(p.add_run(f"{num}.  "), 10.5, bold=True)
            write_inline(p, text)
        elif re.match(r"^\*\*[A-Za-z][A-Za-z ]*:\*\*", line):   # memo header field
            p = new_para(doc, after=1)
            write_inline(p, line, size=10)
            i += 1
        elif line.startswith("¹"):                       # footnote
            p = new_para(doc, before=6, after=3)
            write_inline(p, line, size=8.5, color=MUTED)
            i += 1
        else:                                            # paragraph
            buf = [line]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(
                    r"^(#|\||!\[|---$|\d+\.\s|¹)", lines[i].strip()):
                buf.append(lines[i].strip())
                i += 1
            text = " ".join(buf)
            small = text.startswith("**Sources.**")
            p = new_para(doc, after=7)
            write_inline(p, text, size=8.5 if small else 10.5,
                         color=MUTED if small else None)

    doc.save(OUT)
    print(f"wrote {OUT}")
    print(f"  {n_tables} tables, {n_images} figure(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
