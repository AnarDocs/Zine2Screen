#!/bin/bash
# imposeConvert.sh — rescale an imposed booklet PDF between A4 and Letter

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    echo "Usage:"
    echo "  imposeConvert.sh -toA4     input.pdf [output.pdf]   Rescale Letter-imposed → A4"
    echo "  imposeConvert.sh -toLetter input.pdf [output.pdf]   Rescale A4-imposed → Letter"
    exit 1
}

if [ $# -lt 2 ]; then usage; fi

direction="$1"
input="$2"
output="${3:-}"

if [ ! -f "$input" ]; then
    echo "Error: file not found: $input"
    exit 1
fi

stem=$(basename "$input" .pdf)

case "$direction" in
    -toA4)
        output="${output:-${stem}-A4.pdf}"
        echo "Converting $input → A4 imposed → $output"
        python3 "$SCRIPT_DIR/screen2zine.py" "$input" -o "$output" --convert-to A4
        ;;
    -toLetter)
        output="${output:-${stem}-letter.pdf}"
        echo "Converting $input → Letter imposed → $output"
        python3 "$SCRIPT_DIR/screen2zine.py" "$input" -o "$output" --convert-to letter
        ;;
    *)
        echo "Unknown direction: $direction"
        usage
        ;;
esac
