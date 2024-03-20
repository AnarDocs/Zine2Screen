#!/bin/bash

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

# Create output directory if it doesn't exist
mkdir -p "$output_dir"

# Convert each page of the PDF to PNG
pdftoppm -png "$input_pdf" "${output_dir}/page"

# Get the total number of pages in the PDF file
total_pages=$(pdfinfo "$input_pdf" | grep "Pages" | awk '{print $2}')

echo $total_pages

# Calculate the number of booklet pages
booklet_pages=$((total_pages * 2))

echo $booklet_pages

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

echo ${ordered_page_numbers[@]}

# Loop through the PDF pages and calculate left and right page numbers
for ((i = 1; i <= total_pages; i++)); do
    calculate_page_numbers "$i" "$total_pages"
done

#read -p "pause?"

# Split each PNG image into left and right halves and rename them
index=0
for ((page_number = 1; page_number <= total_pages; page_number++)); do
    left_page="${ordered_page_numbers[$index]}"
    echo $left_page
    right_page="${ordered_page_numbers[$index + 1]}"
#    right_page="${ordered_page_numbers[$index*$page_number]}"
#    right_page="${ordered_page_numbers[$((index * page_number))]}"
    echo $right_page
    convert "${output_dir}/page-${page_number}.png" -crop 50%x100% +repage "${output_dir}/page_${left_page}.png"
#read -p "pause?"
    cp "${output_dir}/page_${left_page}-0.png" "${output_dir}/page_out_${left_page}.png"
    cp "${output_dir}/page_${left_page}-1.png" "${output_dir}/page_out_${right_page}.png"
#    convert "${output_dir}/page-${page_number}.png" -crop 50%x100% +repage "${output_dir}/page_${right_page}.png"
#read -p "pause?"
    rm "${output_dir}/page-${page_number}.png"  # Remove the original PNG file after splitting
    ((index+=2))
    echo $index
done

echo "Conversion and renaming complete."
