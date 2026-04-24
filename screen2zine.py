#!/usr/bin/env python3
"""Impose a reading-order PDF as a printable saddle-stitch booklet."""

import argparse
import sys
from pathlib import Path
from pypdf import PdfReader, PdfWriter, PageObject, Transformation


def main():
    parser = argparse.ArgumentParser(
        description="Impose a reading-order PDF as a printable saddle-stitch booklet."
    )
    parser.add_argument("input", help="Input PDF in reading order")
    parser.add_argument("-o", "--output", help="Output PDF path (default: {input}-booklet.pdf)")
    parser.add_argument(
        "--binding-margin", type=float, default=36,
        metavar="PTS",
        help="Extra space on spine edge in points (default: 36 ≈ 12mm)"
    )
    parser.add_argument(
        "--outer-margin", type=float, default=18,
        metavar="PTS",
        help="Extra space on outer/top/bottom edge in points (default: 18 ≈ 6mm)"
    )
    parser.add_argument(
        "--flip-even", action="store_true",
        help="Rotate even-numbered output sheets 180° for short-edge duplex printing"
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        sys.exit(f"Error: file not found: {args.input}")

    output_path = Path(args.output) if args.output else input_path.with_name(input_path.stem + "-booklet.pdf")

    reader = PdfReader(str(input_path))
    writer = PdfWriter()

    pages = list(reader.pages)
    page_count = len(pages)

    # Pad to a multiple of 4 (each folded sheet holds 4 pages)
    while len(pages) % 4 != 0:
        blank = PageObject.create_blank_page(
            width=float(pages[0].mediabox.width),
            height=float(pages[0].mediabox.height)
        )
        pages.append(blank)

    total = len(pages)
    page_w = float(pages[0].mediabox.width)
    page_h = float(pages[0].mediabox.height)

    binding = args.binding_margin
    outer = args.outer_margin

    # Landscape sheet: two source pages side by side with margins
    sheet_w = (page_w + binding + outer) * 2
    sheet_h = page_h + (outer * 2)

    # Saddle-stitch imposition: outermost pair first, working inward
    pairs = []
    lo, hi = 0, total - 1
    while lo < hi:
        pairs.append((hi, lo))      # back / front cover of outer sheet
        lo += 1
        hi -= 1
        if lo < hi:
            pairs.append((lo, hi))  # next inner sheet
            lo += 1
            hi -= 1

    for left_idx, right_idx in pairs:
        sheet = PageObject.create_blank_page(width=sheet_w, height=sheet_h)

        # Left page (verso): binding margin is on its right edge
        sheet.merge_transformed_page(
            pages[left_idx],
            Transformation().translate(outer, outer)
        )

        # Right page (recto): binding margin is on its left edge
        sheet.merge_transformed_page(
            pages[right_idx],
            Transformation().translate(page_w + outer + binding * 2, outer)
        )

        writer.add_page(sheet)

    if args.flip_even:
        for i, page in enumerate(writer.pages):
            if i % 2 == 1:  # 0-based odd index = 1-based even sheet (back of each physical sheet)
                page.rotate(180)

    with open(output_path, "wb") as f:
        writer.write(f)

    padded = total - page_count
    pad_note = f", {padded} blank page(s) added to reach multiple of 4" if padded else ""
    print(f"Done — {len(pairs)} sheets from {page_count} pages{pad_note} → {output_path}")


if __name__ == "__main__":
    main()
