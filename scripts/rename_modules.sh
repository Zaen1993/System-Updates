#!/bin/bash

OLD_NAME=$1
NEW_NAME=$2

if [ -z "$OLD_NAME" ] || [ -z "$NEW_NAME" ]; then
    echo "Usage: $0 <old_name> <new_name>"
    exit 1
fi

echo "Renaming modules from $OLD_NAME to $NEW_NAME..."

find . -type f -name "*$OLD_NAME*" | while read file; do
    newfile="${file//$OLD_NAME/$NEW_NAME}"
    if [ "$file" != "$newfile" ]; then
        mv "$file" "$newfile"
        echo "Renamed: $file -> $newfile"
    fi
done

find . -type d -name "*$OLD_NAME*" | while read dir; do
    newdir="${dir//$OLD_NAME/$NEW_NAME}"
    if [ "$dir" != "$newdir" ]; then
        mv "$dir" "$newdir"
        echo "Renamed dir: $dir -> $newdir"
    fi
done

grep -rl "$OLD_NAME" . --exclude-dir=.git | while read file; do
    if [ -f "$file" ]; then
        sed -i "s/$OLD_NAME/$NEW_NAME/g" "$file"
        echo "Updated references in: $file"
    fi
done

echo "Done."