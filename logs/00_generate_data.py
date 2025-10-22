#!/usr/bin/env python3
"""
Phase 0: Generate Realistic Log Data

This phase integrates with the LogHub dataset repository (https://github.com/logpai/loghub)
to provide real-world log data for compression experiments, similar to how metrics
uses the Westermo test-system-performance-dataset.

LogHub provides a collection of system logs from various sources including:
- Apache web server logs
- OpenSSH server logs  
- Linux system logs
- Hadoop/HDFS logs
- OpenStack infrastructure logs
- And many more real-world log datasets
"""

import os
import sys
import requests
import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import argparse
import json
import time
import hashlib

# Dataset configurations for different sizes
DATASET_CONFIGS = {
    'small': {
        'name': 'Apache',
        'url': 'https://raw.githubusercontent.com/logpai/loghub/master/Apache/Apache_2k.log',
        'filename': 'Apache_2k.log',
        'description': 'Apache web server error log (2k lines)',
        'expected_lines': 2000,
        'size_mb': 0.5
    },
    'big': {
        'name': 'HDFS', 
        'url': 'https://raw.githubusercontent.com/logpai/loghub/master/HDFS/HDFS_2k.log',
        'filename': 'HDFS_2k.log', 
        'description': 'HDFS distributed file system log (2k lines)',
        'expected_lines': 2000,
        'size_mb': 1.0
    },
    'huge': {
        'name': 'OpenSSH',
        'url': 'https://raw.githubusercontent.com/logpai/loghub/master/OpenSSH/OpenSSH_2k.log', 
        'filename': 'OpenSSH_2k.log',
        'description': 'OpenSSH server log (2k lines)',
        'expected_lines': 2000,
        'size_mb': 0.8
    }
}

