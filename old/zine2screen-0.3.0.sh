#!/bin/bash

# Add rename of pages according to array
# Add put images in sub-folder

# Check if the required tools are installed
command -v pdftoppm >/dev/null 2>&1 || { echo >&2 "pdftoppm is required but not installed. Aborting."; exit 1; }
command -v convert >/dev/null 2>&1 || { echo >&2 "ImageMagick is required but not installed. Aborting."; exit 1; }

# Check if the correct number of arguments are provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 input_pdf output_directory"
    exit 1
fi

input_pdf="$1"
output_dir="$2"

# If output directory is not provided, create one based on PDF name
if [ -z "$output_dir" ]; then
    output_dir="${input_pdf%.*}_output"
fi

# Create output directory if it doesn't exist
mkdir -p "$output_dir"

# Convert each page of the PDF to PNG with optional resolution
if [ -n "$resolution" ]; then
    pdftoppm -png -r "$resolution" "$input_pdf" "${output_dir}/page"
else
    pdftoppm -png "$input_pdf" "${output_dir}/page"
fi

# Get the total number of pages in the PDF file
total_pages=$(pdfinfo "$input_pdf" | grep "Pages" | awk '{print $2}')

# Calculate the number of booklet pages
booklet_pages=$((total_pages * 2))

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
echo "${ordered_page_numbers[@]}"

# Split each PNG image into left and right halves
l=0
for png_file in "${output_dir}"/*.png; do
    filename=$(basename "$png_file")
    page_number=$(echo "$filename" | cut -d'-' -f2 | cut -d'.' -f1)
    convert "$png_file" -crop 50%x100% +repage "${output_dir}/${filename%.*}_%d.png"
    cp "${output_dir}/${filename%.*}_%d.png" "${output_dir}/newbookpage_${ordered_page_numbers[l-1]}"
    rm "$png_file"  # Remove the original PNG file after splitting
    ((l++))    
done

# Reorder the pages
i=1
while [ -f "${output_dir}/page-${i}_1.png" ]; do
    mv "${output_dir}/page-${i}_1.png" "${output_dir}/page_${((2*i-1))}.png"
    cp "${output_dir}/page_$((2*i-1)).png" "${output_dir}/bookpage_${ordered_page_numbers[i-1]}"
    mv "${output_dir}/page-${i}_2.png" "${output_dir}/page_${((2*i))}.png"
    cp "${output_dir}/page_$((2*i-1)).png" "${output_dir}/bookpage_${ordered_page_numbers[i]}"
    ((i++))
done

# doesn't work - do it manually from file list?
# cp "${output_dir}/page_$((2*i-1)).png" "${output_dir}/bookpage_${ordered_page_numbers[i-1]}"

echo "Conversion and reordering complete."
