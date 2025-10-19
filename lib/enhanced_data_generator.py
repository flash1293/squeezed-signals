"""
Enhanced data generator with more regularity for better compression.

This module generates realistic time-series data with patterns that are common
in real monitoring systems and provide better compression ratios.
"""

import random
import time
import math
from typing import List, Dict, Any

def generate_enhanced_metric_data(
    num_series: int = 50,      # Will be overridden by dataset_size parameter
    num_points_per_series: int = 1000,  # Will be overridden by dataset_size parameter
    base_interval: int = 15,   # seconds
    jitter_range: int = 2,     # Reduced jitter for more regular timestamps
    dataset_size: str = "small",  # "small" or "big"
    regularity_level: str = "medium"  # "low", "medium", "high"
) -> List[Dict[str, Any]]:
    """
    Generate enhanced time-series metric data with better compression characteristics.
    
    Args:
        num_series: Number of unique time series (overridden by dataset_size)
        num_points_per_series: Number of data points per series (overridden by dataset_size)
        base_interval: Base scrape interval in seconds
        jitter_range: Random jitter range in seconds (reduced for regularity)
        dataset_size: "small" (50 series x 1k points) or "big" (500 series x 10k points)
        regularity_level: "low", "medium", "high" - how much regularity to inject
        
    Returns:
        List of data point dictionaries with enhanced patterns
    """
    
    # Override parameters based on dataset size
    if dataset_size == "small":
        num_series = 50
        num_points_per_series = 1000
    elif dataset_size == "big":
        num_series = 500
        num_points_per_series = 10000
    else:
        raise ValueError("dataset_size must be 'small' or 'big'")
    
    # Adjust regularity based on level
    if regularity_level == "low":
        jitter_factor = 1.0
        precision_factor = 1.0
        stability_factor = 1.0
    elif regularity_level == "medium":
        jitter_factor = 0.5  # Reduce timestamp jitter
        precision_factor = 0.7  # More value rounding
        stability_factor = 0.8  # More stable patterns
    elif regularity_level == "high":
        jitter_factor = 0.2  # Very regular timestamps
        precision_factor = 0.4  # Heavy value rounding
        stability_factor = 0.5  # Very stable patterns
    else:
        raise ValueError("regularity_level must be 'low', 'medium', or 'high'")
    
    # Adjust jitter based on regularity level
    jitter_range = max(1, int(jitter_range * jitter_factor))
    
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
    
    # Create infrastructure correlation patterns
    # Services on same host/region tend to have similar load patterns
    infrastructure_patterns = {}
    for host in hosts:
        for region in regions:
            # Each host+region combination gets a shared load pattern
            pattern_id = f"{host}-{region}"
            infrastructure_patterns[pattern_id] = {
                "load_phase": random.uniform(0, 2 * math.pi),  # Phase offset for daily cycle
                "load_amplitude": random.uniform(0.2, 0.8),    # How much daily variation
                "stability": random.uniform(0.3, 0.9),         # How stable the service is
            }
    
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
        
        # Attach infrastructure pattern
        pattern_key = f"{labels['host']}-{labels['region']}"
        series_definitions.append({
            "name": metric_name,
            "labels": labels,
            "pattern": infrastructure_patterns[pattern_key]
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
        pattern = series["pattern"]
        
        # Initialize series-specific parameters with enhanced regularity
        base_rate = None
        trend_rate = 0
        volatility = 1.0
        rate_volatility = 0.1
        
        if "cpu" in series["name"] or "memory" in series["name"]:
            # Percentage metrics: more stable patterns with platform correlation
            base_value = random.uniform(25, 75)  # Narrower range for more similarity
            trend_rate = random.uniform(-0.0005, 0.0005) * stability_factor
            volatility = random.uniform(0.3, 1.5) * stability_factor
            
            # Enhanced daily pattern with infrastructure correlation
            seasonal_amplitude = random.uniform(8, 20) * pattern["load_amplitude"]
            seasonal_frequency = 1.0 / (24 * 60 * 60 / base_interval)  # Daily cycle
            seasonal_phase = pattern["load_phase"]
            
            min_bound, max_bound = 0, 100
        elif "duration" in series["name"] or "response_time" in series["name"]:
            # Latency metrics: more predictable with shared infrastructure patterns
            base_value = random.uniform(15, 80)
            trend_rate = random.uniform(-0.0002, 0.0002) * stability_factor
            volatility = random.uniform(0.8, 3.0) * stability_factor
            
            # Service latency follows infrastructure load
            seasonal_amplitude = random.uniform(10, 30) * pattern["load_amplitude"]
            seasonal_frequency = 1.0 / (24 * 60 * 60 / base_interval)
            seasonal_phase = pattern["load_phase"]
            
            min_bound, max_bound = 1, 5000
        elif "total" in series["name"] or "count" in series["name"]:
            # Counter metrics: smoother rate changes
            base_value = random.randint(1000, 10000)
            base_rate = random.uniform(0.2, 1.5)
            rate_volatility = random.uniform(0.005, 0.08) * stability_factor
            
            # Request volume follows daily patterns
            seasonal_amplitude = random.uniform(0.2, 0.8) * pattern["load_amplitude"]
            seasonal_frequency = 1.0 / (24 * 60 * 60 / base_interval)
            seasonal_phase = pattern["load_phase"]
            
            min_bound, max_bound = base_value, float('inf')
        elif "error_rate" in series["name"]:
            # Error rates: mostly very stable with correlated incidents
            base_value = random.uniform(0.05, 1.5)  # Lower and more stable
            trend_rate = random.uniform(-0.00005, 0.00005) * stability_factor
            volatility = random.uniform(0.02, 0.15) * stability_factor
            
            # Error spikes correlate with load
            seasonal_amplitude = random.uniform(0.1, 2.0) * pattern["load_amplitude"]
            seasonal_frequency = 1.0 / (24 * 60 * 60 / base_interval)
            seasonal_phase = pattern["load_phase"] + random.uniform(0, math.pi/4)
            
            min_bound, max_bound = 0, 25
        else:
            # Generic metrics: more stable
            base_value = random.uniform(20, 80)
            trend_rate = random.uniform(-0.0005, 0.0005) * stability_factor
            volatility = random.uniform(0.4, 2.0) * stability_factor
            
            seasonal_amplitude = random.uniform(8, 20) * pattern["load_amplitude"]
            seasonal_frequency = 1.0 / (24 * 60 * 60 / base_interval)
            seasonal_phase = pattern["load_phase"]
            
            min_bound, max_bound = 0, 500
        
        current_timestamp = base_timestamp
        current_value = base_value
        current_rate = base_rate if "total" in series["name"] or "count" in series["name"] else None
        
        # Enhanced timestamp generation with better regularity
        timestamps = []
        for i in range(num_points_per_series):
            if i == 0:
                timestamp = current_timestamp
            else:
                # More regular intervals with occasional jitter
                if random.random() < 0.8 * (2.0 - stability_factor):  # 80% regular for medium stability
                    timestamp = current_timestamp + base_interval
                else:
                    timestamp_jitter = random.randint(-jitter_range, jitter_range)
                    timestamp = current_timestamp + base_interval + timestamp_jitter
            
            timestamps.append(timestamp)
            current_timestamp = timestamp
        
        # Value generation with enhanced patterns
        for i, timestamp in enumerate(timestamps):
            # Time-based seasonal component
            time_progress = i / num_points_per_series
            seasonal_component = seasonal_amplitude * math.sin(
                seasonal_frequency * i * 2 * math.pi + seasonal_phase
            )
            
            if "total" in series["name"] or "count" in series["name"]:
                # Monotonically increasing counter with smoother rate changes
                rate_noise = random.gauss(0, rate_volatility)
                current_rate = max(0.01, current_rate + rate_noise + seasonal_component * 0.02)
                increment = max(0, current_rate + random.gauss(0, volatility * 0.05))
                current_value += increment
                value = current_value
            else:
                # Enhanced value generation with platform stability
                trend_component = trend_rate * i
                random_walk_step = random.gauss(0, volatility)
                
                # Platform stability effect - reduce randomness
                stability_damping = pattern["stability"]
                random_walk_step *= (1.0 - stability_damping * 0.5)
                
                # Update current value with temporal correlation
                current_value += (trend_component + random_walk_step + seasonal_component * 0.15)
                
                # Apply bounds with soft constraint
                if current_value < min_bound:
                    current_value = min_bound + abs(random.gauss(0, volatility * 0.5))
                elif current_value > max_bound:
                    current_value = max_bound - abs(random.gauss(0, volatility * 0.5))
                
                value = current_value
                
                # Enhanced value quantization based on precision factor
                if "percent" in series["name"]:
                    # Round percentages to realistic precision
                    decimal_places = max(0, int(2 * precision_factor))
                    value = round(max(0, min(100, value)), decimal_places)
                elif "duration" in series["name"] or "response_time" in series["name"]:
                    # Round latencies to realistic precision (milliseconds)
                    if value < 10:
                        value = round(value, 2)  # Sub-10ms: 2 decimal places
                    elif value < 100:
                        value = round(value, 1)  # 10-100ms: 1 decimal place
                    else:
                        value = round(value)     # >100ms: whole numbers
                elif "active_connections" in series["name"] or "queue_size" in series["name"]:
                    value = max(0, int(round(value)))
                else:
                    # Generic rounding based on precision factor
                    if precision_factor < 0.5:
                        # High precision - round to fewer decimal places
                        if value < 1:
                            value = round(value, 3)
                        elif value < 10:
                            value = round(value, 2)
                        elif value < 100:
                            value = round(value, 1)
                        else:
                            value = round(value)
                    else:
                        # Lower precision - keep more decimals
                        value = round(value, 2)
            
            data_point = {
                "timestamp": timestamp,
                "metric_name": series["name"],
                "value": value,
                "labels": series["labels"].copy()
            }
            
            data_points.append(data_point)
    
    # Sort by timestamp to simulate realistic ingestion order
    data_points.sort(key=lambda x: x["timestamp"])
    
    return data_points

def generate_metric_data(*args, **kwargs):
    """
    Wrapper function that calls the enhanced generator.
    Maintains compatibility with existing code.
    """
    # Extract regularity level if provided, otherwise use medium
    regularity_level = kwargs.pop('regularity_level', 'medium')
    
    # Call enhanced generator
    return generate_enhanced_metric_data(*args, regularity_level=regularity_level, **kwargs)

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
    
    # Analyze timestamp regularity
    intervals = []
    for i in range(1, len(data_points)):
        if data_points[i]["metric_name"] == data_points[i-1]["metric_name"]:
            interval = data_points[i]["timestamp"] - data_points[i-1]["timestamp"]
            intervals.append(interval)
    
    regular_intervals = sum(1 for interval in intervals if interval == 15)  # Assuming 15s base interval
    regularity_pct = (regular_intervals / len(intervals) * 100) if intervals else 0
    
    # Analyze value precision
    rounded_values = 0
    total_values = 0
    for point in data_points:
        if isinstance(point["value"], float):
            total_values += 1
            # Check if value appears to be rounded (limited decimal places)
            str_val = str(point["value"])
            if '.' in str_val:
                decimal_places = len(str_val.split('.')[1])
                if decimal_places <= 2:  # 2 or fewer decimal places suggests rounding
                    rounded_values += 1
            else:
                rounded_values += 1  # Integer values are "rounded"
    
    precision_pct = (rounded_values / total_values * 100) if total_values else 0
    
    print(f"Generated enhanced dataset statistics:")
    print(f"  Total data points: {len(data_points):,}")
    print(f"  Unique time series: {len(unique_series):,}")
    print(f"  Time range: {time_range_hours:.1f} hours")
    print(f"  Avg points per series: {len(data_points) / len(unique_series):.1f}")
    print(f"  Timestamp regularity: {regularity_pct:.1f}% exact intervals")
    print(f"  Value precision: {precision_pct:.1f}% appear rounded/quantized")
    
    # Sample data point
    print(f"\nSample data point:")
    sample = data_points[len(data_points) // 2]
    print(f"  Timestamp: {sample['timestamp']}")
    print(f"  Metric: {sample['metric_name']}")
    print(f"  Value: {sample['value']}")
    print(f"  Labels: {sample['labels']}")

def load_dataset():
    """Load the generated dataset from the output directory."""
    import pickle
    from pathlib import Path
    
    dataset_file = Path("output/raw_dataset.pkl")
    if not dataset_file.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_file}. Please run 00_generate_data.py first.")
    
    with open(dataset_file, 'rb') as f:
        data_points = pickle.load(f)
    
    return data_points