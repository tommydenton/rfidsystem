#!/usr/bin/env python3
"""
Race Times Merger - Combine start and end times into single rows

This script processes deduplicated race timing data and merges start/end times
for each racer into a single row with duration calculation.

Output format: id,tag_type,tag_id,tag_position,timestamp_h_start,timestamp_h_end,duration
"""

import csv
import argparse
import sys
from datetime import datetime
from collections import defaultdict


def parse_timestamp(timestamp_str):
    """
    Parse ISO timestamp string to datetime object
    """
    try:
        # Handle both formats: with and without microseconds
        if '.' in timestamp_str:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except Exception as e:
        print(f"Error parsing timestamp '{timestamp_str}': {e}")
        return None


def format_duration(start_time, end_time):
    """
    Calculate and format duration between start and end times
    Returns duration in format "HH:MM:SS"
    """
    if not start_time or not end_time:
        return ""
    
    duration = end_time - start_time
    total_seconds = int(duration.total_seconds())
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def merge_race_times(input_file, output_file=None):
    """
    Merge start and end times into single rows per racer
    
    Args:
        input_file: Path to input CSV file (deduplicated data)
        output_file: Path to output CSV file (optional)
    """
    print(f"Processing race timing data from: {input_file}")
    
    # Read the CSV file
    try:
        with open(input_file, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            all_records = list(reader)
            fieldnames = reader.fieldnames
    except Exception as e:
        print(f"Error reading file {input_file}: {e}")
        return None
    
    print(f"Loaded {len(all_records)} records")
    
    # Group records by tag_id
    racers_data = defaultdict(list)
    for record in all_records:
        tag_id = record.get('tag_id', '')
        racers_data[tag_id].append(record)
    
    print(f"Found {len(racers_data)} unique racers")
    
    # Process each racer
    merged_records = []
    racers_with_both = 0
    racers_start_only = 0
    
    for tag_id, records in racers_data.items():
        if len(records) == 1:
            # Only start time
            record = records[0]
            merged_record = {
                'id': record.get('id', ''),
                'tag_type': record.get('tag_type', ''),
                'tag_id': tag_id,
                'tag_position': record.get('tag_position', ''),
                'timestamp_h_start': record.get('timestamp_h', ''),
                'timestamp_h_end': '',
                'duration': ''
            }
            merged_records.append(merged_record)
            racers_start_only += 1
            
        elif len(records) == 2:
            # Both start and end times - sort by timestamp to identify start vs end
            sorted_records = sorted(records, key=lambda x: int(x.get('timestamp', 0)))
            start_record = sorted_records[0]
            end_record = sorted_records[1]
            
            # Parse timestamps for duration calculation
            start_time = parse_timestamp(start_record.get('timestamp_h', ''))
            end_time = parse_timestamp(end_record.get('timestamp_h', ''))
            duration = format_duration(start_time, end_time)
            
            # Use start record as base for id, tag_type, tag_position
            merged_record = {
                'id': start_record.get('id', ''),
                'tag_type': start_record.get('tag_type', ''),
                'tag_id': tag_id,
                'tag_position': start_record.get('tag_position', ''),
                'timestamp_h_start': start_record.get('timestamp_h', ''),
                'timestamp_h_end': end_record.get('timestamp_h', ''),
                'duration': duration
            }
            merged_records.append(merged_record)
            racers_with_both += 1
            
        else:
            print(f"Warning: Racer {tag_id} has {len(records)} records (expected 1 or 2)")
    
    print(f"Processed {len(merged_records)} racers:")
    print(f"  - {racers_with_both} racers with both start and end times")
    print(f"  - {racers_start_only} racers with start time only")
    
    # Define output fieldnames
    output_fieldnames = ['id', 'tag_type', 'tag_id', 'tag_position', 
                        'timestamp_h_start', 'timestamp_h_end', 'duration']
    
    # Output results
    if output_file:
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=output_fieldnames)
                writer.writeheader()
                writer.writerows(merged_records)
            print(f"Results saved to: {output_file}")
        except Exception as e:
            print(f"Error writing to {output_file}: {e}")
            return None
    else:
        # Print to stdout
        print("\nMerged data (first 10 rows):")
        print(','.join(output_fieldnames))
        for i, record in enumerate(merged_records[:10]):
            row = ','.join(str(record.get(field, '')) for field in output_fieldnames)
            print(row)
        if len(merged_records) > 10:
            print(f"... and {len(merged_records) - 10} more rows")
    
    # Show some sample durations
    completed_races = [r for r in merged_records if r['duration']]
    if completed_races:
        print(f"\nSample race durations:")
        for i, record in enumerate(completed_races[:5]):
            print(f"  Racer {record['tag_id'][-8:]}: {record['duration']}")
    
    return merged_records


def main():
    parser = argparse.ArgumentParser(description='Merge race start/end times into single rows')
    parser.add_argument('input_file', help='Input CSV file path (deduplicated timing data)')
    parser.add_argument('-o', '--output', help='Output CSV file path (default: print sample to stdout)')
    
    args = parser.parse_args()
    
    result = merge_race_times(args.input_file, args.output)
    
    if result is not None:
        print("Merging completed successfully!")
    else:
        print("Merging failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()