#!/bin/bash
# Usage: ./script.sh [directory]
# If no directory is specified, the script defaults to the current directory.

dir="${1:-.}"

# Use -maxdepth 1 to limit the search to the specified directory only.
find "$dir" -maxdepth 1 -type f \( -name "*.rb" -o -name "*.erb" -o -name "*.py" \) | while IFS= read -r file; do
    echo "$file"
    echo "-------------"
    cat "$file"
    echo ""  # Optional: extra newline for readability.
done

