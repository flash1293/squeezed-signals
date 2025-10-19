#!/usr/bin/env python3
"""
Phase 5: Losing Precision for Longevity - Downsampling

This script demonstrates how to reduce data volume for long-term storage
by aggregating high-resolution data into lower-resolution "rollups".
"""

import os
import pickle
import statistics
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
    Downsample a single time series into multiple aggregated series.
    
    Args:
        series_data: Original series data with timestamps and values
        interval_seconds: Downsampling interval in seconds
        
    Returns:
        List of new downsampled data points
    """
    timestamps = series_data["timestamps"]
    values = series_data["values"]
    
    if not timestamps or not values:
        return []
    
    # Create time buckets
    buckets = create_time_buckets(timestamps, values, interval_seconds)
    
    # Generate downsampled points
    downsampled_points = []
    
    for bucket_start, bucket_data in sorted(buckets.items()):
        # Sort bucket data by timestamp
        bucket_data.sort(key=lambda x: x[0])
        
        # Calculate aggregates
        aggregates = calculate_aggregates(bucket_data)
        
        if aggregates:
            # Create data points for each aggregate
            for agg_name, agg_value in aggregates.items():
                downsampled_points.append({
                    "timestamp": bucket_start,
                    "aggregate": agg_name,
                    "value": agg_value,
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
            
            # Convert back to original format with additional aggregate info
            for ds_point in downsampled_series:
                full_point = {
                    "timestamp": ds_point["timestamp"],
                    "metric_name": f"{metric_name}_{ds_point['aggregate']}_{interval}s",
                    "value": ds_point["value"],
                    "labels": labels.copy(),
                    "aggregate_info": {
                        "original_metric": metric_name,
                        "aggregate_type": ds_point["aggregate"],
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
        
        # Analyze aggregate distribution
        agg_types = defaultdict(int)
        for point in ds_data[:1000]:  # Sample first 1000 points
            agg_type = point.get("aggregate_info", {}).get("aggregate_type", "unknown")
            agg_types[agg_type] += 1
        
        print(f"    Aggregate types: {dict(agg_types)}")

def store_downsampled_data(downsampled_datasets: Dict[int, List[Dict[str, Any]]], output_dir: str) -> Dict[int, int]:
    """
    Store downsampled datasets using the most efficient format from previous phases.
    
    Args:
        downsampled_datasets: Dictionary of interval to downsampled data
        output_dir: Output directory for files
        
    Returns:
        Dictionary mapping interval to file size
    """
    print(f"\nStoring downsampled data using efficient binary format...")
    
    file_sizes = {}
    
    for interval, ds_data in downsampled_datasets.items():
        if not ds_data:
            continue
        
        # Convert to columnar format (reuse logic from Phase 2)
        from lib.data_generator import print_data_stats
        
        print(f"  Processing {interval}s interval data...")
        
        # Create series dictionary
        series_metadata = {}
        series_data = defaultdict(lambda: {"timestamps": [], "values": []})
        series_id_map = {}
        next_series_id = 0
        
        for point in ds_data:
            # Create series key including aggregate info
            agg_info = point.get("aggregate_info", {})
            series_key = f"{point['metric_name']}{{{','.join(f'{k}={v}' for k, v in sorted(point['labels'].items()))}}}"
            
            if series_key not in series_id_map:
                series_id = str(next_series_id)
                series_id_map[series_key] = series_id
                series_metadata[series_id] = {
                    "name": point["metric_name"],
                    "labels": point["labels"].copy(),
                    "aggregate_info": agg_info
                }
                next_series_id += 1
            else:
                series_id = series_id_map[series_key]
            
            series_data[series_id]["timestamps"].append(point["timestamp"])
            series_data[series_id]["values"].append(point["value"])
        
        # Sort within each series
        for series_id, data in series_data.items():
            sorted_pairs = sorted(zip(data["timestamps"], data["values"]))
            data["timestamps"] = [ts for ts, _ in sorted_pairs]
            data["values"] = [val for _, val in sorted_pairs]
        
        # Create the structure
        downsampled_structure = {
            "series_metadata": series_metadata,
            "series_data": dict(series_data),
            "downsampling_info": {
                "interval_seconds": interval,
                "original_data_count": "unknown",
                "aggregates_included": list(set(
                    point.get("aggregate_info", {}).get("aggregate_type", "unknown") 
                    for point in ds_data[:100]  # Sample
                ))
            }
        }
        
        # Store as MessagePack
        output_file = os.path.join(output_dir, f"metrics.downsampled.{interval}s.msgpack")
        with open(output_file, "wb") as f:
            msgpack.dump(downsampled_structure, f, use_bin_type=True)
        
        file_size = os.path.getsize(output_file)
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
    """Main function to execute Phase 5."""
    print("=" * 60)
    print("Phase 5: Downsampling for Long-term Storage")
    print("=" * 60)
    
    # Load original dataset
    raw_data_file = "output/raw_dataset.pkl"
    if not os.path.exists(raw_data_file):
        print(f"❌ Error: {raw_data_file} not found. Please run 00_generate_data.py first.")
        return
    
    with open(raw_data_file, "rb") as f:
        original_data = pickle.load(f)
    
    print(f"Loaded original dataset: {len(original_data):,} data points")
    
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
    compressed_file = "output/metrics.compressed.msgpack"
    high_res_size = os.path.getsize(compressed_file) if os.path.exists(compressed_file) else None
    
    print(f"\n📊 Downsampling Storage Results:")
    total_downsampled_size = sum(file_sizes.values())
    print(f"  Total downsampled storage: {total_downsampled_size:,} bytes")
    
    if high_res_size:
        storage_ratio = high_res_size / total_downsampled_size if total_downsampled_size > 0 else float('inf')
        print(f"  vs High-resolution compressed: {storage_ratio:.2f}x more efficient")
        print(f"  High-res: {high_res_size:,} bytes vs Downsampled: {total_downsampled_size:,} bytes")
    
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
    
    print(f"\n✅ Phase 5 completed successfully!")
    
    return {
        "format": "Downsampled (Multiple Intervals)",
        "file_size": total_downsampled_size,
        "compression_ratio": high_res_size / total_downsampled_size if high_res_size and total_downsampled_size > 0 else 1.0,
        "data_points": sum(len(ds_data) for ds_data in downsampled_datasets.values())
    }

if __name__ == "__main__":
    main()