# Data Generation Deep Dive

## Overview

The metrics storage demonstration supports **two data generation modes** to test compression algorithms against different types of time-series data:

1. **Synthetic Data Generator** (default) - Enhanced patterns for optimal compression
2. **Real Data Generator** - Actual production monitoring data

Both generators produce the same data structure and can be tested at three scales: `small` (~50K points), `big` (~500K points), and `huge` (~100M points).

## Usage

```bash
# Use synthetic data (default)
python main.py --size small

# Use real monitoring data
DATA_GENERATOR=real python main.py --size small
```

The system automatically caches generated datasets, so subsequent runs with the same configuration are instant.

## 1. Synthetic Data Generator (Default)

**Purpose**: Generate realistic time-series metrics with patterns that mirror production monitoring systems while demonstrating excellent compression characteristics.

### Key Features

- **Infrastructure Correlation**: Services on the same host/region share load patterns
- **Temporal Regularity**: 80%+ of timestamps are perfectly regular (15s intervals)
- **Value Quantization**: Realistic precision levels based on metric type
- **Platform Stability**: Reduced randomness to model well-managed infrastructure

### Generated Patterns

**Metric Types**:
- CPU/Memory usage (0-100% with 1-2 decimal precision)
- HTTP requests (monotonic counters with realistic rate changes)
- Response times (correlated with load, appropriate precision)
- Network/Disk I/O (counter-based with infrastructure correlation)
- Connection counts and queue sizes (integer values, bounded ranges)

**Implementation Details**:
```python
# Infrastructure correlation
infrastructure_patterns = {
    f"{host}-{region}": {
        "load_phase": random.uniform(0, 2 * math.pi),
        "load_amplitude": random.uniform(0.2, 0.8),
        "stability": random.uniform(0.3, 0.9),
    }
}

# Timestamp regularity (80% perfect intervals)
if random.random() < 0.8:
    timestamp = current_timestamp + base_interval
else:
    timestamp = current_timestamp + base_interval + random_jitter

# Value quantization by metric type
if "percent" in metric_name:
    value = round(value, 1)  # 1 decimal place
elif "duration" in metric_name:
    value = round(value, 2) if value < 10 else round(value, 1)
```

### Compression Benefits

- **94.6% zero timestamp deltas** → 43.75x timestamp compression
- **Quantized value patterns** → 1.71x value compression
- **Overall**: 30.59x compression (vs 14.42x with random data)

## 2. Real Data Generator

**Purpose**: Test compression algorithms against actual production monitoring data from the [Westermo test-system-performance-dataset](https://github.com/westermo/test-system-performance-dataset).

### Key Features

- **Authentic Production Data**: Real system metrics from production environments
- **Diverse Metrics**: CPU, memory, disk, network, and system load data
- **Natural Patterns**: Actual timestamp irregularities and value distributions
- **Automatic Download**: Git clones the dataset on first use
- **Smart Caching**: Generated datasets cached per configuration

### Data Processing

1. **Repository Clone**: Downloads dataset from GitHub (one-time)
2. **CSV Discovery**: Finds all .csv files in the dataset
3. **Metric Extraction**: Parses performance data from CSV files
4. **Label Generation**: Creates labels from file paths (host, environment)
5. **Format Conversion**: Transforms to standard metric format

```python
# Example metric structure
{
    "metric_name": "cpu_usage_percent",
    "labels": {
        "host": "system-001",
        "environment": "prod"
    },
    "timestamp": 1729612800,  # Unix timestamp
    "value": 45.2
}
```

### Dataset Sizes

- **small**: ~50,000 data points from select files
- **big**: ~500,000 data points across multiple systems
- **huge**: ~100M data points (full dataset processing)

## Comparison: Synthetic vs Real

| Aspect | Synthetic | Real |
|--------|-----------|------|
| **Timestamp Regularity** | 80% perfect intervals | Variable (production timing) |
| **Value Patterns** | Optimized quantization | Natural precision |
| **Compression Ratio** | ~30x (optimized) | ~20x (natural) |
| **Realism** | Modeled patterns | Actual production data |
| **Use Case** | Algorithm demonstration | Real-world validation |

## Implementation Architecture

The data generator uses a routing pattern in `00_generate_data.py`:

```python
def generate_metric_data(data_generator: str = "synthetic", ...):
    if data_generator == "real":
        from .real_data_generator import generate_real_metric_data
        return generate_real_metric_data(dataset_size=dataset_size)
    elif data_generator == "synthetic":
        return _generate_synthetic_metric_data(...)
```

**Caching System**:
- Cache key: MD5 hash of `{dataset_size}-{data_generator}`
- Cache files: `output/raw_dataset.pkl` + `output/dataset_cache.txt`
- Automatic invalidation when configuration changes

## Why Two Generators?

1. **Synthetic**: Demonstrates maximum compression potential with realistic patterns
2. **Real**: Validates that compression techniques work on actual production data

Both achieve excellent compression ratios, proving the algorithms are production-ready while the synthetic data shows the theoretical maximum efficiency.