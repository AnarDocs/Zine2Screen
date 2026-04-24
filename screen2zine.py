#!/usr/bin/env python3
"""Impose a reading-order PDF for printing: booklet, trifold, or fourfold."""

import argparse
import math
import sys
from pathlib import Path
from pypdf import PdfReader, PdfWriter, PageObject, Transformation


def _blank(pages):
    return PageObject.create_blank_page(
        width=float(pages[0].mediabox.width),
        height=float(pages[0].mediabox.height)
    )


def impose_booklet(pages, page_count, binding, outer, flip_even):
    while len(pages) % 4 != 0:
        pages.append(_blank(pages))

    total = len(pages)
    page_w = float(pages[0].mediabox.width)
    page_h = float(pages[0].mediabox.height)

    sheet_w = (page_w + binding + outer) * 2
    sheet_h = page_h + outer * 2

    pairs = []
    lo, hi = 0, total - 1
    while lo < hi:
        pairs.append((hi, lo))
        lo += 1
        hi -= 1
        if lo < hi:
            pairs.append((lo, hi))
            lo += 1
            hi -= 1

    writer = PdfWriter()
    for left_idx, right_idx in pairs:
        sheet = PageObject.create_blank_page(width=sheet_w, height=sheet_h)
        sheet.merge_transformed_page(pages[left_idx], Transformation().translate(outer, outer))
        sheet.merge_transformed_page(pages[right_idx], Transformation().translate(page_w + outer + binding * 2, outer))
        writer.add_page(sheet)

    if flip_even:
        for i, page in enumerate(writer.pages):
            if i % 2 == 1:
                page.rotate(180)

    padded = len(pages) - page_count
    pad_note = f", {padded} blank page(s) added to reach multiple of 4" if padded else ""
    print(f"Done — {len(pairs)} sheets from {page_count} pages{pad_note}")
    return writer


def impose_trifold(pages, page_count, outer):
    """
    Trifold (letter fold): 6 panels across 2 sides of a single sheet.
    Front side: panels 5, 6, 1  (indices 4, 5, 0)
    Back side:  panels 2, 3, 4  (indices 1, 2, 3)
    """
    while len(pages) % 6 != 0:
        pages.append(_blank(pages))

    page_w = float(pages[0].mediabox.width)
    page_h = float(pages[0].mediabox.height)
    sheet_w = page_w * 3 + outer * 2
    sheet_h = page_h + outer * 2

    writer = PdfWriter()
    for panel_indices in ([4, 5, 0], [1, 2, 3]):
        sheet = PageObject.create_blank_page(width=sheet_w, height=sheet_h)
        for col, idx in enumerate(panel_indices):
            sheet.merge_transformed_page(pages[idx], Transformation().translate(outer + col * page_w, outer))
        writer.add_page(sheet)

    padded = len(pages) - page_count
    pad_note = f", {padded} blank page(s) added to reach multiple of 6" if padded else ""
    print(f"Done — 2-sided trifold from {page_count} pages{pad_note}")
    return writer


def impose_fourfold(pages, page_count, outer):
    """
    Fourfold (quarter fold): 4 pages on one side of a single sheet.
    Layout when flat:
        top-left:     page 1  (right way up)
        top-right:    page 4  (upside down — reads correctly when folded)
        bottom-left:  page 2  (right way up)
        bottom-right: page 3  (right way up)
    """
    while len(pages) % 4 != 0:
        pages.append(_blank(pages))

    page_w = float(pages[0].mediabox.width)
    page_h = float(pages[0].mediabox.height)
    sheet_w = page_w * 2 + outer * 2
    sheet_h = page_h * 2 + outer * 2

    sheet = PageObject.create_blank_page(width=sheet_w, height=sheet_h)

    # Bottom-left: page 2
    sheet.merge_transformed_page(pages[1], Transformation().translate(outer, outer))
    # Bottom-right: page 3
    sheet.merge_transformed_page(pages[2], Transformation().translate(outer + page_w, outer))
    # Top-left: page 1
    sheet.merge_transformed_page(pages[0], Transformation().translate(outer, outer + page_h))
    # Top-right: page 4, rotated 180° so it reads correctly after folding.
    # Rotation is about the origin, so after rotate(180) the content sits in negative
    # space; translating by (outer + 2*page_w, outer + 2*page_h) brings it into the
    # top-right cell of the sheet.
    sheet.merge_transformed_page(
        pages[3],
        Transformation().rotate(180).translate(outer + 2 * page_w, outer + 2 * page_h)
    )

    writer = PdfWriter()
    writer.add_page(sheet)

    padded = len(pages) - page_count
    pad_note = f", {padded} blank page(s) added to reach multiple of 4" if padded else ""
    print(f"Done — 1-side fourfold from {page_count} pages{pad_note}")
    return writer


def main():
    parser = argparse.ArgumentParser(
        description="Impose a reading-order PDF for printing."
    )
    parser.add_argument("input", help="Input PDF in reading order")
    parser.add_argument("-o", "--output", help="Output PDF path")
    parser.add_argument(
        "--format", choices=["booklet", "trifold", "fourfold"], default="booklet",
        help="Imposition format (default: booklet)"
    )
    parser.add_argument(
        "--binding-margin", type=float, default=36, metavar="PTS",
        help="Booklet only: extra space on spine edge in points (default: 36 ≈ 12mm)"
    )
    parser.add_argument(
        "--outer-margin", type=float, default=18, metavar="PTS",
        help="Extra space on outer/top/bottom edges in points (default: 18 ≈ 6mm)"
    )
    parser.add_argument(
        "--flip-even", action="store_true",
        help="Booklet only: rotate even-numbered output sheets 180° for short-edge duplex"
    )
    parser.add_argument(
        "--half", action="store_true",
        help="Scale each page down by 1/√2 before imposition (A4→A5, A5→A6, etc.)"
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        sys.exit(f"Error: file not found: {args.input}")

    suffixes = {"booklet": "-booklet", "trifold": "-trifold", "fourfold": "-fourfold"}
    output_path = Path(args.output) if args.output else input_path.with_name(
        input_path.stem + suffixes[args.format] + ".pdf"
    )

    reader = PdfReader(str(input_path))
    pages = list(reader.pages)
    page_count = len(pages)

    if args.half:
        factor = 1 / math.sqrt(2)
        for page in pages:
            page.scale_by(factor)

    if args.format == "booklet":
        writer = impose_booklet(pages, page_count, args.binding_margin, args.outer_margin, args.flip_even)
    elif args.format == "trifold":
        writer = impose_trifold(pages, page_count, args.outer_margin)
    else:
        writer = impose_fourfold(pages, page_count, args.outer_margin)

    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"→ {output_path}")


if __name__ == "__main__":
    main()
