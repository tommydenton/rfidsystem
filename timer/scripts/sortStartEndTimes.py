#!/usr/bin/env python3
"""
Race Timing Data Deduplicator - Minimal Version (No External Dependencies)

This script processes race timing data to remove duplicate entries and identify
start/end times for each racer based on time clustering.

Requirements:
- Valid tag_IDs must be exactly 28 characters (letters and numbers)
- Start time: LAST timestamp from the first time cluster
- End time: FIRST timestamp from the last time cluster
- Time clusters are separated by a configurable gap threshold
"""

import csv
import re
import argparse
import sys
from collections import defaultdict


def is_valid_tag_id(tag_id):
    """
    Check if tag_id is valid (28 characters, letters and numbers only)
    """
    if not isinstance(tag_id, str):
        return False
    return len(tag_id) == 28 and re.match(r'^[A-Za-z0-9]{28}$', tag_id)


def find_time_clusters(timestamps, gap_threshold_minutes=2):
    """
    Group timestamps into clusters based on time gaps
    
    Args:
        timestamps: List of Unix timestamps (integers)
        gap_threshold_minutes: Minimum gap in minutes to separate clusters
    
    Returns:
        List of lists, each containing timestamps in a cluster
    """
    if not timestamps:
        return []
    
    # Sort timestamps
    sorted_timestamps = sorted(timestamps)
    gap_threshold_seconds = gap_threshold_minutes * 60
    
    clusters = []
    current_cluster = [sorted_timestamps[0]]
    
    for i in range(1, len(sorted_timestamps)):
        # Convert timestamp difference to seconds
        time_gap = (sorted_timestamps[i] - sorted_timestamps[i-1]) / 1000
        
        if time_gap > gap_threshold_seconds:
            # Start new cluster
            clusters.append(current_cluster)
            current_cluster = [sorted_timestamps[i]]
        else:
            # Add to current cluster
            current_cluster.append(sorted_timestamps[i])
    
    # Don't forget the last cluster
    clusters.append(current_cluster)
    
    return clusters


def process_racer_data(racer_records, gap_threshold_minutes=2):
    """
    Process timing data for a single racer
    
    Args:
        racer_records: List of dictionaries containing all records for one tag_id
        gap_threshold_minutes: Gap threshold for clustering
    
    Returns:
        List of dictionaries containing the records to keep
    """
    # Get all timestamps for clustering
    timestamps = [int(record['timestamp']) for record in racer_records]
    clusters = find_time_clusters(timestamps, gap_threshold_minutes)
    
    records_to_keep = []
    
    if len(clusters) == 1:
        # Only one cluster - this is start time only
        # Keep the LAST timestamp from this cluster
        last_timestamp = max(clusters[0])
        start_record = next(r for r in racer_records if int(r['timestamp']) == last_timestamp)
        records_to_keep.append(start_record)
        
    elif len(clusters) >= 2:
        # Multiple clusters - we have start and end times
        # Start time: LAST timestamp from FIRST cluster
        first_cluster = clusters[0]
        last_timestamp_first_cluster = max(first_cluster)
        start_record = next(r for r in racer_records if int(r['timestamp']) == last_timestamp_first_cluster)
        records_to_keep.append(start_record)
        
        # End time: FIRST timestamp from LAST cluster
        last_cluster = clusters[-1]
        first_timestamp_last_cluster = min(last_cluster)
        end_record = next(r for r in racer_records if int(r['timestamp']) == first_timestamp_last_cluster)
        records_to_keep.append(end_record)
    
    return records_to_keep


def deduplicate_race_data(input_file, output_file=None, gap_threshold_minutes=2):
    """
    Main function to process race timing data
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file (optional)
        gap_threshold_minutes: Time gap threshold for clustering
    """
    print(f"Processing race timing data from: {input_file}")
    print(f"Gap threshold: {gap_threshold_minutes} minutes")
    
    # Read the CSV file
    try:
        with open(input_file, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            all_records = list(reader)
            fieldnames = reader.fieldnames
    except Exception as e:
        print(f"Error reading file {input_file}: {e}")
        return None
    
    print(f"Loaded {len(all_records)} total records")
    
    # Filter for valid tag_IDs and group by tag_id
    valid_records = []
    racers_data = defaultdict(list)
    
    for record in all_records:
        tag_id = record.get('tag_id', '')
        if is_valid_tag_id(tag_id):
            valid_records.append(record)
            racers_data[tag_id].append(record)
    
    print(f"Found {len(valid_records)} records with valid 28-character tag_IDs")
    print(f"Filtered out {len(all_records) - len(valid_records)} records with invalid tag_IDs")
    
    if len(valid_records) == 0:
        print("No valid records found!")
        return None
    
    # Process each unique tag_id
    all_processed_records = []
    
    print(f"Processing {len(racers_data)} unique racers...")
    
    for tag_id, racer_records in racers_data.items():
        processed_records = process_racer_data(racer_records, gap_threshold_minutes)
        all_processed_records.extend(processed_records)
    
    print(f"Reduced from {len(valid_records)} to {len(all_processed_records)} records")
    
    # Output results
    if output_file:
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_processed_records)
            print(f"Results saved to: {output_file}")
        except Exception as e:
            print(f"Error writing to {output_file}: {e}")
            return None
    else:
        # Print to stdout
        print("\nProcessed data:")
        if all_processed_records:
            print(','.join(fieldnames))
            for record in all_processed_records:
                print(','.join(str(record.get(field, '')) for field in fieldnames))
    
    # Summary statistics
    racer_counts = defaultdict(int)
    for record in all_processed_records:
        racer_counts[record['tag_id']] += 1
    
    start_only_count = sum(1 for count in racer_counts.values() if count == 1)
    complete_pairs_count = sum(1 for count in racer_counts.values() if count == 2)
    
    print(f"\nSummary:")
    print(f"Racers with start time only: {start_only_count}")
    print(f"Racers with both start and end times: {complete_pairs_count}")
    
    return all_processed_records


def main():
    parser = argparse.ArgumentParser(description='Deduplicate race timing data')
    parser.add_argument('input_file', help='Input CSV file path')
    parser.add_argument('-o', '--output', help='Output CSV file path (default: print to stdout)')
    parser.add_argument('-g', '--gap', type=float, default=2.0, 
                       help='Time gap threshold in minutes (default: 2.0)')
    
    args = parser.parse_args()
    
    # Validate gap threshold
    if args.gap <= 0 or args.gap > 300:
        print("Error: Gap threshold must be between 0 and 300 minutes")
        sys.exit(1)
    
    result = deduplicate_race_data(args.input_file, args.output, args.gap)
    
    if result is not None:
        print("Processing completed successfully!")
    else:
        print("Processing failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
    