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
from lib.enhanced_data_generator import generate_enhanced_metric_data, print_data_stats as print_enhanced_stats

def main():
    """Generate the dataset for the storage engine demonstration."""
    print("=" * 60)
    print("Phase 0: Generating Time-Series Dataset")
    print("=" * 60)
    
    # Get dataset size from environment variable or default to small
    dataset_size = os.environ.get('DATASET_SIZE', 'small')
    
    # Get data generation mode from environment variable
    use_enhanced = os.environ.get('USE_ENHANCED_GENERATOR', 'false').lower() == 'true'
    regularity_level = os.environ.get('REGULARITY_LEVEL', 'medium')  # low, medium, high
    
    # Configuration for data generation
    config = {
        "dataset_size": dataset_size,   # Read from environment or default to small
        "base_interval": 15,        # Base scrape interval (seconds)
        "jitter_range": 5 if not use_enhanced else 2  # Reduced jitter for enhanced mode
    }
    
    if use_enhanced:
        config["regularity_level"] = regularity_level
    
    print(f"Generating dataset with configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    if use_enhanced:
        print(f"  Mode: Enhanced (regularity_level={regularity_level})")
    else:
        print(f"  Mode: Standard")
    print()
    
    # Generate the data using appropriate generator
    print("Generating data points...")
    if use_enhanced:
        data_points = generate_enhanced_metric_data(**config)
        print_function = print_enhanced_stats
        generator_type = "enhanced"
    else:
        data_points = generate_metric_data(**config)
        print_function = print_data_stats
        generator_type = "standard"
    
    # Print statistics
    print_function(data_points)
    
    # Save the raw data for use by other phases
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Use different filename for enhanced data
    filename_suffix = f"_enhanced_{regularity_level}" if use_enhanced else ""
    raw_data_file = os.path.join(output_dir, f"raw_dataset{filename_suffix}.pkl")
    
    with open(raw_data_file, "wb") as f:
        pickle.dump(data_points, f)
    
    # Also save as the standard filename for compatibility
    standard_file = os.path.join(output_dir, "raw_dataset.pkl")
    with open(standard_file, "wb") as f:
        pickle.dump(data_points, f)
    
    file_size = os.path.getsize(raw_data_file)
    print(f"\nRaw dataset saved to: {raw_data_file}")
    print(f"Raw dataset size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
    
    # Also save as a Python module for easy importing
    dataset_module_file = os.path.join(output_dir, "dataset.py")
    with open(dataset_module_file, "w") as f:
        f.write("# Generated dataset for metrics storage demonstration\n")
        f.write(f"# Generator: {generator_type}")
        if use_enhanced:
            f.write(f" (regularity_level={regularity_level})")
        f.write("\n\n")
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

if __name__ == "__main__":
    main()