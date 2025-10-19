#!/usr/bin/env python3
"""
Phase 0: Data Generation

This script generates a realistic, yet compressible, dataset of time-series metrics
that will be used by all subsequent storage implementations.
"""

import os
import sys
import pickle
from lib.data_generator import generate_metric_data, print_data_stats

def main():
    """Generate the dataset for the storage engine demonstration."""
    print("=" * 60)
    print("Phase 0: Generating Time-Series Dataset")
    print("=" * 60)
    
    # Get configuration from environment variables or defaults
    dataset_size = os.environ.get('DATASET_SIZE', 'small')
    data_generator = os.environ.get('DATA_GENERATOR', 'synthetic')
    
    # Configuration for data generation
    config = {
        "dataset_size": dataset_size,      # Read from environment or default to small
        "data_generator": data_generator,  # Read from environment or default to synthetic
        "base_interval": 15,               # Base scrape interval (seconds) - synthetic only
        "jitter_range": 2                  # Random jitter range (seconds) - synthetic only
    }
    
    print(f"Generating dataset with configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    if data_generator == "synthetic":
        print(f"  Enhanced patterns: Infrastructure correlation, value quantization, timestamp regularity")
    elif data_generator == "real":
        print(f"  Real monitoring data: Westermo test-system-performance-dataset")
    print()
    
    # Generate the data using appropriate generator
    print("Generating data points...")
    data_points = generate_metric_data(**config)
    
    # Print statistics using appropriate function
    if data_generator == "real":
        from lib.real_data_generator import print_real_data_stats
        print_real_data_stats(data_points)
    else:
        print_data_stats(data_points)
    
    # Save the raw data for use by other phases
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    raw_data_file = os.path.join(output_dir, "raw_dataset.pkl")
    with open(raw_data_file, "wb") as f:
        pickle.dump(data_points, f)
    
    file_size = os.path.getsize(raw_data_file)
    print(f"\nRaw dataset saved to: {raw_data_file}")
    print(f"Raw dataset size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
    
    # Also save as a Python module for easy importing
    dataset_module_file = os.path.join(output_dir, "dataset.py")
    with open(dataset_module_file, "w") as f:
        f.write("# Generated dataset for metrics storage demonstration\n")
        f.write("# Enhanced data generation with infrastructure correlation and value quantization\n\n")
        f.write("DATASET = [\n")
        
        for i, point in enumerate(data_points):
            if i > 0:
                f.write(",\n")
            f.write(f"    {point!r}")
        
        f.write("\n]\n")
    
    print(f"Dataset module saved to: {dataset_module_file}")
    print(f"Dataset module size: {os.path.getsize(dataset_module_file):,} bytes")
    
    print(f"\n✅ Phase 0 completed successfully!")
    print(f"Generated {len(data_points):,} data points across {len(set((p['metric_name'], tuple(sorted(p['labels'].items()))) for p in data_points))} unique series")
    
    return data_points
    
    print(f"\n✅ Phase 0 completed successfully!")
    print(f"Generated {len(data_points):,} data points across {len(set((p['metric_name'], tuple(sorted(p['labels'].items()))) for p in data_points))} unique series")
    
    return data_points

if __name__ == "__main__":
    main()