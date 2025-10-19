"""
Real dataset generator using the westermo/test-system-performance-dataset.

This module downloads and processes real performance monitoring data from:
https://github.com/westermo/test-system-performance-dataset
"""

import os
import subprocess
import pandas as pd
import numpy as np
import time
import random
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime, timezone

def ensure_dataset_downloaded():
    """Download the test-system-performance-dataset if not already present."""
    dataset_dir = Path("test-system-performance-dataset")
    
    if dataset_dir.exists():
        print(f"✅ Dataset repository already exists at: {dataset_dir}")
        return dataset_dir
    
    print("📥 Downloading test-system-performance-dataset...")
    try:
        subprocess.run([
            "git", "clone", 
            "https://github.com/westermo/test-system-performance-dataset.git"
        ], check=True, capture_output=True, text=True)
        print(f"✅ Successfully cloned dataset to: {dataset_dir}")
        return dataset_dir
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to clone dataset: {e.stderr}")

def discover_csv_files(dataset_dir: Path) -> List[Path]:
    """Discover all CSV files in the dataset directory."""
    csv_files = list(dataset_dir.rglob("*.csv"))
    print(f"🔍 Found {len(csv_files)} CSV files in dataset")
    
    # Print some examples
    for i, csv_file in enumerate(csv_files[:5]):
        relative_path = csv_file.relative_to(dataset_dir)
        file_size = csv_file.stat().st_size
        print(f"  {i+1}. {relative_path} ({file_size:,} bytes)")
    
    if len(csv_files) > 5:
        print(f"  ... and {len(csv_files) - 5} more files")
    
    return csv_files

def parse_csv_file(csv_path: Path) -> pd.DataFrame:
    """Parse a single CSV file from the performance dataset."""
    try:
        # Try different common CSV formats
        df = pd.read_csv(csv_path)
        
        # Standardize column names (common patterns in monitoring data)
        if 'timestamp' in df.columns:
            timestamp_col = 'timestamp'
        elif 'time' in df.columns:
            timestamp_col = 'time'
        elif 'date' in df.columns:
            timestamp_col = 'date'
        else:
            # Use first column as timestamp if no obvious timestamp column
            timestamp_col = df.columns[0]
        
        # Convert timestamp to Unix timestamp
        try:
            if timestamp_col == 'timestamp' and df[timestamp_col].dtype in ['int64', 'float64']:
                # This is likely "seconds since first data was collected" format
                # Convert to Unix timestamps by adding to a base time
                base_time = int(time.time()) - df[timestamp_col].max()  # Start time
                df['unix_timestamp'] = df[timestamp_col] + base_time
            else:
                # Try to parse as datetime
                df['unix_timestamp'] = pd.to_datetime(df[timestamp_col]).astype('int64') // 10**9
        except:
            # If timestamp parsing fails, generate sequential timestamps
            start_time = int(time.time()) - len(df) * 15  # 15 second intervals going backwards
            df['unix_timestamp'] = range(start_time, start_time + len(df) * 15, 15)
        
        return df
        
    except Exception as e:
        print(f"⚠️  Failed to parse {csv_path}: {e}")
        return None

def extract_metrics_from_dataframe(df: pd.DataFrame, csv_path: Path) -> List[Dict[str, Any]]:
    """Extract metric data points from a parsed DataFrame."""
    if df is None or len(df) == 0:
        return []
    
    data_points = []
    
    # Generate labels from file path
    path_parts = csv_path.parts
    host_name = "unknown"
    environment = "prod"
    
    # Try to extract meaningful labels from path
    for part in path_parts:
        if 'node' in part.lower() or 'server' in part.lower() or 'host' in part.lower():
            host_name = part
        elif 'test' in part.lower():
            environment = "test"
        elif 'dev' in part.lower():
            environment = "dev"
    
    # Extract region from path or generate one
    region_candidates = ["us-east-1", "eu-west-1", "ap-southeast-1", "us-west-2"]
    region = random.choice(region_candidates)
    
    # Process each numeric column as a separate metric
    for column in df.columns:
        if column == 'unix_timestamp':
            continue
            
        # Skip non-numeric columns
        if not pd.api.types.is_numeric_dtype(df[column]):
            continue
        
        # Clean up metric name
        metric_name = column.lower()
        metric_name = metric_name.replace(' ', '_').replace('-', '_')
        metric_name = ''.join(c for c in metric_name if c.isalnum() or c == '_')
        
        # Add appropriate suffix based on metric type
        if 'cpu' in metric_name and 'percent' not in metric_name:
            metric_name += '_percent'
        elif 'memory' in metric_name and 'percent' not in metric_name and 'bytes' not in metric_name:
            metric_name += '_percent'
        elif 'disk' in metric_name and 'bytes' not in metric_name:
            metric_name += '_bytes'
        elif 'network' in metric_name and 'bytes' not in metric_name:
            metric_name += '_bytes'
        elif ('time' in metric_name or 'latency' in metric_name) and 'ms' not in metric_name:
            metric_name += '_ms'
        elif 'count' in metric_name or 'total' in metric_name:
            if 'total' not in metric_name:
                metric_name += '_total'
        
        # Create data points for this metric
        for _, row in df.iterrows():
            if pd.isna(row[column]):
                continue
                
            value = float(row[column])
            
            # Skip invalid values
            if not np.isfinite(value):
                continue
            
            data_point = {
                "timestamp": int(row['unix_timestamp']),
                "metric_name": metric_name,
                "value": value,
                "labels": {
                    "host": host_name,
                    "region": region,
                    "environment": environment,
                    "source": "real_dataset"
                }
            }
            
            data_points.append(data_point)
    
    return data_points

