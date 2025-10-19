#!/usr/bin/env python3
"""
Phase 7: Downsampling + zstd - Multi-Resolution Storage with Compression

This script demonstrates how to reduce data volume for long-term storage
by aggregating high-resolution data into lower-resolution "rollups" with
zstd compression applied for maximum space efficiency.
"""

import os
import pickle
import statistics
import zstandard as zstd
from typing import List, Dict, Any, Tuple, Callable
from collections import defaultdict
import msgpack

def create_time_buckets(timestamps: List[int], values: List[float], interval_seconds: int) -> Dict[int, List[Tuple[int, float]]]:
    """
    Group data points into time buckets based on the specified interval.
    
    Args:
        timestamps: List of timestamps
        values: List of values
        interval_seconds: Bucket interval in seconds
        
    Returns:
        Dictionary mapping bucket_start_time to list of (timestamp, value) pairs
    """
    buckets = defaultdict(list)
    
    for ts, val in zip(timestamps, values):
        # Calculate bucket start time (aligned to interval)
        bucket_start = (ts // interval_seconds) * interval_seconds
        buckets[bucket_start].append((ts, val))
    
    return dict(buckets)

def calculate_aggregates(bucket_data: List[Tuple[int, float]]) -> Dict[str, float]:
    """
    Calculate various aggregates for a bucket of data points.
    
    Args:
        bucket_data: List of (timestamp, value) tuples in the bucket
        
    Returns:
        Dictionary of aggregate names to values
    """
    if not bucket_data:
        return {}
    
    values = [val for _, val in bucket_data]
    
    aggregates = {
        "count": len(values),
        "sum": sum(values),
        "avg": statistics.mean(values),
        "min": min(values),
        "max": max(values),
        "first": values[0],
        "last": values[-1]
    }
    
    # Add percentiles if we have enough data points
    if len(values) >= 2:
        try:
            aggregates["median"] = statistics.median(values)
        except:
            aggregates["median"] = aggregates["avg"]
    
    if len(values) >= 4:
        try:
            sorted_values = sorted(values)
            p95_idx = int(0.95 * len(sorted_values))
            p99_idx = int(0.99 * len(sorted_values))
            
            aggregates["p95"] = sorted_values[min(p95_idx, len(sorted_values) - 1)]
            aggregates["p99"] = sorted_values[min(p99_idx, len(sorted_values) - 1)]
        except:
            aggregates["p95"] = aggregates["max"]
            aggregates["p99"] = aggregates["max"]
    
    # Calculate standard deviation if possible
    if len(values) >= 2:
        try:
            aggregates["stddev"] = statistics.stdev(values)
        except:
            aggregates["stddev"] = 0.0
    
    return aggregates

def downsample_series(series_data: Dict[str, Any], interval_seconds: int) -> List[Dict[str, Any]]:
    """
    Downsample a single time series to reduce data points while preserving trends.
    
    Args:
        series_data: Original series data with timestamps and values
        interval_seconds: Downsampling interval in seconds
        
    Returns:
        List of downsampled data points (one per time bucket)
    """
    timestamps = series_data["timestamps"]
    values = series_data["values"]
    
    if not timestamps or not values:
        return []
    
    # Create time buckets
    buckets = create_time_buckets(timestamps, values, interval_seconds)
    
    # Generate downsampled points (one per bucket using average)
    downsampled_points = []
    
    for bucket_start, bucket_data in sorted(buckets.items()):
        # Sort bucket data by timestamp
        bucket_data.sort(key=lambda x: x[0])
        
        # Calculate just the average for simplicity (this is the key fix!)
        values_in_bucket = [value for _, value in bucket_data]
        
        if values_in_bucket:
            avg_value = sum(values_in_bucket) / len(values_in_bucket)
            
            downsampled_points.append({
                "timestamp": bucket_start,
                "value": avg_value,
                "interval_seconds": interval_seconds,
                "original_count": len(bucket_data)
            })
    
    return downsampled_points

def downsample_dataset(original_data: List[Dict[str, Any]], intervals: List[int]) -> Dict[int, List[Dict[str, Any]]]:
    """
    Downsample the entire dataset at multiple intervals.
    
    Args:
        original_data: Original high-resolution data points
        intervals: List of downsampling intervals in seconds
        
    Returns:
        Dictionary mapping interval to list of downsampled data points
    """
    print(f"Downsampling dataset at {len(intervals)} different intervals...")
    
    # Group original data by series
    series_groups = defaultdict(list)
    for point in original_data:
        series_key = (point["metric_name"], tuple(sorted(point["labels"].items())))
        series_groups[series_key].append((point["timestamp"], point["value"]))
    
    # Sort each series by timestamp
    for series_key in series_groups:
        series_groups[series_key].sort(key=lambda x: x[0])
    
    downsampled_datasets = {}
    
    for interval in intervals:
        print(f"  Processing {interval}s interval...")
        downsampled_points = []
        
        for series_key, time_value_pairs in series_groups.items():
            metric_name, label_items = series_key
            labels = dict(label_items)
            
            # Extract timestamps and values
            timestamps = [tv[0] for tv in time_value_pairs]
            values = [tv[1] for tv in time_value_pairs]
            
            # Downsample this series
            series_data = {"timestamps": timestamps, "values": values}
            downsampled_series = downsample_series(series_data, interval)
            
            # Convert back to original format (much simpler now!)
            for ds_point in downsampled_series:
                full_point = {
                    "timestamp": ds_point["timestamp"],
                    "metric_name": metric_name,  # Keep original metric name
                    "value": ds_point["value"],
                    "labels": labels.copy(),
                    "aggregate_info": {
                        "original_metric": metric_name,
                        "aggregate_type": "avg",  # We're using average
                        "interval_seconds": interval,
                        "original_count": ds_point["original_count"]
                    }
                }
                downsampled_points.append(full_point)
        
        downsampled_datasets[interval] = downsampled_points
        print(f"    Generated {len(downsampled_points):,} aggregate data points")
    
    return downsampled_datasets

def analyze_downsampling_efficiency(original_data: List[Dict[str, Any]], downsampled_datasets: Dict[int, List[Dict[str, Any]]]) -> None:
    """Analyze the efficiency gains from downsampling."""
    print(f"\nDownsampling efficiency analysis:")
    
    original_count = len(original_data)
    print(f"  Original data points: {original_count:,}")
    
    for interval, ds_data in sorted(downsampled_datasets.items()):
        ds_count = len(ds_data)
        reduction_ratio = original_count / ds_count if ds_count > 0 else float('inf')
        reduction_percent = (1 - ds_count / original_count) * 100 if original_count > 0 else 0
        
        print(f"  {interval}s interval: {ds_count:,} points ({reduction_ratio:.1f}x reduction, {reduction_percent:.1f}% less data)")
        print(f"    Using average aggregation per time bucket")

def store_downsampled_data(downsampled_datasets: Dict[int, List[Dict[str, Any]]], output_dir: str) -> Dict[int, int]:
    """
    Store downsampled datasets using the compressed format from Phase 5.
    
    Args:
        downsampled_datasets: Dictionary of interval to downsampled data
        output_dir: Output directory for files
        
    Returns:
        Dictionary mapping interval to file size
    """
    print(f"\nStoring downsampled data using Phase 5 compression techniques...")
    print("(Building on columnar + specialized compression from previous phases)")
    
    # Import compression functions from Phase 5
    import sys
    from pathlib import Path
    lib_path = Path(__file__).parent / "lib"
    sys.path.insert(0, str(lib_path))
    from encoders import delta_encode_timestamps, xor_encode_floats, run_length_encode
    
    file_sizes = {}
    
    for interval, ds_data in downsampled_datasets.items():
        if not ds_data:
            continue
        
        print(f"  Processing {interval}s interval data...")
        
        # Convert to columnar format first
        series_metadata = {}
        series_data = defaultdict(lambda: {"timestamps": [], "values": []})
        series_id_map = {}
        next_series_id = 0
        
        for point in ds_data:
            # Create series key
            series_key = (point["metric_name"], tuple(sorted(point["labels"].items())))
            
            if series_key not in series_id_map:
                series_id = str(next_series_id)
                series_id_map[series_key] = series_id
                next_series_id += 1
                
                series_metadata[series_id] = {
                    "metric_name": point["metric_name"],
                    "labels": point["labels"]
                }
            
            series_id = series_id_map[series_key]
            series_data[series_id]["timestamps"].append(point["timestamp"])
            series_data[series_id]["values"].append(point["value"])
        
        # Now apply Phase 5 compression techniques to each series
        compressed_series_data = {}
        
        for series_id, data in series_data.items():
            timestamps = sorted(data["timestamps"])
            values = data["values"]
            
            # Apply timestamp compression (double-delta encoding)
            if len(timestamps) >= 2:
                base_ts, first_delta, deltas = delta_encode_timestamps(timestamps)
                compressed_timestamps = {
                    "base_timestamp": base_ts,
                    "first_delta": first_delta,
                    "deltas": run_length_encode(deltas)  # Further compress with RLE
                }
            else:
                compressed_timestamps = timestamps
            
            # Apply value compression (XOR encoding)
            if len(values) >= 2:
                base_value, encoded_values = xor_encode_floats(values)
                compressed_values = {
                    "base_value": base_value,
                    "encoded": run_length_encode(encoded_values)  # Further compress with RLE
                }
            else:
                compressed_values = values
            
            compressed_series_data[series_id] = {
                "timestamps": compressed_timestamps,
                "values": compressed_values
            }
        
        # Create final compressed structure (same as Phase 5)
        compressed_data = {
            "series_metadata": series_metadata,
            "series_data": compressed_series_data
        }
        
        # Store using MessagePack (same as Phase 5)
        output_file = os.path.join(output_dir, f"metrics.downsampled.{interval}s.zst")
        # Serialize and compress with zstd
        msgpack_data = msgpack.packb(compressed_data, use_bin_type=True)
        compressor = zstd.ZstdCompressor(level=3)
        compressed_msgpack = compressor.compress(msgpack_data)
        
        with open(output_file, "wb") as f:
            f.write(compressed_msgpack)
        
        file_size = len(compressed_msgpack)
        file_sizes[interval] = file_size
        
        print(f"    Stored {interval}s data: {file_size:,} bytes ({len(ds_data):,} points)")
    
    return file_sizes


def demonstrate_query_efficiency(original_data: List[Dict[str, Any]], downsampled_datasets: Dict[int, List[Dict[str, Any]]]) -> None:
    """Demonstrate how downsampling improves query efficiency."""
    print(f"\nQuery efficiency demonstration:")
    
    # Simulate a long-range query (e.g., "show CPU usage for last 6 hours")
    if not original_data:
        return
    
    # Find CPU metrics
    cpu_metrics = [p for p in original_data if "cpu" in p["metric_name"].lower()]
    if not cpu_metrics:
        print("  No CPU metrics found for demonstration")
        return
    
    # Get time range
    timestamps = [p["timestamp"] for p in cpu_metrics]
    time_span_hours = (max(timestamps) - min(timestamps)) / 3600
    
    print(f"  Original data span: {time_span_hours:.1f} hours")
    print(f"  Original CPU data points: {len(cpu_metrics):,}")
    
    # Show how many points we'd need to process for different intervals
    for interval in sorted(downsampled_datasets.keys()):
        ds_data = downsampled_datasets[interval]
        cpu_ds_metrics = [p for p in ds_data if "cpu" in p["metric_name"].lower() and "avg" in p["metric_name"]]
        
        if cpu_ds_metrics:
            reduction_ratio = len(cpu_metrics) / len(cpu_ds_metrics) if cpu_ds_metrics else float('inf')
            print(f"  {interval}s downsampled: {len(cpu_ds_metrics):,} points ({reduction_ratio:.1f}x fewer)")

def main():
    """Main function to execute Phase 7."""
    print("=" * 60)
    print("Phase 7: Downsampling + zstd for Long-term Storage")
    print("=" * 60)
    
    # Verify that Phase 6 exists (we build on its techniques)
    compressed_file = "output/metrics.compressed.zst"
    if not os.path.exists(compressed_file):
        print(f"❌ Error: {compressed_file} not found. Please run 05_compression_tricks.py first.")
        return
    
    # For simplicity of demonstration, we'll use the original data for downsampling
    # but apply Phase 5's compression techniques to the downsampled results
    print("Loading original dataset for downsampling (will apply Phase 6 compression to results)...")
    
    # Load original dataset for downsampling
    try:
        from lib.data_generator import load_dataset
        original_data = load_dataset()
        print(f"Loaded {len(original_data):,} data points for downsampling")
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return 1
    
    # Define downsampling intervals (in seconds)
    intervals = [60, 300, 900, 3600]  # 1min, 5min, 15min, 1hour
    
    print(f"Downsampling at intervals: {[f'{i}s' for i in intervals]}")
    
    # Perform downsampling
    downsampled_datasets = downsample_dataset(original_data, intervals)
    
    # Analyze efficiency
    analyze_downsampling_efficiency(original_data, downsampled_datasets)
    
    # Store downsampled data
    file_sizes = store_downsampled_data(downsampled_datasets, "output")
    
    # Demonstrate query efficiency
    demonstrate_query_efficiency(original_data, downsampled_datasets)
    
    # Compare with high-resolution compressed storage
    compressed_file = "output/metrics.compressed.zst"
    high_res_size = os.path.getsize(compressed_file) if os.path.exists(compressed_file) else None
    
    print(f"\n📊 Downsampling Storage Results:")
    total_downsampled_size = sum(file_sizes.values())
    print(f"  Total downsampled storage: {total_downsampled_size:,} bytes")
    print(f"  Uses Phase 6 compression techniques: specialized algorithms + zstd")
    
    if high_res_size:
        storage_ratio = high_res_size / total_downsampled_size if total_downsampled_size > 0 else float('inf')
        print(f"  vs High-resolution compressed (Phase 6): {storage_ratio:.2f}x more efficient")
        print(f"  Phase 6: {high_res_size:,} bytes vs Phase 7: {total_downsampled_size:,} bytes")
    
    print(f"\n  Individual interval files:")
    for interval, size in sorted(file_sizes.items()):
        points = len(downsampled_datasets[interval])
        bytes_per_point = size / points if points > 0 else 0
        print(f"    {interval}s: {size:,} bytes ({points:,} points, {bytes_per_point:.2f} bytes/point)")
    
    print(f"\n💡 Downsampling Characteristics:")
    print(f"  ✅ Pros:")
    print(f"    - Dramatic data reduction for long-term storage")
    print(f"    - Much faster queries over long time ranges")
    print(f"    - Multiple aggregates preserve different views")
    print(f"    - Essential for cost-effective retention")
    print(f"    - Enables hierarchical storage management")
    print(f"  ❌ Cons:")
    print(f"    - Lossy process - fine-grained details are lost")
    print(f"    - Need multiple aggregates to retain outlier visibility")
    print(f"    - Complex retention policy management")
    print(f"    - Cannot recover original high-resolution data")
    
    print(f"\n✅ Phase 7 completed successfully!")
    
    return {
        "format": "Downsampled (Multiple Intervals)",
        "file_size": total_downsampled_size,
        "compression_ratio": high_res_size / total_downsampled_size if high_res_size and total_downsampled_size > 0 else 1.0,
        "data_points": sum(len(ds_data) for ds_data in downsampled_datasets.values())
    }

if __name__ == "__main__":
    import time
    start_time = time.time()
    result = main()
    end_time = time.time()
    
    if result:
        print(f"\n✅ Phase 7 completed in {end_time - start_time:.2f} seconds")
    else:
        print(f"\n❌ Phase 7 failed after {end_time - start_time:.2f} seconds")