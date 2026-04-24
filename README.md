# Zine2Screen

Tools for converting zine and booklet PDFs between print and screen formats — whether you're preparing a zine to print, splitting a scanned booklet to read on screen, or reimposing spreads for a new print run.

| Script | Input | Output |
|--------|-------|--------|
| `screen2zine.py` | Reading-order single pages | Imposed booklet, ready to print |
| `zine2screen.sh` | Imposed booklet (print order) | Reading-order single pages |
| `splitSpread.sh` | 2-page spreads (any order) | Individual pages, or reimposed |

## Common tasks

Use `bookWiz` for quick conversions, or call the individual scripts directly for more control.

```bash
./bookWiz -tobook   input.pdf [output.pdf] [flip]   # reading-order → imposed booklet
./bookWiz -frombook input.pdf [output.pdf]           # imposed booklet → reading-order
./bookWiz -fromscan input.pdf [output.pdf]           # scanned spreads → reading-order
./bookWiz -scan2book input.pdf [output.pdf] [flip]   # scanned spreads → imposed booklet
```

Add `flip` at the end to rotate even-numbered sheets 180° for short-edge duplex printers.

---

**I have a reading-order PDF and want to print it as a booklet**
```bash
./bookWiz -tobook myzine.pdf
# → myzine-booklet.pdf
```
Alternatively: `python screen2zine.py myzine.pdf`

**I have a print-imposed PDF and want to read it on screen**
```bash
./bookWiz -frombook myzine.pdf
# → myzine-screen.pdf
```
Alternatively: `./zine2screen.sh myzine.pdf`

**I have a scanned booklet (spreads in reading order) and want a screen-readable PDF**
```bash
./bookWiz -fromscan myzine.pdf
# → myzine-screen.pdf
```
Alternatively: `./splitSpread.sh -c myzine.pdf`

**I have a scanned booklet and want to reprint it as an imposed booklet**
```bash
./bookWiz -scan2book myzine.pdf
# → myzine-booklet.pdf
```
Alternatively:
```bash
./splitSpread.sh -c myzine.pdf
python screen2zine.py myzine-compiled.pdf
```

**I just want to extract a couple of spreads from a PDF**
```bash
./splitSpread.sh -x=1,4 myzine.pdf
# → individual files for spreads 1 and 4 only
```

Example files for each format are in the `examples/` directory.

---

## Requirements

### zine2screen.sh

- **ImageMagick** (`convert`)
- **Poppler** (`pdftoppm`, `pdfinfo`)
- **Ghostscript** (`gs`)
- **img2pdf** — optional but recommended (avoids ImageMagick's PDF policy restrictions)

### splitSpread.sh

- **ImageMagick** (`convert`, `identify`)
- **Poppler** (`pdfinfo`)
- **pdftk**

### screen2zine.py

- **Python 3**
- **pypdf** — `pip install pypdf`

---

Run `dependencies.sh` to install the shell tool dependencies automatically, or manually:

| Platform | Command |
|----------|---------|
| Debian/Ubuntu | `sudo apt install poppler-utils imagemagick ghostscript pdftk img2pdf` |
| Fedora/RHEL | `sudo yum install poppler-utils ImageMagick ghostscript pdftk && pip install img2pdf` |
| macOS | `brew install poppler imagemagick ghostscript pdftk-java img2pdf` |

Works on macOS and Linux. Windows is not supported (WSL may work).

---

## screen2zine.py — reading-order PDF → printable booklet

Imposes a reading-order PDF as a saddle-stitch booklet. Pages are arranged so that when printed double-sided, folded, and stapled, they read in the correct sequence. Works directly with PDF vectors — no rasterisation, no quality loss.

```bash
python screen2zine.py input.pdf
python screen2zine.py input.pdf -o booklet.pdf
python screen2zine.py input.pdf --binding-margin 36 --outer-margin 18
python screen2zine.py input.pdf --flip-even
```

Margins are in PDF points (1pt = 1/72 inch ≈ 0.35mm). Defaults: binding edge 36pt (~12mm), outer/top/bottom edge 18pt (~6mm). The page count is automatically padded to a multiple of 4 with blank pages if necessary.

`--flip-even` rotates even-numbered output sheets 180° (the back side of each physical sheet). Use this when printing on a duplex printer that flips on the short edge — without it, the back of each sheet comes out upside down.

---

## zine2screen.sh — imposed PDF → reading-order pages

Takes a print-imposed PDF (pages in booklet printing order) and reorders them into sequential reading order. Outputs individual page images and a compiled `-screen.pdf`.

```bash
./zine2screen.sh zine.pdf                       # output to zine_output/
./zine2screen.sh zine.pdf zinescreen            # images to zinescreen/
./zine2screen.sh -r300 zine.pdf                 # 300 DPI (default 150 / 75 is usually fine for screen)
./zine2screen.sh -o reading-order.pdf zine.pdf  # set output PDF path
```

Page images are written to `./{output_dir}/images/`. Convert to JPEG with:

```bash
mogrify -format jpg *.png
```

> Assumes standard saddle-stitch imposition order. If your PDF was imposed by a different application or method, results may be incorrect.

---

## splitSpread.sh — split 2-page spreads into individual pages

Splits every page of a PDF down the middle (left half first, then right half), outputting individual single-page PDFs. Works with spreads in any order — reading order, scanned, or imposed.

```bash
./splitSpread.sh input.pdf                      # split only, individual files
./splitSpread.sh -r=300 input.pdf               # set resolution (default 150 DPI)
./splitSpread.sh -o=output/ input.pdf           # write output files to a directory
./splitSpread.sh -c input.pdf                   # split and compile into a single PDF
./splitSpread.sh -b -c input.pdf                # split, reorder to print order, and compile
./splitSpread.sh -b -c -f input.pdf             # as above, then flip even pages for short-edge duplex
./splitSpread.sh -x=1,36 input.pdf              # extract specific original spreads only
```

The `-b` flag reorders output pages from reading order into saddle-stitch printing order (last+first, second+second-to-last, etc.) — the opposite direction to `zine2screen.sh`. Use it when you want to re-impose already-split pages for printing.

`-f` rotates even-numbered pages 180° in the compiled output (the back side of each physical sheet). Requires `-c`. Use with `-b -c` when your duplex printer flips on the short edge.

---

## Limitations

- **zine2screen.sh** and **splitSpread.sh** rasterise through PNG — text will not be selectable. Use a higher DPI for legible small text.
- **splitSpread.sh** assumes every input page is a 2-page spread and splits all pages in half regardless.
- **zine2screen.sh** only handles standard saddle-stitch imposition order.
- **zine2screen.sh** and **splitSpread.sh** write output to the current directory or a created subdirectory.

---

## ImageMagick security policy error

If you get: `attempt to perform an operation not allowed by the security policy`

This is an ImageMagick default that blocks PDF operations on servers. To disable it, run as root:

```bash
for file in `convert -list policy | grep "Path:" | grep -v built | sed 's/Path: \(.*\)/\1/g'`; do sed -i 's/domain="coder" rights="none" pattern="PDF"/domain="coder" rights="read|write" pattern="PDF"/g' $file; done
```

Or install `img2pdf` as an alternative (recommended — it's already used automatically if present).

Note: This compiles together 3 different tools I created for similar purposes