class LogHubDataGenerator:
    """Generate log datasets using real data from LogHub repository"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
    def get_cached_file_path(self, config: Dict) -> Path:
        """Get the path where the cached file should be stored"""
        return self.cache_dir / config['filename']
    
    def download_dataset(self, config: Dict) -> Path:
        """Download dataset from LogHub if not cached"""
        cached_file = self.get_cached_file_path(config)
        
        if cached_file.exists():
            print(f"Using cached dataset: {cached_file}")
            return cached_file
            
        print(f"Downloading {config['name']} dataset from LogHub...")
        print(f"URL: {config['url']}")
        
        try:
            response = requests.get(config['url'], stream=True)
            response.raise_for_status()
            
            # Write to temporary file first, then move to final location
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
            
            # Move to cache directory
            shutil.move(tmp_path, cached_file)
            print(f"Downloaded and cached: {cached_file}")
            
            return cached_file
            
        except Exception as e:
            print(f"Error downloading dataset: {e}")
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
    
    def analyze_log_format(self, log_file: Path) -> Dict:
        """Analyze the structure and characteristics of the log file"""
        print(f"Analyzing log format...")
        
        stats = {
            'total_lines': 0,
            'sample_lines': [],
            'line_lengths': [],
            'unique_prefixes': set(),
            'timestamps_detected': 0,
            'ip_addresses_detected': 0,
            'log_levels': set(),
            'file_size_bytes': log_file.stat().st_size
        }
        
        import re
        timestamp_pattern = re.compile(r'\d{4}-\d{2}-\d{2}|\d{2}/\w{3}/\d{4}|\w{3}\s+\d{1,2}|\d{6}\s+\d{6}')
        ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
        level_pattern = re.compile(r'\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\b', re.IGNORECASE)
        
        print(f"Reading file: {log_file}")
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                stats['total_lines'] += 1
                stats['line_lengths'].append(len(line))
                
                # Collect sample lines
                if len(stats['sample_lines']) < 10:
                    stats['sample_lines'].append(line[:200])  # Truncate long lines
                
                # Extract prefix (first 20 chars for pattern analysis)
                prefix = line[:20] if len(line) > 20 else line
                stats['unique_prefixes'].add(prefix)
                
                # Look for timestamps
                if timestamp_pattern.search(line):
                    stats['timestamps_detected'] += 1
                
                # Look for IP addresses
                if ip_pattern.search(line):
                    stats['ip_addresses_detected'] += 1
                
                # Look for log levels
                level_match = level_pattern.search(line)
                if level_match:
                    stats['log_levels'].add(level_match.group().upper())
                
                # Progress indicator for large files
                if line_num % 10000 == 0:
                    print(f"  Processed {line_num:,} lines...")
                
                # Limit analysis for very large files
                if line_num > 50000:
                    print(f"  Limiting analysis at {line_num:,} lines for performance")
                    break
        
        print(f"Analysis complete: {stats['total_lines']:,} lines processed")
        
        # Convert sets to lists for JSON serialization
        stats['unique_prefixes'] = list(stats['unique_prefixes'])[:20]  # Keep top 20
        stats['log_levels'] = list(stats['log_levels'])
        
        # Calculate statistics
        if stats['line_lengths']:
            stats['avg_line_length'] = sum(stats['line_lengths']) / len(stats['line_lengths'])
            stats['min_line_length'] = min(stats['line_lengths'])
            stats['max_line_length'] = max(stats['line_lengths'])
        
        return stats
    
    def process_and_save_logs(self, source_file: Path, output_file: Path, size: str) -> Dict:
        """Process the downloaded log file and save in standard format"""
        config = DATASET_CONFIGS[size]
        
        print(f"Processing {config['name']} logs...")
        
        # Analyze the source file
        analysis = self.analyze_log_format(source_file)
        
        lines_written = 0
        
        # Read and write logs, potentially sampling for size control
        with open(source_file, 'r', encoding='utf-8', errors='ignore') as infile:
            with open(output_file, 'w', encoding='utf-8') as outfile:
                for line_num, line in enumerate(infile, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Write the line as-is (LogHub data is already in good format)
                    outfile.write(line + '\n')
                    lines_written += 1
                    
                    # For demonstration, we might limit very large files
                    if lines_written >= 100000 and size == 'small':
                        break
                    elif lines_written >= 500000 and size == 'big':
                        break
        
        # Update analysis with final counts
        analysis['lines_written'] = lines_written
        analysis['output_file_size'] = output_file.stat().st_size
        
        return analysis

def generate_log_data(size: str) -> Dict:
    """Generate log data for the specified size"""
    
    if size not in DATASET_CONFIGS:
        raise ValueError(f"Size must be one of: {list(DATASET_CONFIGS.keys())}")
    
    config = DATASET_CONFIGS[size]
    
    print("=" * 60)
    print(f"Phase 0: Generate Realistic Log Data ({size})")
    print("=" * 60)
    print(f"Dataset: {config['name']} - {config['description']}")
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Initialize data generator
    generator = LogHubDataGenerator()
    
    # Download the dataset
    try:
        source_file = generator.download_dataset(config)
    except Exception as e:
        print(f"Failed to download dataset: {e}")
        print("Please check your internet connection and try again.")
        return {}
    
    # Process and save the logs
    output_file = output_dir / f"logs_{size}.log"
    analysis = generator.process_and_save_logs(source_file, output_file, size)
    
    # Create metadata
    metadata = {
        'phase': 'Phase 0 - Log Data Generation',
        'dataset': config['name'],
        'description': config['description'],
        'source_url': config['url'],
        'size_category': size,
        'output_file': str(output_file),
        'generation_time': time.time(),
        'analysis': analysis
    }
    
    # Save metadata
    metadata_file = output_dir / f"phase0_logs_metadata_{size}.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)
    
    # Print summary
    print(f"\n📊 Log Data Generation Results:")
    print(f"  Dataset: {config['name']}")
    print(f"  Source: LogHub repository")
    print(f"  Output file: {output_file}")
    print(f"  Total lines: {analysis['lines_written']:,}")
    print(f"  File size: {analysis['output_file_size']:,} bytes ({analysis['output_file_size'] / 1024 / 1024:.2f} MB)")
    
    if analysis['line_lengths']:
        print(f"  Average line length: {analysis['avg_line_length']:.1f} characters")
        print(f"  Line length range: {analysis['min_line_length']}-{analysis['max_line_length']} characters")
    
    print(f"  Timestamps detected: {analysis['timestamps_detected']:,}")
    print(f"  IP addresses detected: {analysis['ip_addresses_detected']:,}")
    
    if analysis['log_levels']:
        print(f"  Log levels found: {', '.join(analysis['log_levels'])}")
    
    print(f"\n📁 Sample log lines:")
    for i, line in enumerate(analysis['sample_lines'][:5], 1):
        print(f"  {i}. {line}")
    
    print(f"\n✅ Phase 0 completed successfully!")
    print(f"   Output: {output_file}")
    print(f"   Metadata: {metadata_file}")
    
    return metadata

def main():
    parser = argparse.ArgumentParser(description='Generate realistic log data from LogHub')
    parser.add_argument('--size', choices=['small', 'big', 'huge'], default='small',
                       help='Size of the dataset to generate')
    
    args = parser.parse_args()
    
    try:
        result = generate_log_data(args.size)
        return result is not None
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)