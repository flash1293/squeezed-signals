"""
Data generator for time-series metrics storage engine demo.

This module generates realistic, yet compressible, time-series data
that mimics typical observability metrics.
"""

import random
import time
import math
from typing import List, Dict, Any

def generate_metric_data(
    num_series: int = 50,
    num_points_per_series: int = 1000,
    base_interval: int = 15,  # seconds
    jitter_range: int = 5     # seconds
) -> List[Dict[str, Any]]:
    """
    Generate time-series metric data points.
    
    Args:
        num_series: Number of unique time series to generate
        num_points_per_series: Number of data points per series
        base_interval: Base scrape interval in seconds
        jitter_range: Random jitter range in seconds
        
    Returns:
        List of data point dictionaries
    """
    
    # Define metric names and possible label values
    metric_names = [
        "cpu_usage_percent",
        "memory_usage_percent", 
        "http_requests_total",
        "http_request_duration_seconds",
        "disk_io_bytes_total",
        "network_bytes_total",
        "active_connections",
        "queue_size",
        "error_rate_percent",
        "response_time_ms"
    ]
    
    hosts = ["server-a", "server-b", "server-c", "server-d", "server-e"]
    regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]
    environments = ["prod", "staging", "dev"]
    status_codes = ["200", "404", "500", "503"]
    
    # Generate unique time series (metric + labels combinations)
    series_definitions = []
    for _ in range(num_series):
        metric_name = random.choice(metric_names)
        labels = {
            "host": random.choice(hosts),
            "region": random.choice(regions),
            "environment": random.choice(environments)
        }
        
        # Add metric-specific labels
        if "http" in metric_name:
            labels["status_code"] = random.choice(status_codes)
            labels["method"] = random.choice(["GET", "POST", "PUT", "DELETE"])
        elif "disk" in metric_name or "network" in metric_name:
            labels["device"] = random.choice(["eth0", "eth1", "sda", "sdb"])
        
        series_definitions.append({
            "name": metric_name,
            "labels": labels
        })
    
    # Remove duplicates by converting to a set of (name, sorted_labels) tuples
    unique_series = []
    seen = set()
    for series in series_definitions:
        key = (series["name"], tuple(sorted(series["labels"].items())))
        if key not in seen:
            seen.add(key)
            unique_series.append(series)
    
    series_definitions = unique_series[:num_series]
    
    # Generate data points for each series
    data_points = []
    base_timestamp = int(time.time()) - (num_points_per_series * base_interval)
    
    for series in series_definitions:
        # Initialize series-specific parameters for realistic data generation
        if "cpu" in series["name"] or "memory" in series["name"]:
            # Percentage metrics: oscillate between reasonable values
            base_value = random.uniform(20, 80)
            amplitude = random.uniform(5, 15)
            frequency = random.uniform(0.001, 0.01)
            noise_level = 2.0
        elif "duration" in series["name"] or "response_time" in series["name"]:
            # Latency metrics: mostly low with occasional spikes
            base_value = random.uniform(10, 100)  # milliseconds
            amplitude = random.uniform(5, 20)
            frequency = random.uniform(0.005, 0.02)
            noise_level = 5.0
        elif "total" in series["name"] or "count" in series["name"]:
            # Counter metrics: monotonically increasing
            base_value = random.randint(1000, 10000)
            increment_rate = random.uniform(0.1, 2.0)
            noise_level = 0.1
        elif "error_rate" in series["name"]:
            # Error rates: mostly low, occasional spikes
            base_value = random.uniform(0.1, 2.0)
            amplitude = random.uniform(0.5, 3.0)
            frequency = random.uniform(0.001, 0.005)
            noise_level = 0.2
        else:
            # Generic metrics
            base_value = random.uniform(10, 100)
            amplitude = random.uniform(5, 25)
            frequency = random.uniform(0.001, 0.01)
            noise_level = 3.0
        
        current_timestamp = base_timestamp
        current_value = base_value
        
        for i in range(num_points_per_series):
            # Add timestamp jitter to simulate real-world scraping
            timestamp_jitter = random.randint(-jitter_range, jitter_range)
            timestamp = current_timestamp + timestamp_jitter
            
            # Generate realistic values based on metric type
            if "total" in series["name"] or "count" in series["name"]:
                # Monotonically increasing counter
                current_value += max(0, increment_rate + random.gauss(0, noise_level))
                value = current_value
            else:
                # Oscillating value with noise
                sine_component = amplitude * math.sin(frequency * i * 2 * math.pi)
                noise = random.gauss(0, noise_level)
                value = max(0, base_value + sine_component + noise)
                
                # Ensure percentages stay within bounds
                if "percent" in series["name"]:
                    value = max(0, min(100, value))
            
            data_point = {
                "timestamp": timestamp,
                "metric_name": series["name"],
                "value": value,
                "labels": series["labels"].copy()
            }
            
            data_points.append(data_point)
            current_timestamp += base_interval
    
    # Sort by timestamp to simulate realistic ingestion order
    data_points.sort(key=lambda x: x["timestamp"])
    
    return data_points

def print_data_stats(data_points: List[Dict[str, Any]]) -> None:
    """Print statistics about the generated dataset."""
    if not data_points:
        print("No data points generated")
        return
    
    # Count unique series
    unique_series = set()
    for point in data_points:
        series_key = (point["metric_name"], tuple(sorted(point["labels"].items())))
        unique_series.add(series_key)
    
    # Time range
    timestamps = [point["timestamp"] for point in data_points]
    time_range_hours = (max(timestamps) - min(timestamps)) / 3600
    
    print(f"Generated dataset statistics:")
    print(f"  Total data points: {len(data_points):,}")
    print(f"  Unique time series: {len(unique_series):,}")
    print(f"  Time range: {time_range_hours:.1f} hours")
    print(f"  Avg points per series: {len(data_points) / len(unique_series):.1f}")
    
    # Sample data point
    print(f"\nSample data point:")
    sample = data_points[len(data_points) // 2]
    print(f"  Timestamp: {sample['timestamp']}")
    print(f"  Metric: {sample['metric_name']}")
    print(f"  Value: {sample['value']:.2f}")
    print(f"  Labels: {sample['labels']}")