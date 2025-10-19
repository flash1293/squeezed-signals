#!/usr/bin/env python3
"""
Phase 1: The Baseline - Denormalized NDJSON

This script implements the simplest possible storage format: one JSON object per line.
This serves as our baseline for comparison - it's human-readable but extremely inefficient.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add lib directory to path for imports
lib_path = Path(__file__).parent / "lib"
sys.path.insert(0, str(lib_path))

from data_generator import load_dataset

def store_as_ndjson(data_points: List[Dict[str, Any]], output_file: str) -> int:
    """
    Store data points as newline-delimited JSON (NDJSON).
    
    Args:
        data_points: List of data point dictionaries
        output_file: Path to output file
        
    Returns:
        File size in bytes
    """
    print(f"Writing {len(data_points):,} data points to NDJSON format...")
    
    with open(output_file, "w") as f:
        for point in data_points:
            # Use compact JSON representation (no spaces)
            json_line = json.dumps(point, separators=(',', ':'))
            f.write(json_line + '\n')
    
    return os.path.getsize(output_file)

def store_as_ndjson(data_points: List[Dict[str, Any]], output_file: str) -> int:
    """
    Store data points as newline-delimited JSON (NDJSON).
    
    Args:
        data_points: List of data point dictionaries
        output_file: Path to output file
        
    Returns:
        File size in bytes
    """
    print(f"Writing {len(data_points):,} data points to NDJSON format...")
    
    with open(output_file, "w") as f:
        for point in data_points:
            json.dump(point, f, separators=(',', ':'))  # No spaces for efficiency
            f.write('\n')
    
    return os.path.getsize(output_file)

def analyze_ndjson_inefficiency(data_points: List[Dict[str, Any]]) -> None:
    """Analyze the sources of inefficiency in NDJSON format."""
    print("\nAnalyzing NDJSON inefficiencies:")
    
    # Count repeated keys
    key_repetitions = {}
    for point in data_points:
        # Count top-level keys
        for key in point.keys():
            key_repetitions[key] = key_repetitions.get(key, 0) + 1
        
        # Count label keys
        for label_key in point.get("labels", {}).keys():
            full_key = f"labels.{label_key}"
            key_repetitions[full_key] = key_repetitions.get(full_key, 0) + 1
    
    print("  Key repetitions:")
    for key, count in sorted(key_repetitions.items()):
        print(f"    '{key}': {count:,} times")
    
    # Count repeated label values
    label_value_repetitions = {}
    for point in data_points:
        for label_key, label_value in point.get("labels", {}).items():
            key_value = f"{label_key}={label_value}"
            label_value_repetitions[key_value] = label_value_repetitions.get(key_value, 0) + 1
    
    print(f"\n  Most repeated label values:")
    sorted_labels = sorted(label_value_repetitions.items(), key=lambda x: x[1], reverse=True)
    for key_value, count in sorted_labels[:10]:
        print(f"    '{key_value}': {count:,} times")
    
    # Estimate redundancy
    sample_point = data_points[0]
    sample_json = json.dumps(sample_point, separators=(',', ':'))
    
    # Estimate redundant key bytes
    key_bytes = sum(len(f'"{key}":') for key in sample_point.keys())
    if "labels" in sample_point:
        key_bytes += sum(len(f'"{key}":') for key in sample_point["labels"].keys())
    
    redundant_key_bytes = key_bytes * len(data_points)
    
    print(f"\n  Estimated redundant key bytes: ~{redundant_key_bytes:,} bytes")
    print(f"  Average JSON size per point: ~{len(sample_json)} bytes")

def main():
    """Main function to execute Phase 1."""
    print("=" * 60)
    print("Phase 1: Baseline - Denormalized NDJSON Storage")
    print("=" * 60)
    
    # Load the dataset
    try:
        data_points = load_dataset()
        print(f"Loaded {len(data_points):,} data points from dataset")
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return 1
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Store as NDJSON
    output_file = output_dir / "metrics.ndjson"
    file_size = store_as_ndjson(data_points, output_file)

    print(f"\n📊 NDJSON Storage Results:")
    print(f"  Output file: {output_file}")
    print(f"  File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
    print(f"  Bytes per data point: {file_size / len(data_points):.2f}")
    
    # Analyze inefficiencies
    analyze_ndjson_inefficiency(data_points)
    
    print(f"\n✅ Phase 1 completed successfully!")
    return 0


if __name__ == "__main__":
    start_time = time.time()
    result = main()
    end_time = time.time()
    
    if result == 0:
        print(f"\n✅ Phase 1 completed in {end_time - start_time:.2f} seconds")
    else:
        print(f"\n❌ Phase 1 failed after {end_time - start_time:.2f} seconds")
    
    sys.exit(result)