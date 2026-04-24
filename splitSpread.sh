#!/bin/bash

# Default values
resolution=150
booklet_flag="false"
compile_flag="false"
extract_flag="false"
flip_flag="false"
extract_pages=()
output_dir="."

# Parse options
for arg in "$@"; do
    case $arg in
        -r=*)
            resolution="${arg#*=}"
            shift
            ;;
        -o=*)
            output_dir="${arg#*=}"
            shift
            ;;
        -b)
            booklet_flag="true"
            shift
            ;;
        -c)
            compile_flag="true"
            shift
            ;;
        -f)
            flip_flag="true"
            shift
            ;;
        -x=*)
            extract_flag="true"
            IFS=',' read -ra extract_pages <<< "${arg#*=}"
            shift
            ;;
        *.pdf)
            input_pdf="$arg"
            filename=$(basename "$input_pdf" .pdf)
            shift
            ;;
        *)
            echo "Unknown argument: $arg"
            exit 1
            ;;
    esac
done

if [ ! -f "$input_pdf" ]; then
    echo "Error: Input PDF file not found: $input_pdf"
    exit 1
fi

if [ "$flip_flag" == "true" ] && [ "$compile_flag" != "true" ]; then
    echo "Warning: -f (flip) has no effect without -c (compile)."
fi

# Create output directory if needed
if [ "$output_dir" != "." ]; then
    mkdir -p "$output_dir"
fi

# If -x flag is used, extract specific original pages and exit
if [ "$extract_flag" == "true" ]; then
    echo "Extracting original pages: ${extract_pages[*]}"
    for p in "${extract_pages[@]}"; do
        padded_page=$(printf "%04d" "$p")
        convert -density "$resolution" "$input_pdf[$((p-1))]" -quality 100 "${output_dir}/${filename}-orig-page-${padded_page}.pdf"
    done
    echo "Extraction complete."
    exit 0
fi

# Get total pages in input PDF
total_pages=$(pdfinfo "$input_pdf" | awk '/^Pages:/ {print $2}')
echo "Total pages in PDF: $total_pages"

# Output page counter
output_page_counter=1

# Split pages
for ((i = 0; i < total_pages; i++)); do
    page_img="page-${i}.png"
    convert -density "$resolution" "$input_pdf[$i]" -quality 100 "$page_img"

    # Get image dimensions
    width=$(identify -format "%w" "$page_img")
    height=$(identify -format "%h" "$page_img")
    half_width=$((width / 2))

    # Crop left half
    convert "$page_img" -crop "${half_width}x${height}+0+0" +repage "left-${i}.png"
    convert "left-${i}.png" -density "$resolution" -quality 100 "$(printf "${output_dir}/${filename}-page-%04d.pdf" $output_page_counter)"
    ((output_page_counter++))

    # Crop right half
    convert "$page_img" -crop "${half_width}x${height}+${half_width}+0" +repage "right-${i}.png"
    convert "right-${i}.png" -density "$resolution" -quality 100 "$(printf "${output_dir}/${filename}-page-%04d.pdf" $output_page_counter)"
    ((output_page_counter++))

    # Clean up temporary images
    rm "$page_img" "left-${i}.png" "right-${i}.png"
done

echo "Page splitting complete!"

# If -b flag is set, rename pages to booklet order
if [ "$booklet_flag" == "true" ]; then
    echo "Renaming pages to booklet print order..."

    total_output_pages=$((output_page_counter - 1))
    if (( total_output_pages % 4 != 0 )); then
        echo "Warning: Total output pages is not a multiple of 4. Booklet may not fold evenly."
    fi

    # Generate booklet sequence
    declare -a booklet_sequence
    total_pairs=$((total_output_pages / 2))
    for ((i=1, j=total_output_pages; i<=total_pairs; i++, j--)); do
        booklet_sequence+=("$(printf "${output_dir}/${filename}-page-%04d.pdf" $j)")
        booklet_sequence+=("$(printf "${output_dir}/${filename}-page-%04d.pdf" $i)")
    done

    # Rename files in booklet order
    for ((k=0; k<${#booklet_sequence[@]}; k++)); do
        src="${booklet_sequence[$k]}"
        dest=$(printf "${output_dir}/${filename}-booklet-page-%04d.pdf" $((k + 1)))
        mv "$src" "$dest"
    done

    echo "Booklet renaming complete!"
fi

# If -c flag is set, compile the pages
if [ "$compile_flag" == "true" ]; then
    echo "Compiling pages into a single PDF..."

    if [ "$booklet_flag" == "true" ]; then
        booklet_files=("${output_dir}/${filename}"-booklet-page-*.pdf)
        if [ ! -f "${booklet_files[0]}" ]; then
            echo "Error: No booklet pages found to compile."
            exit 1
        fi
        compiled="${output_dir}/${filename}-booklet-compiled.pdf"
        pdftk "${booklet_files[@]}" cat output "$compiled"
    else
        normal_files=("${output_dir}/${filename}"-page-*.pdf)
        if [ ! -f "${normal_files[0]}" ]; then
            echo "Error: No split pages found to compile."
            exit 1
        fi
        compiled="${output_dir}/${filename}-compiled.pdf"
        pdftk "${normal_files[@]}" cat output "$compiled"
    fi

    echo "Compilation complete!"

    # If -f flag is set, rotate odd pages (1, 3, 5...) 180° in the compiled PDF
    if [ "$flip_flag" == "true" ]; then
        echo "Flipping odd pages..."
        total_compiled=$((output_page_counter - 1))
        cat_args=()
        for ((i=1; i<=total_compiled; i++)); do
            if (( i % 2 == 0 )); then
                cat_args+=("${i}S")
            else
                cat_args+=("$i")
            fi
        done
        tmp="${compiled%.pdf}-tmp.pdf"
        pdftk "$compiled" cat "${cat_args[@]}" output "$tmp" && mv "$tmp" "$compiled"
        echo "Flip complete!"
    fi
fi
