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

def get_cache_key(config):
    """Generate a cache key based on configuration."""
    # Create a stable hash of the configuration
    import hashlib
    config_str = f"{config['dataset_size']}-{config['data_generator']}"
    return hashlib.md5(config_str.encode()).hexdigest()

def check_cache(config):
    """Check if cached dataset exists for this configuration."""
    output_dir = "output"
    raw_data_file = os.path.join(output_dir, "raw_dataset.pkl")
    cache_info_file = os.path.join(output_dir, "dataset_cache.txt")
    
    if not os.path.exists(raw_data_file) or not os.path.exists(cache_info_file):
        return None
    
    # Check if cache info matches current config
    try:
        with open(cache_info_file, 'r') as f:
            cached_config = f.read().strip()
        
        current_cache_key = get_cache_key(config)
        if cached_config == current_cache_key:
            # Load cached data
            with open(raw_data_file, "rb") as f:
                data_points = pickle.load(f)
            return data_points
    except:
        pass
    
    return None

def save_to_cache(data_points, config):
    """Save dataset and configuration to cache."""
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Save data
    raw_data_file = os.path.join(output_dir, "raw_dataset.pkl")
    with open(raw_data_file, "wb") as f:
        pickle.dump(data_points, f)
    
    # Save cache info
    cache_info_file = os.path.join(output_dir, "dataset_cache.txt")
    cache_key = get_cache_key(config)
    with open(cache_info_file, 'w') as f:
        f.write(cache_key)
    
    return raw_data_file

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
    
    print(f"Dataset configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    if data_generator == "synthetic":
        print(f"  Enhanced patterns: Infrastructure correlation, value quantization, timestamp regularity")
    elif data_generator == "real":
        print(f"  Real monitoring data: Westermo test-system-performance-dataset")
    print()
    
    # Check cache first
    print("🔍 Checking for cached dataset...")
    data_points = check_cache(config)
    
    if data_points is not None:
        print(f"✅ Found cached dataset with {len(data_points):,} points")
        print("💨 Using cached data (use different config or delete output/raw_dataset.pkl to regenerate)")
    else:
        print("📊 No cache found, generating new dataset...")
        # Generate the data using appropriate generator
        data_points = generate_metric_data(**config)
        
        # Save to cache
        raw_data_file = save_to_cache(data_points, config)
        print(f"💾 Saved to cache: {raw_data_file}")
    
    # Print statistics using appropriate function
    if data_generator == "real":
        from lib.real_data_generator import print_real_data_stats
        print_real_data_stats(data_points)
    else:
        print_data_stats(data_points)
    
    # Ensure output files exist and are up to date
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    raw_data_file = os.path.join(output_dir, "raw_dataset.pkl")
    
    # Check if we need to update the pickle file (might be cached from different config)
    if not os.path.exists(raw_data_file):
        print(f"\n💾 Saving dataset to: {raw_data_file}")
        with open(raw_data_file, "wb") as f:
            pickle.dump(data_points, f)
    
    file_size = os.path.getsize(raw_data_file)
    print(f"\n📁 Dataset file: {raw_data_file}")
    print(f"📏 Dataset size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
    
    # Also save as a Python module for easy importing
    dataset_module_file = os.path.join(output_dir, "dataset.py")
    print(f"📝 Updating Python module: {dataset_module_file}")
    with open(dataset_module_file, "w") as f:
        f.write("# Generated dataset for metrics storage demonstration\n")
        if data_generator == "real":
            f.write("# Real monitoring data from westermo/test-system-performance-dataset\n\n")
        else:
            f.write("# Enhanced data generation with infrastructure correlation and value quantization\n\n")
        f.write("DATASET = [\n")
        
        for i, point in enumerate(data_points):
            if i > 0:
                f.write(",\n")
            f.write(f"    {point!r}")
        
        f.write("\n]\n")
    
    print(f"📏 Python module size: {os.path.getsize(dataset_module_file):,} bytes")
    
    print(f"\n✅ Phase 0 completed successfully!")
    print(f"📊 Final dataset: {len(data_points):,} data points across {len(set((p['metric_name'], tuple(sorted(p['labels'].items()))) for p in data_points))} unique series")
    
    return data_points

if __name__ == "__main__":
    main()