#!/usr/bin/env python3
"""
Phase 5: Columnar Storage + zstd

Instead of storing one JSON object per data point, this approach groups all data points
for the same time series together, storing timestamps and values in arrays with zstd
compression applied for additional space savings.
"""

import os
import sys
import pickle
import msgpack
import zstandard as zstd
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict

# Add project root to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DEFAULT_ZSTD_LEVEL

def create_series_key(metric_name: str, labels: Dict[str, str]) -> str:
    """Create a consistent series key from metric name and labels."""
    sorted_labels = sorted(labels.items())
    label_str = ",".join(f"{k}={v}" for k, v in sorted_labels)
    return f"{metric_name}{{{label_str}}}"

def convert_to_columnar_format(data_points: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convert row-based data to columnar format grouped by time series.
    
    Args:
        data_points: List of data point dictionaries
        
    Returns:
        Dictionary with series metadata and columnar data
    """
    print(f"Converting {len(data_points):,} data points to columnar format...")
    
    # Create series dictionary and collect data by series
    series_metadata = {}
    series_data = defaultdict(lambda: {"timestamps": [], "values": []})
    series_id_map = {}
    next_series_id = 0
    
    for point in data_points:
        # Create series key
        series_key = create_series_key(point["metric_name"], point["labels"])
        
        # Assign series ID if not seen before
        if series_key not in series_id_map:
            series_id = str(next_series_id)
            series_id_map[series_key] = series_id
            series_metadata[series_id] = {
                "name": point["metric_name"],
                "labels": point["labels"].copy()
            }
            next_series_id += 1
        else:
            series_id = series_id_map[series_key]
        
        # Add data point to series
        series_data[series_id]["timestamps"].append(point["timestamp"])
        series_data[series_id]["values"].append(point["value"])
    
    # Sort timestamps and values within each series
    for series_id, data in series_data.items():
        # Sort by timestamp
        sorted_pairs = sorted(zip(data["timestamps"], data["values"]))
        data["timestamps"] = [ts for ts, _ in sorted_pairs]
        data["values"] = [val for _, val in sorted_pairs]
    
    columnar_structure = {
        "series_metadata": series_metadata,
        "series_data": dict(series_data)  # Convert defaultdict to regular dict
    }
    
    print(f"Created {len(series_metadata)} unique time series")
    
    return columnar_structure

def analyze_columnar_benefits(original_data: List[Dict[str, Any]], columnar_data: Dict[str, Any]) -> None:
    """Analyze the benefits of columnar format."""
    print("\nAnalyzing columnar format benefits:")
    
    num_series = len(columnar_data["series_metadata"])
    total_points = sum(len(series["timestamps"]) for series in columnar_data["series_data"].values())
    
    print(f"  Original format: {len(original_data):,} individual dictionaries")
    print(f"  Columnar format: {num_series} series with {total_points:,} total points")
    print(f"  Average points per series: {total_points / num_series:.1f}")
    
    # Count metadata reduction
    unique_metric_names = set(meta["name"] for meta in columnar_data["series_metadata"].values())
    unique_label_keys = set()
    unique_label_values = set()
    
    for meta in columnar_data["series_metadata"].values():
        for key, value in meta["labels"].items():
            unique_label_keys.add(key)
            unique_label_values.add(value)
    
    print(f"\n  Metadata consolidation:")
    print(f"    Unique metric names: {len(unique_metric_names)}")
    print(f"    Unique label keys: {len(unique_label_keys)}")
    print(f"    Unique label values: {len(unique_label_values)}")
    
    # Estimate space savings from eliminating redundant keys
    sample_point = original_data[0]
    redundant_keys_per_point = len('"timestamp":') + len('"metric_name":') + len('"value":') + len('"labels":')
    redundant_keys_per_point += sum(len(f'"{key}":') for key in sample_point.get("labels", {}).keys())
    
    print(f"\n  Estimated key redundancy eliminated:")
    print(f"    ~{redundant_keys_per_point * len(original_data):,} redundant key characters")

def store_as_columnar(columnar_data: Dict[str, Any], output_file: str) -> int:
    """
    Store columnar data using MessagePack binary format.
    
    Args:
        columnar_data: Columnar format data
        output_file: Path to output file
        
    Returns:
        File size in bytes
    """
    print(f"\nWriting columnar data to MessagePack format...")
    
    with open(output_file, "wb") as f:
        msgpack.dump(columnar_data, f, use_bin_type=True)
    
    return os.path.getsize(output_file)

def verify_columnar_data(columnar_data: Dict[str, Any]) -> None:
    """Verify the integrity of columnar data."""
    print("\nVerifying columnar data integrity...")
    
    series_metadata = columnar_data["series_metadata"]
    series_data = columnar_data["series_data"]
    
    # Check that all series have both metadata and data
    metadata_ids = set(series_metadata.keys())
    data_ids = set(series_data.keys())
    
    if metadata_ids != data_ids:
        print(f"  ⚠️  Warning: Metadata and data series IDs don't match")
        print(f"     Metadata only: {metadata_ids - data_ids}")
        print(f"     Data only: {data_ids - metadata_ids}")
    else:
        print(f"  ✅ All {len(metadata_ids)} series have both metadata and data")
    
    # Check data consistency within series
    total_points = 0
    for series_id, data in series_data.items():
        timestamps = data["timestamps"]
        values = data["values"]
        
        if len(timestamps) != len(values):
            print(f"  ⚠️  Warning: Series {series_id} has mismatched timestamps/values")
        
        total_points += len(timestamps)
        
        # Check if timestamps are sorted
        if timestamps != sorted(timestamps):
            print(f"  ⚠️  Warning: Series {series_id} has unsorted timestamps")
    
    print(f"  Total data points verified: {total_points:,}")

def main():
    """Main function to execute Phase 5."""
    print("=" * 60)
    print("Phase 5: Columnar Storage + zstd")
    print("=" * 60)
    
    # Load the generated dataset
    raw_data_file = "output/raw_dataset.pkl"
    if not os.path.exists(raw_data_file):
        print(f"❌ Error: {raw_data_file} not found. Please run 00_generate_data.py first.")
        return

    with open(raw_data_file, "rb") as f:
        data_points = pickle.load(f)

    print(f"Loaded {len(data_points):,} data points from dataset")

    # Convert to columnar format
    columnar_data = convert_to_columnar_format(data_points)

    # Verify data integrity
    verify_columnar_data(columnar_data)

    # Analyze benefits
    analyze_columnar_benefits(data_points, columnar_data)

    # Store as MessagePack first, then compress
    print(f"\nWriting columnar data to MessagePack format...")
    uncompressed_data = msgpack.packb(columnar_data, use_bin_type=True)
    
    # Apply zstd compression
    print(f"Applying zstd compression...")
    compressor = zstd.ZstdCompressor(level=DEFAULT_ZSTD_LEVEL)
    compressed_data = compressor.compress(uncompressed_data)
    
    # Write compressed data
    output_file = "output/metrics.columnar.zst"
    with open(output_file, "wb") as f:
        f.write(compressed_data)
    
    file_size = len(compressed_data)
    uncompressed_size = len(uncompressed_data)
    compression_ratio = uncompressed_size / file_size    # Compare with previous phases
    ndjson_file = "output/metrics.ndjson"
    bintable_file = "output/metrics.bintable.zst"
    
    ndjson_size = os.path.getsize(ndjson_file) if os.path.exists(ndjson_file) else None
    bintable_size = os.path.getsize(bintable_file) if os.path.exists(bintable_file) else None
    
    print(f"\n📊 Columnar Storage + zstd Results:")
    print(f"  Output file: {output_file}")
    print(f"  Uncompressed size: {uncompressed_size:,} bytes")
    print(f"  Compressed size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
    print(f"  zstd compression ratio: {compression_ratio:.2f}x")
    print(f"  Bytes per data point: {file_size / len(data_points):.2f}")
    
    if ndjson_size:
        overall_compression = ndjson_size / file_size
        space_saved = ndjson_size - file_size
        print(f"\n📉 Compression vs NDJSON:")
        print(f"  NDJSON size: {ndjson_size:,} bytes")
        print(f"  Columnar + zstd size: {file_size:,} bytes")
        print(f"  Overall compression ratio: {overall_compression:.2f}x")
        space_saved = ndjson_size - file_size
        print(f"  Space saved: {space_saved:,} bytes ({space_saved / ndjson_size * 100:.1f}%)")
    
    if bintable_size:
        vs_bintable = bintable_size / file_size
        print(f"\n📉 Comparison vs Binary Table + zstd:")
        print(f"  Binary Table + zstd size: {bintable_size:,} bytes")
        print(f"  Columnar + zstd size: {file_size:,} bytes")
        print(f"  Ratio: {vs_bintable:.2f}x {'better' if vs_bintable > 1 else 'worse'}")
    
    print(f"\n✅ Phase 5 completed successfully!")
    
    return {
        "format": "Columnar (MessagePack)",
        "file_size": file_size,
        "compression_ratio": ndjson_size / file_size if ndjson_size else 1.0,
        "data_points": len(data_points)
    }

if __name__ == "__main__":
    import time
    start_time = time.time()
    result = main()
    end_time = time.time()
    
    if result:
        print(f"\n✅ Phase 5 completed in {end_time - start_time:.2f} seconds")
    else:
        print(f"\n❌ Phase 5 failed after {end_time - start_time:.2f} seconds")