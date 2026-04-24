#!/usr/bin/env python3
"""Generate the three example PDFs for Zine2Screen."""

from pathlib import Path
from reportlab.lib.pagesizes import A4, A5, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter, PageObject, Transformation

OUT = Path(__file__).parent

LOREM = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor "
    "incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud "
    "exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure "
    "dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. "
    "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt "
    "mollit anim id est laborum. Sed ut perspiciatis unde omnis iste natus error sit "
    "voluptatem accusantium doloremque laudantium, totam rem aperiam eaque ipsa quae ab "
    "illo inventore veritatis et quasi architecto beatae vitae dicta sunt explicabo."
)

A5_W, A5_H = A5  # 419.5 x 595.3 pt


# ── 1. Straight A5 four-pager ─────────────────────────────────────────────────

def make_straight_a5(path):
    c = canvas.Canvas(str(path), pagesize=A5)
    for n in range(1, 5):
        w, h = A5
        # Page label
        c.setFont("Helvetica-Bold", 18)
        c.drawString(15 * mm, h - 20 * mm, f"Page {n}")
        # Thin rule under the title
        c.setLineWidth(0.5)
        c.line(15 * mm, h - 23 * mm, w - 15 * mm, h - 23 * mm)
        # Lorem ipsum body
        c.setFont("Helvetica", 9)
        text = c.beginText(15 * mm, h - 32 * mm)
        text.setLeading(14)
        for word_pos in range(0, len(LOREM), 80):
            text.textLine(LOREM[word_pos:word_pos + 80])
        c.drawText(text)
        # Footer page number
        c.setFont("Helvetica", 8)
        c.drawCentredString(w / 2, 10 * mm, str(n))
        c.showPage()
    c.save()
    print(f"  ✓ {path.name}")


# ── 2 & 3. Spread helpers ─────────────────────────────────────────────────────

def make_spread_pdf(path, spreads):
    """
    spreads: list of (left_page_index, right_page_index) — 0-based into the A5 PDF.
    """
    a5_pdf = PdfReader(str(OUT / "straight_a5.pdf"))
    writer = PdfWriter()

    sheet_w = A5_W * 2   # two A5 pages wide
    sheet_h = A5_H       # same height

    for left_idx, right_idx in spreads:
        sheet = PageObject.create_blank_page(width=sheet_w, height=sheet_h)
        sheet.merge_transformed_page(
            a5_pdf.pages[left_idx],
            Transformation().translate(0, 0)
        )
        sheet.merge_transformed_page(
            a5_pdf.pages[right_idx],
            Transformation().translate(A5_W, 0)
        )
        writer.add_page(sheet)

    with open(path, "wb") as f:
        writer.write(f)
    print(f"  ✓ {path.name}")


if __name__ == "__main__":
    print("Creating examples...")

    # 1. Straight A5
    make_straight_a5(OUT / "straight_a5.pdf")

    # 2. Imposed booklet order: [p4|p1], [p2|p3]
    make_spread_pdf(OUT / "imposed_booklet.pdf", [(3, 0), (1, 2)])

    # 3. Scanned / reading-order spreads: [p1|p2], [p3|p4]
    make_spread_pdf(OUT / "scanned_spreads.pdf", [(0, 1), (2, 3)])

    print("Done.")
