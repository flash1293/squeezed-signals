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
    num_series: int = 500,     # Increased from 50 to 500
    num_points_per_series: int = 10000,  # Increased from 1000 to 10000  
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
        base_rate = None  # Initialize for counter metrics
        trend_rate = 0    # Initialize for non-counter metrics
        volatility = 1.0  # Initialize for all metrics
        rate_volatility = 0.1  # Initialize for counter metrics
        
        if "cpu" in series["name"] or "memory" in series["name"]:
            # Percentage metrics: random walk with bounds
            base_value = random.uniform(20, 80)
            trend_rate = random.uniform(-0.001, 0.001)  # Very slow trend
            volatility = random.uniform(0.5, 2.0)  # Random walk step size
            seasonal_amplitude = random.uniform(5, 15)
            seasonal_frequency = random.uniform(0.001, 0.01)
            min_bound, max_bound = 0, 100
        elif "duration" in series["name"] or "response_time" in series["name"]:
            # Latency metrics: random walk with occasional spikes
            base_value = random.uniform(10, 100)
            trend_rate = random.uniform(-0.0005, 0.0005)
            volatility = random.uniform(1.0, 5.0)
            seasonal_amplitude = random.uniform(5, 20)
            seasonal_frequency = random.uniform(0.005, 0.02)
            min_bound, max_bound = 1, 10000  # Latency can spike high
        elif "total" in series["name"] or "count" in series["name"]:
            # Counter metrics: monotonically increasing with random walk in rate
            base_value = random.randint(1000, 10000)
            base_rate = random.uniform(0.1, 2.0)  # Base increment rate
            rate_volatility = random.uniform(0.01, 0.1)  # How much rate varies
            seasonal_amplitude = random.uniform(0.1, 0.5)
            seasonal_frequency = random.uniform(0.001, 0.005)
            min_bound, max_bound = base_value, float('inf')
        elif "error_rate" in series["name"]:
            # Error rates: mostly low with correlated spikes
            base_value = random.uniform(0.1, 2.0)
            trend_rate = random.uniform(-0.0001, 0.0001)
            volatility = random.uniform(0.05, 0.2)
            seasonal_amplitude = random.uniform(0.5, 3.0)
            seasonal_frequency = random.uniform(0.001, 0.005)
            min_bound, max_bound = 0, 50  # Error rates can spike
        else:
            # Generic metrics: random walk
            base_value = random.uniform(10, 100)
            trend_rate = random.uniform(-0.001, 0.001)
            volatility = random.uniform(0.5, 3.0)
            seasonal_amplitude = random.uniform(5, 25)
            seasonal_frequency = random.uniform(0.001, 0.01)
            min_bound, max_bound = 0, 1000
        
        current_timestamp = base_timestamp
        current_value = base_value
        current_rate = base_rate if "total" in series["name"] or "count" in series["name"] else None
        
        for i in range(num_points_per_series):
            # Add timestamp jitter to simulate real-world scraping
            timestamp_jitter = random.randint(-jitter_range, jitter_range)
            timestamp = current_timestamp + timestamp_jitter
            
            # Generate realistic values with temporal correlation
            if "total" in series["name"] or "count" in series["name"]:
                # Monotonically increasing counter with varying rate
                seasonal_effect = seasonal_amplitude * math.sin(seasonal_frequency * i * 2 * math.pi)
                rate_noise = random.gauss(0, rate_volatility)
                current_rate = max(0.01, current_rate + rate_noise + seasonal_effect * 0.1)
                increment = max(0, current_rate + random.gauss(0, volatility * 0.1))
                current_value += increment
                value = current_value
            else:
                # Random walk with trend, seasonality, and bounds
                seasonal_component = seasonal_amplitude * math.sin(seasonal_frequency * i * 2 * math.pi)
                trend_component = trend_rate * i
                random_walk_step = random.gauss(0, volatility)
                
                # Update current value with temporal correlation
                current_value += trend_component + random_walk_step + seasonal_component * 0.1
                
                # Apply bounds with soft constraint (allows temporary excursions)
                if current_value < min_bound:
                    current_value = min_bound + abs(random.gauss(0, volatility))
                elif current_value > max_bound:
                    current_value = max_bound - abs(random.gauss(0, volatility))
                
                value = current_value
                
                # Ensure percentages stay within bounds more strictly
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