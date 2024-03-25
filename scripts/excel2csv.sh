#This script converts all the excel files in the folder globs to csv files

# First, if the files in the folder globs are incorrectly encoded as csv, change the extension to .xlsx
# Then, convert the .xlsx files to .csv files using in2csv from csvkit

# Example usage:
# $ bash excel2csv.sh folder1* folder2* folder3*

#! /bin/bash


read -p "Enter the folders to process (separated by spaces): " folders

for folder in $folders
do
    if [ ! -d "$folder" ]; then
        echo "Folder $folder does not exist. Skipping..."
        continue
    fi

    echo "Processing folder $folder"

    # Change extensions to .xlsx
    for file in "$folder"/*.csv
    do
        mv "$file" "${file/.csv/.xlsx}"
    done

    # Convert .xlsx files to .csv files
    for file in "$folder"/*.xlsx
    do
        in2csv "$file" > "${file/.xlsx/.csv}"
    done

    # Remove the .xlsx files
    for file in "$folder"/*.xlsx
    do
        rm "$file"
    done
done
