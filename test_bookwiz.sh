#!/bin/bash
# Run each bookWiz conversion against the example files, output to test_output/

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="$SCRIPT_DIR/test_output"

pass=0
fail=0
skip=0

mkdir -p "$OUT"

# Check whether a list of commands are all available
require() {
    for cmd in "$@"; do
        if ! command -v "$cmd" &>/dev/null; then
            echo "  SKIP — required tool not found: $cmd"
            ((skip++))
            return 1
        fi
    done
    return 0
}

run_test() {
    local label="$1"
    local expected_output="$2"
    shift 2

    echo "──────────────────────────────────────────"
    echo "TEST: $label"
    echo "CMD:  bookWiz $*"
    echo ""

    if "$SCRIPT_DIR/bookWiz" "$@"; then
        if [ -f "$expected_output" ]; then
            size=$(wc -c < "$expected_output")
            echo ""
            echo "✓ PASS — $(basename "$expected_output") (${size} bytes)"
            ((pass++))
        else
            echo ""
            echo "✗ FAIL — output file not found: $expected_output"
            ((fail++))
        fi
    else
        echo ""
        echo "✗ FAIL — bookWiz exited with error"
        ((fail++))
    fi
    echo ""
}

# ── Tests requiring only Python / pypdf ───────────────────────────────────────

if require python3; then
    run_test \
        "Reading-order → imposed booklet" \
        "$OUT/straight_a5-booklet.pdf" \
        -tobook "$SCRIPT_DIR/examples/straight_a5.pdf" "$OUT/straight_a5-booklet.pdf"

    run_test \
        "Reading-order → imposed booklet (flip odd)" \
        "$OUT/straight_a5-booklet-flip.pdf" \
        -tobook "$SCRIPT_DIR/examples/straight_a5.pdf" "$OUT/straight_a5-booklet-flip.pdf" flip
fi

# ── Tests requiring poppler (pdftoppm, pdfinfo) + ImageMagick ────────────────

if require pdftoppm pdfinfo convert; then
    run_test \
        "Imposed booklet → reading-order" \
        "$OUT/imposed_booklet-screen.pdf" \
        -frombook "$SCRIPT_DIR/examples/imposed_booklet.pdf" "$OUT/imposed_booklet-screen.pdf"
fi

# ── Tests requiring poppler (pdfinfo) + ImageMagick + pdftk ──────────────────

if require pdfinfo convert identify pdftk; then
    run_test \
        "Scanned spreads → reading-order" \
        "$OUT/scanned_spreads-screen.pdf" \
        -fromscan "$SCRIPT_DIR/examples/scanned_spreads.pdf" "$OUT/scanned_spreads-screen.pdf"

    run_test \
        "Scanned spreads → imposed booklet" \
        "$OUT/scanned_spreads-booklet.pdf" \
        -scan2book "$SCRIPT_DIR/examples/scanned_spreads.pdf" "$OUT/scanned_spreads-booklet.pdf"

    run_test \
        "Scanned spreads → imposed booklet (flip odd)" \
        "$OUT/scanned_spreads-booklet-flip.pdf" \
        -scan2book "$SCRIPT_DIR/examples/scanned_spreads.pdf" "$OUT/scanned_spreads-booklet-flip.pdf" flip
fi

echo "══════════════════════════════════════════"
echo "Results: $pass passed, $fail failed, $skip skipped (missing tools)"
[ $skip -gt 0 ] && echo "Install missing tools with: ./dependencies.sh"
echo "Output files in: $OUT"
echo ""

[ $fail -eq 0 ]