def generate_real_metric_data(
    dataset_size: str = "small",
    max_files: int = None
) -> List[Dict[str, Any]]:
    """
    Generate time-series data from real performance monitoring dataset.
    
    Args:
        dataset_size: "small" (50k points) or "big" (500k points)
        max_files: Maximum number of CSV files to process (None for all)
        
    Returns:
        List of data point dictionaries from real monitoring data
    """
    
    # Set target data point counts
    if dataset_size == "small":
        target_points = 50000
        max_files = max_files or 10
    elif dataset_size == "big":
        target_points = 500000
        max_files = max_files or 50
    else:
        raise ValueError("dataset_size must be 'small' or 'big'")
    
    print(f"🎯 Target: ~{target_points:,} data points from real monitoring data")
    
    # Download dataset if needed
    dataset_dir = ensure_dataset_downloaded()
    
    # Find CSV files
    csv_files = discover_csv_files(dataset_dir)
    
    if not csv_files:
        raise RuntimeError("No CSV files found in dataset")
    
    # Randomly sample files if we have too many
    if len(csv_files) > max_files:
        csv_files = random.sample(csv_files, max_files)
        print(f"📊 Randomly selected {max_files} files for processing")
    
    all_data_points = []
    processed_files = 0
    
    for csv_file in csv_files:
        if len(all_data_points) >= target_points:
            break
            
        print(f"📁 Processing: {csv_file.relative_to(dataset_dir)}")
        
        # Parse CSV file
        df = parse_csv_file(csv_file)
        if df is None:
            continue
        
        # Extract metrics
        file_data_points = extract_metrics_from_dataframe(df, csv_file)
        
        if file_data_points:
            all_data_points.extend(file_data_points)
            processed_files += 1
            print(f"  ✅ Extracted {len(file_data_points):,} data points")
        else:
            print(f"  ⚠️  No usable data points found")
    
    # Trim to target size if we have too many points
    if len(all_data_points) > target_points:
        all_data_points = random.sample(all_data_points, target_points)
        print(f"✂️  Trimmed to target size: {len(all_data_points):,} points")
    
    # Sort by timestamp for consistency
    all_data_points.sort(key=lambda x: x['timestamp'])
    
    print(f"📊 Final dataset: {len(all_data_points):,} points from {processed_files} files")
    
    return all_data_points

def print_real_data_stats(data_points: List[Dict[str, Any]]):
    """Print statistics about the real dataset."""
    if not data_points:
        print("No data points to analyze")
        return
    
    print("\n" + "=" * 50)
    print("REAL DATASET STATISTICS")
    print("=" * 50)
    
    # Basic counts
    total_points = len(data_points)
    print(f"Total data points: {total_points:,}")
    
    # Unique metrics
    unique_metrics = set(point['metric_name'] for point in data_points)
    print(f"Unique metrics: {len(unique_metrics)}")
    print("Metric types:")
    for metric in sorted(unique_metrics):
        count = sum(1 for p in data_points if p['metric_name'] == metric)
        print(f"  {metric}: {count:,} points")
    
    # Time range
    timestamps = [point['timestamp'] for point in data_points]
    time_range = max(timestamps) - min(timestamps)
    hours = time_range / 3600
    print(f"Time range: {hours:.1f} hours")
    
    # Unique series (metric + labels combination)
    unique_series = set()
    for point in data_points:
        series_key = (point['metric_name'], tuple(sorted(point['labels'].items())))
        unique_series.add(series_key)
    
    print(f"Unique time series: {len(unique_series):,}")
    
    # Host and region distribution
    hosts = set(point['labels'].get('host', 'unknown') for point in data_points)
    regions = set(point['labels'].get('region', 'unknown') for point in data_points)
    environments = set(point['labels'].get('environment', 'unknown') for point in data_points)
    
    print(f"Unique hosts: {len(hosts)} ({', '.join(sorted(hosts)[:5])}{'...' if len(hosts) > 5 else ''})")
    print(f"Unique regions: {len(regions)} ({', '.join(sorted(regions))})")
    print(f"Unique environments: {len(environments)} ({', '.join(sorted(environments))})")
    
    # Value statistics
    values = [point['value'] for point in data_points]
    print(f"Value range: {min(values):.2f} to {max(values):.2f}")
    
    print("=" * 50)