#!/bin/bash
exec 2>&1

silent=0

if [[ $silent -eq 1 ]]; then
  # Redirect standard output (stdout) to /dev/null for silence
  exec &> /dev/null
fi

# Check if the required tools are installed
command -v pdftoppm >/dev/null 2>&1 || { echo >&2 "pdftoppm is required but not installed. Aborting."; exit 1; }
command -v convert >/dev/null 2>&1 || { echo >&2 "ImageMagick is required but not installed. Aborting."; exit 1; }
command -v gs >/dev/null 2>&1 || { echo >&2 "Ghostscript is required but not installed. Aborting."; exit 1; }
command -v img2pdf >/dev/null 2>&1 || { echo >&2 "Img2PDF is missing but may be needed."; }

# Parse command-line resolution option
while getopts ":r:" opt; do
  case $opt in
    r) resolution=$OPTARG ;;
    \?) echo "Invalid option: -$OPTARG" >&2; exit 1 ;;
  esac
done
shift $((OPTIND-1))

# Check if the correct number of arguments are provided
if [ -z "$1" ]; then
  echo "Usage: $0 input_pdf output_directory"
  exit 1
fi

input_pdf="$1"
output_dir="$2"

# If output directory is not provided, create one based on PDF name
if [ -z "$output_dir" ]; then
    output_dir="${input_pdf%.*}_output"
    echo "Creating output directory: $output_dir"
fi

output_dir="$output_dir/images"

if [[ -d "$output_dir" ]]; then
  echo "Error: Directory \"$output_dir\" already exists. Exiting."
  exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$output_dir"

echo "Exporting PDF pages to PNG (this may take a few minutes)"
# Convert each page of the PDF to PNG with optional resolution
if [ -n "$resolution" ]; then
    echo "Setting resolution to $resolution"
    pdftoppm -progress -png -r "$resolution" "$input_pdf" "${output_dir}/page"
else
    pdftoppm -progress -png "$input_pdf" "${output_dir}/page"
    resolution=150
fi

# Get the total number of pages in the PDF file
total_pages=$(pdfinfo "$input_pdf" | grep "Pages" | awk '{print $2}')
echo "Total PDF pages: $total_pages"

# Calculate the number of booklet pages
booklet_pages=$((total_pages * 2))
echo "Booklet pages: $booklet_pages"

# Array to store the page numbers in the desired order
ordered_page_numbers=()

# Function to determine left and right page numbers
calculate_page_numbers() {
    local page_num=$1
    local total_pages=$2

    if ((total_pages % 2 == 0)); then
        if ((page_num % 2 == 0)); then
            left_page=$((page_num))
            right_page=$((booklet_pages - page_num + 1))
        else
            left_page=$((booklet_pages - page_num + 1))
            right_page=$((page_num))
        fi
    else
        if ((page_num % 2 == 0)); then
            left_page=$((booklet_pages - page_num + 1))
            right_page=$((page_num))
        else
            left_page=$((page_num))
            right_page=$((booklet_pages - page_num + 1))
        fi
    fi

    # Add left and right page numbers to the ordered array
    ordered_page_numbers+=("$left_page")
    ordered_page_numbers+=("$right_page")
}

# Loop through the PDF pages and calculate left and right page numbers
for ((i = 1; i <= total_pages; i++)); do
    calculate_page_numbers "$i" "$total_pages"
done
echo "Booklet page arrangement: ${ordered_page_numbers[@]}"

# Split each PNG image into left and right halves
l=0
for png_file in "${output_dir}"/*.png; do
    filename=$(basename "$png_file")
    page_number=$(echo "$filename" | cut -d'-' -f2 | cut -d'.' -f1)
    convert "$png_file" -crop 50%x100% +repage "${output_dir}/${filename%.*}_%d.png" 
    echo "Splitting PDF page $page_number"
    # could convert as it finds latest filename?
    rm "$png_file"  # Remove the original PNG file after splitting
    ((l++))    
done

echo "Reordering PNG pages into booklet order"
# Reorder the pages
i=0
for page in "${output_dir}"/*.png; do
    mv "$page" "${output_dir}/${input_pdf%.*}-screen-page_${ordered_page_numbers[i]}.png"
    echo "Reordered page exported: $((i + 1)) of ${booklet_pages} (no. ${ordered_page_numbers[i]})"
    ((i++))
done

# Convert images to PDF
echo "Converting booklet images to screen PDF"
if command -v img2pdf &>/dev/null; then
    img2pdf -o "${input_pdf%.*}-screen.pdf" "${output_dir}"/*.png
else
    # Convert PNG files to PDF using ImageMagick - doesn't work with default policy
    convert -density $resolution "${output_dir}/*.png" "${input_pdf%.*}-screen.pdf"
fi

echo "Conversion and reordering complete."
