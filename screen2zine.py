#!/usr/bin/env python3
"""Impose a reading-order PDF for printing: booklet, trifold, or fourfold."""

import argparse
import math
import sys
from pathlib import Path
from pypdf import PdfReader, PdfWriter, PageObject, Transformation

# Portrait dimensions in points (width × height)
PAPER_SIZES_PT = {
    "A2": (1190.55, 1683.78),
    "A3": (841.89, 1190.55),
    "A4": (595.276, 841.89),
    "A5": (419.528, 595.276),
    "A6": (297.638, 419.528),
    "letter": (612.0, 792.0),
    "legal": (612.0, 1008.0),
    "tabloid": (792.0, 1224.0),
}
def _landscape(name):
    w, h = PAPER_SIZES_PT[name]
    return (max(w, h), min(w, h))


# All sizes sorted smallest-area-first for auto-paper selection
_PAPER_BY_AREA = sorted(PAPER_SIZES_PT, key=lambda n: _landscape(n)[0] * _landscape(n)[1])


def _auto_paper(need_w, need_h):
    """Smallest standard landscape paper that fits need_w × need_h.

    A 1pt tolerance absorbs sub-millimetre rounding differences in source PDFs
    without misidentifying genuinely different paper sizes.
    """
    tol = 1.0
    for name in _PAPER_BY_AREA:
        sw, sh = _landscape(name)
        if sw + tol >= need_w and sh + tol >= need_h:
            return sw, sh
    return need_w, need_h


def _resolve_paper(paper, need_w, need_h):
    if paper == "auto":
        return _auto_paper(need_w, need_h)
    if paper not in PAPER_SIZES_PT:
        sys.exit(f"Error: unknown paper size '{paper}'. Choose from: {', '.join(PAPER_SIZES_PT)}")
    sw, sh = _landscape(paper)
    if sw < need_w or sh < need_h:
        print(
            f"Warning: content ({need_w:.1f}×{need_h:.1f} pt) overflows {paper} "
            f"({sw:.1f}×{sh:.1f} pt) — pages will be clipped.",
            file=sys.stderr,
        )
    return sw, sh


def _blank(pages):
    return PageObject.create_blank_page(
        width=float(pages[0].mediabox.width),
        height=float(pages[0].mediabox.height)
    )


def impose_booklet(pages, page_count, binding, outer, flip_even, paper="auto"):
    while len(pages) % 4 != 0:
        pages.append(_blank(pages))

    total = len(pages)
    page_w = float(pages[0].mediabox.width)
    page_h = float(pages[0].mediabox.height)

    # Raw spread dimensions: outer + page + binding*2 + page + outer
    raw_w = (page_w + binding + outer) * 2
    raw_h = page_h + outer * 2

    sheet_w, sheet_h = _resolve_paper(paper, raw_w, raw_h)

    # Centre the content block within the (potentially larger) sheet
    x_pad = (sheet_w - raw_w) / 2
    y_pad = (sheet_h - raw_h) / 2
    left_x = x_pad + outer
    right_x = x_pad + outer + page_w + binding * 2
    y_offset = y_pad + outer

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
        sheet.merge_transformed_page(pages[left_idx], Transformation().translate(left_x, y_offset))
        sheet.merge_transformed_page(pages[right_idx], Transformation().translate(right_x, y_offset))
        writer.add_page(sheet)

    if flip_even:
        for i, page in enumerate(writer.pages):
            if i % 2 == 1:
                page.rotate(180)

    padded = len(pages) - page_count
    pad_note = f", {padded} blank page(s) added to reach multiple of 4" if padded else ""
    print(f"Done — {len(pairs)} sheets from {page_count} pages{pad_note}")
    return writer


def impose_trifold(pages, page_count, outer, paper="auto"):
    """
    Trifold (letter fold): 6 panels across 2 sides of a single sheet.
    Front side: panels 5, 6, 1  (indices 4, 5, 0)
    Back side:  panels 2, 3, 4  (indices 1, 2, 3)
    """
    while len(pages) % 6 != 0:
        pages.append(_blank(pages))

    page_w = float(pages[0].mediabox.width)
    page_h = float(pages[0].mediabox.height)
    raw_w = page_w * 3 + outer * 2
    raw_h = page_h + outer * 2

    sheet_w, sheet_h = _resolve_paper(paper, raw_w, raw_h)
    x_pad = (sheet_w - raw_w) / 2
    y_pad = (sheet_h - raw_h) / 2

    writer = PdfWriter()
    for panel_indices in ([4, 5, 0], [1, 2, 3]):
        sheet = PageObject.create_blank_page(width=sheet_w, height=sheet_h)
        for col, idx in enumerate(panel_indices):
            sheet.merge_transformed_page(
                pages[idx],
                Transformation().translate(x_pad + outer + col * page_w, y_pad + outer),
            )
        writer.add_page(sheet)

    padded = len(pages) - page_count
    pad_note = f", {padded} blank page(s) added to reach multiple of 6" if padded else ""
    print(f"Done — 2-sided trifold from {page_count} pages{pad_note}")
    return writer


