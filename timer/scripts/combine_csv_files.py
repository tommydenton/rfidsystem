#!/usr/bin/env python3
"""
CSV File Combiner
Combines multiple timeresults CSV files into a single file with one header.
"""

import csv
import glob
import os
from pathlib import Path


def combine_csv_files(input_pattern, output_file):
    """
    Combine multiple CSV files matching a pattern into a single file.
    
    Args:
        input_pattern (str): Glob pattern to match input files (e.g., 'timeresults_*.csv')
        output_file (str): Path to the output combined file
    """
    # Find all files matching the pattern
    input_files = glob.glob(input_pattern)
    
    if not input_files:
        print(f"No files found matching pattern: {input_pattern}")
        return
    
    input_files.sort()  # Sort files for consistent ordering
    print(f"Found {len(input_files)} files to combine:")
    for file in input_files:
        print(f"  - {file}")
    
    header_written = False
    total_rows = 0
    
    with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
        writer = None
        
        for file_path in input_files:
            print(f"Processing: {file_path}")
            
            with open(file_path, 'r', newline='', encoding='utf-8') as infile:
                reader = csv.reader(infile)
                
                # Read the header
                try:
                    header = next(reader)
                except StopIteration:
                    print(f"Warning: {file_path} is empty, skipping...")
                    continue
                
                # Write header only once
                if not header_written:
                    writer = csv.writer(outfile)
                    writer.writerow(header)
                    header_written = True
                    print(f"Header written: {', '.join(header)}")
                
                # Write all data rows from this file
                file_rows = 0
                for row in reader:
                    if row:  # Skip empty rows
                        writer.writerow(row)
                        file_rows += 1
                        total_rows += 1
                
                print(f"  Added {file_rows} data rows from {file_path}")
    
    print(f"\nCombined files successfully!")
    print(f"Total data rows written: {total_rows}")
    print(f"Output file: {output_file}")


def main():
    """Main function to run the CSV combiner."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    
    # Define input pattern and output file
    input_pattern = str(script_dir / "timeresults_*.csv")
    output_file = str(script_dir / "combined_timeresults.csv")
    
    print("CSV File Combiner")
    print("=" * 50)
    print(f"Input pattern: {input_pattern}")
    print(f"Output file: {output_file}")
    print()
    
    # Combine the files
    combine_csv_files(input_pattern, output_file)
    
    # Show some stats about the output file
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
        print(f"Final output file has {line_count} total lines (including header)")


if __name__ == "__main__":
    main()