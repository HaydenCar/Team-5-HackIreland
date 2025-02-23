#!/bin/bash

# Ensure a directory argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <directory>"
  exit 1
fi

# Directory to search
search_dir="$1"

# Target filenames
declare -A files_to_find=(
  ["index.erb"]="erb"
  ["result.erb"]="erb"
  ["book.erb"]="erb"
  ["books.erb"]="erb"
  ["app.rb"]="rb"
  ["Gemfile"]="ruby"
  ["styles.css"]="css"
)

# Find and print matching files
while IFS= read -r file; do
  filename=$(basename "$file")
  if [[ ${files_to_find[$filename]+_} ]]; then
    echo "$filename - ${files_to_find[$filename]}"
  fi
done < <(find "$search_dir" -type f \( -name "index.erb" -o -name "result.erb" -o -name "book.erb" -o -name "books.erb" -o -name "app.rb" -o -name "Gemfile" -o -name "styles.css" \) 2>/dev/null)