def impose_fourfold(pages, page_count, outer, paper="auto"):
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
    raw_w = page_w * 2 + outer * 2
    raw_h = page_h * 2 + outer * 2

    sheet_w, sheet_h = _resolve_paper(paper, raw_w, raw_h)
    x_pad = (sheet_w - raw_w) / 2
    y_pad = (sheet_h - raw_h) / 2
    ox = x_pad + outer
    oy = y_pad + outer

    sheet = PageObject.create_blank_page(width=sheet_w, height=sheet_h)

    # Bottom-left: page 2
    sheet.merge_transformed_page(pages[1], Transformation().translate(ox, oy))
    # Bottom-right: page 3
    sheet.merge_transformed_page(pages[2], Transformation().translate(ox + page_w, oy))
    # Top-left: page 1
    sheet.merge_transformed_page(pages[0], Transformation().translate(ox, oy + page_h))
    # Top-right: page 4, rotated 180° so it reads correctly after folding.
    # Rotation is about the origin, so after rotate(180) the content sits in negative
    # space; translating by (ox + 2*page_w, oy + 2*page_h) brings it into the
    # top-right cell of the sheet.
    sheet.merge_transformed_page(
        pages[3],
        Transformation().rotate(180).translate(ox + 2 * page_w, oy + 2 * page_h)
    )

    writer = PdfWriter()
    writer.add_page(sheet)

    padded = len(pages) - page_count
    pad_note = f", {padded} blank page(s) added to reach multiple of 4" if padded else ""
    print(f"Done — 1-side fourfold from {page_count} pages{pad_note}")
    return writer


def convert_paper(pages, page_count, target_paper, scale_up=0.0):
    """Rescale each sheet to fit a target paper size, centred.

    scale_up > 0 scales above the fit baseline, clipping into outer margins
    rather than adding white space.  Any overflow is outside the MediaBox and
    gets trimmed naturally by the printer.

    Handles portrait-stored landscape sheets (ph > pw, with or without /Rotate)
    by rotating the content into landscape before scaling.
    """
    tw, th = _landscape(target_paper)
    writer = PdfWriter()
    for page in pages:
        pw = float(page.mediabox.width)
        ph = float(page.mediabox.height)
        rotation = int(page.get('/Rotate', 0) or 0) % 360

        if rotation in (90, 270) or (rotation == 0 and ph > pw):
            # Portrait-stored landscape sheet — rotate into landscape first.
            # rotate(-90) then translate(0, pw) maps (x,y) → (y, -x+pw),
            # turning the portrait box (0..pw × 0..ph) into landscape (0..ph × 0..pw).
            eff_w, eff_h = ph, pw
            base_t = Transformation().rotate(-90).translate(0, pw)
        else:
            eff_w, eff_h = pw, ph
            base_t = Transformation()

        scale = min(tw / eff_w, th / eff_h) * (1 + scale_up / 100)
        tx = (tw - eff_w * scale) / 2
        ty = (th - eff_h * scale) / 2
        new_page = PageObject.create_blank_page(width=tw, height=th)
        new_page.merge_transformed_page(
            page, base_t.scale(scale, scale).translate(tx, ty)
        )
        writer.add_page(new_page)
    print(f"Done — {page_count} sheet(s) converted to {target_paper}")
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
    parser.add_argument(
        "--paper", default="auto",
        metavar="SIZE",
        help=(
            "Target output paper size: auto (default), or one of "
            + ", ".join(PAPER_SIZES_PT)
            + ". 'auto' snaps to the smallest standard size that fits the spread."
        ),
    )
    parser.add_argument(
        "--convert-to", choices=list(PAPER_SIZES_PT), metavar="SIZE",
        help=(
            "Rescale an already-imposed PDF to a different paper size "
            "(skips imposition; use with -o to set output path)."
        ),
    )
    parser.add_argument(
        "--scale-up", type=float, default=0.0, metavar="PCT",
        help=(
            "With --convert-to: scale up by this %% above the fit baseline, "
            "clipping into outer margins rather than adding white space (default: 0)."
        ),
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

    if args.convert_to:
        writer = convert_paper(pages, page_count, args.convert_to, args.scale_up)
        with open(output_path, "wb") as f:
            writer.write(f)
        print(f"→ {output_path}")
        return

    if args.half:
        factor = 1 / math.sqrt(2)
        for page in pages:
            page.scale_by(factor)

    if args.format == "booklet":
        writer = impose_booklet(pages, page_count, args.binding_margin, args.outer_margin, args.flip_even, args.paper)
    elif args.format == "trifold":
        writer = impose_trifold(pages, page_count, args.outer_margin, args.paper)
    else:
        writer = impose_fourfold(pages, page_count, args.outer_margin, args.paper)

    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"→ {output_path}")


if __name__ == "__main__":
    main()
