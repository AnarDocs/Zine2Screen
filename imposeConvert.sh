#!/bin/bash
# imposeConvert.sh — rescale an imposed booklet PDF between A4 and Letter

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    echo "Usage:"
    echo "  imposeConvert.sh -toA4     input.pdf [output.pdf] [--scale-up N]   Rescale Letter-imposed → A4"
    echo "  imposeConvert.sh -toLetter input.pdf [output.pdf] [--scale-up N]   Rescale A4-imposed → Letter"
    echo ""
    echo "  --scale-up N   Scale up by N% above the fit baseline, clipping into outer margins (default: 0)"
    exit 1
}

if [ $# -lt 2 ]; then usage; fi

direction="$1"
shift

input=""
output=""
scale_up_arg=""

for arg in "$@"; do
    case "$arg" in
        --scale-up=*) scale_up_arg="--scale-up ${arg#*=}" ;;
        --scale-up)   echo "Error: --scale-up requires a value (e.g. --scale-up=10)"; exit 1 ;;
        *.pdf)
            if [ -z "$input" ]; then input="$arg"
            else output="$arg"
            fi ;;
        *)            echo "Unknown argument: $arg"; usage ;;
    esac
done

if [ -z "$input" ]; then echo "Error: no input file specified"; usage; fi
if [ ! -f "$input" ]; then
    echo "Error: file not found: $input"
    exit 1
fi

stem=$(basename "$input" .pdf)

case "$direction" in
    -toA4)
        output="${output:-${stem}-A4.pdf}"
        echo "Converting $input → A4 imposed → $output"
        python3 "$SCRIPT_DIR/screen2zine.py" "$input" -o "$output" --convert-to A4 $scale_up_arg
        ;;
    -toLetter)
        output="${output:-${stem}-letter.pdf}"
        echo "Converting $input → Letter imposed → $output"
        python3 "$SCRIPT_DIR/screen2zine.py" "$input" -o "$output" --convert-to letter $scale_up_arg
        ;;
    *)
        echo "Unknown direction: $direction"
        usage
        ;;
esac
