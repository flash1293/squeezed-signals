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
import subprocess
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
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
        'size_mb': 1.0
    }
}


class LogHubScraper:
    """
    Scrapes the LogHub repository to extract full dataset download URLs.
    This ensures we can access the complete datasets, not just the 2k samples.
    """
    
    def __init__(self):
        self.temp_dir = None
        self.loghub_path = None
        
    def clone_loghub_repo(self) -> Path:
        """Clone the LogHub repository to a temporary directory"""
        if self.temp_dir is None:
            self.temp_dir = tempfile.mkdtemp(prefix='loghub_scrape_')
            self.loghub_path = Path(self.temp_dir) / 'loghub'
            
            print(f"Cloning LogHub repository to {self.loghub_path}...")
            result = subprocess.run([
                'git', 'clone', '--depth', '1',
                'https://github.com/logpai/loghub.git',
                str(self.loghub_path)
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                raise RuntimeError(f"Failed to clone LogHub repository: {result.stderr}")
                
            print(f"✅ LogHub repository cloned successfully")
            
        return self.loghub_path
    
    def extract_zenodo_urls(self) -> Dict[str, str]:
        """Extract Zenodo download URLs from the LogHub README"""
        loghub_path = self.clone_loghub_repo()
        readme_path = loghub_path / 'README.md'
        
        if not readme_path.exists():
            raise FileNotFoundError(f"README.md not found in {loghub_path}")
        
        print("Parsing README.md for Zenodo URLs...")
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_content = f.read()
        
        zenodo_urls = {}
        
        # Updated pattern to match the actual Zenodo URLs in the README
        zenodo_pattern = r'https://zenodo\.org/records/\d+/files/[^)?\s]+'
        
        # Find all Zenodo URLs in the README
        all_zenodo_urls = re.findall(zenodo_pattern, readme_content)
        
        print(f"Found {len(all_zenodo_urls)} Zenodo URLs in README")
        
        # Map specific datasets to their URLs based on filename patterns
        for url in all_zenodo_urls:
            filename = url.split('/')[-1].lower()
            
            if 'apache' in filename:
                zenodo_urls['Apache'] = url
            elif 'hdfs_v1' in filename:
                zenodo_urls['HDFS'] = url
            elif 'ssh' in filename:  # OpenSSH files are named SSH.tar.gz
                zenodo_urls['OpenSSH'] = url
        
        # If filename-based mapping doesn't work, try parsing the table structure
        if not zenodo_urls:
            lines = readme_content.split('\n')
            for i, line in enumerate(lines):
                if '|' in line:
                    # Check if this line contains a dataset name we're interested in
                    dataset_name = None
                    if 'Apache' in line and 'web server' in line:
                        dataset_name = 'Apache'
                    elif 'HDFS_v1' in line:
                        dataset_name = 'HDFS'
                    elif 'OpenSSH' in line:
                        dataset_name = 'OpenSSH'
                    
                    if dataset_name:
                        # Find Zenodo URLs in this line
                        zenodo_matches = re.findall(zenodo_pattern, line)
                        if zenodo_matches:
                            zenodo_urls[dataset_name] = zenodo_matches[0]
        
        print(f"Extracted Zenodo URLs for {len(zenodo_urls)} datasets")
        for dataset, url in zenodo_urls.items():
            print(f"  {dataset}: {url}")
            
        return zenodo_urls
    
    def cleanup(self):
        """Clean up temporary directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            print(f"🧹 Cleaned up temporary directory: {self.temp_dir}")


# Updated dataset configurations with full dataset capability
def get_full_dataset_configs() -> Dict[str, Dict]:
    """
    Get dataset configurations with both sample and full dataset URLs.
    This function will scrape the LogHub repository for full dataset URLs.
    """
    scraper = LogHubScraper()
    
    try:
        zenodo_urls = scraper.extract_zenodo_urls()
        
        # Enhanced configurations with full dataset URLs
        full_configs = {
            'small': {
                'name': 'Apache',
                'sample_url': 'https://raw.githubusercontent.com/logpai/loghub/master/Apache/Apache_2k.log',
                'full_url': zenodo_urls.get('Apache'),
                'filename': 'Apache_2k.log',
                'full_filename': 'Apache.log',
                'description': 'Apache web server error log',
                'sample_lines': 2000,
                'full_lines': 56481,
                'target_size_mb': 5,  # Trim full dataset to 5MB
                'size_mb': 0.5
            },
            'big': {
                'name': 'HDFS',
                'sample_url': 'https://raw.githubusercontent.com/logpai/loghub/master/HDFS/HDFS_2k.log',
                'full_url': zenodo_urls.get('HDFS'),
                'filename': 'HDFS_2k.log',
                'full_filename': 'HDFS_v1.log',
                'description': 'HDFS distributed file system log',
                'sample_lines': 2000,
                'full_lines': 11175629,
                'target_size_mb': 10,  # Trim full dataset to 10MB
                'size_mb': 1.0
            },
            'huge': {
                'name': 'OpenSSH',
                'sample_url': 'https://raw.githubusercontent.com/logpai/loghub/master/OpenSSH/OpenSSH_2k.log',
                'full_url': zenodo_urls.get('OpenSSH'),
                'filename': 'OpenSSH_2k.log',
                'full_filename': 'OpenSSH.log',
                'description': 'OpenSSH server log',
                'sample_lines': 2000,
                'full_lines': 655146,
                'target_size_mb': 100,  # Trim full dataset to 100MB
                'size_mb': 1.0
            }
        }
        
        return full_configs
        
    finally:
        scraper.cleanup()


# Original dataset configurations for compatibility
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
    
    def __init__(self, cache_dir: str = "cache", use_full_datasets: bool = True):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.use_full_datasets = use_full_datasets
        
    def get_cached_file_path(self, config: Dict, use_full: bool = False) -> Path:
        """Get the path where the cached file should be stored"""
        if use_full and config.get('full_filename'):
            return self.cache_dir / config['full_filename']
        return self.cache_dir / config['filename']
    
    def download_dataset(self, config: Dict, use_full: bool = None) -> Path:
        """Download dataset from LogHub if not cached"""
        if use_full is None:
            use_full = self.use_full_datasets and config.get('full_url') is not None
            
        cached_file = self.get_cached_file_path(config, use_full)
        url = config.get('full_url') if use_full else config.get('sample_url', config.get('url'))
        dataset_type = "full" if use_full else "sample"
        
        if cached_file.exists():
            print(f"Using cached {dataset_type} dataset: {cached_file}")
            return cached_file
            
        if url is None:
            print(f"❌ No URL available for {dataset_type} {config['name']} dataset")
            if use_full:
                # Fallback to sample dataset
                print(f"   Falling back to sample dataset...")
                return self.download_dataset(config, use_full=False)
            raise ValueError(f"No URL available for {config['name']} dataset")
            
        print(f"Downloading {config['name']} {dataset_type} dataset from LogHub...")
        print(f"URL: {url}")
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Download to a temporary file first
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name
            
            # Check if this is a compressed file that needs extraction
            if url.endswith(('.tar.gz', '.zip')):
                print(f"Extracting compressed dataset...")
                extracted_file = self.extract_compressed_file(tmp_path, url, config, use_full)
                os.unlink(tmp_path)  # Clean up compressed file
                print(f"Downloaded and cached: {extracted_file}")
                return extracted_file
            else:
                # Move to cache directory for non-compressed files
                shutil.move(tmp_path, cached_file)
                print(f"Downloaded and cached: {cached_file}")
                return cached_file
            
        except Exception as e:
            print(f"Error downloading {dataset_type} dataset: {e}")
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.unlink(tmp_path)
            
            # If full dataset failed, try sample dataset
            if use_full:
                print(f"   Falling back to sample dataset...")
                return self.download_dataset(config, use_full=False)
            raise
    
    def extract_compressed_file(self, compressed_path: str, url: str, config: Dict, use_full: bool) -> Path:
        """Extract a compressed file and return the path to the log file"""
        
        # Determine the expected log file name inside the archive
        expected_names = []
        if config['name'] == 'Apache':
            expected_names = ['Apache.log', 'apache.log', 'error_log', 'error.log']
        elif config['name'] == 'HDFS':
            expected_names = ['HDFS_v1.log', 'HDFS.log', 'hdfs.log']
        elif config['name'] == 'OpenSSH':
            expected_names = ['SSH.log', 'OpenSSH.log', 'openssh.log', 'auth.log']
        
        # Add generic patterns
        expected_names.extend([f"{config['name']}.log", f"{config['name'].lower()}.log"])
        
        extracted_dir = self.cache_dir / f"extracted_{config['name'].lower()}"
        extracted_dir.mkdir(exist_ok=True)
        
        try:
            if url.endswith('.zip'):
                import zipfile
                with zipfile.ZipFile(compressed_path, 'r') as zip_ref:
                    zip_ref.extractall(extracted_dir)
            elif url.endswith('.tar.gz'):
                import tarfile
                with tarfile.open(compressed_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(extracted_dir)
            
            # Find the log file in the extracted contents
            log_file = self.find_log_file_in_directory(extracted_dir, expected_names)
            
            if log_file is None:
                # List all files to help debug
                all_files = list(extracted_dir.rglob('*'))
                print(f"⚠️  Could not find expected log file. Files in archive:")
                for f in all_files[:10]:  # Show first 10 files
                    print(f"   {f.relative_to(extracted_dir)}")
                if len(all_files) > 10:
                    print(f"   ... and {len(all_files) - 10} more files")
                
                # Use the largest .log file as fallback
                log_files = [f for f in all_files if f.suffix.lower() == '.log' and f.is_file()]
                if log_files:
                    log_file = max(log_files, key=lambda f: f.stat().st_size)
                    print(f"   Using largest .log file: {log_file.name}")
                else:
                    raise FileNotFoundError(f"No .log files found in extracted archive")
            
            # Copy to the expected cache location
            cached_file = self.get_cached_file_path(config, use_full)
            shutil.copy2(log_file, cached_file)
            
            # Clean up extracted directory
            shutil.rmtree(extracted_dir)
            
            return cached_file
            
        except Exception as e:
            # Clean up on error
            if extracted_dir.exists():
                shutil.rmtree(extracted_dir)
            raise e
    
    def find_log_file_in_directory(self, directory: Path, expected_names: List[str]) -> Optional[Path]:
        """Find a log file in the directory based on expected names"""
        
        # First, try exact matches
        for name in expected_names:
            potential_file = directory / name
            if potential_file.is_file():
                return potential_file
        
        # Then, try recursive search
        for name in expected_names:
            matches = list(directory.rglob(name))
            if matches:
                return matches[0]
        
        return None
    
    def trim_dataset_to_size(self, input_file: Path, target_size_mb: float) -> Path:
        """Trim a dataset to approximately the target size in MB"""
        target_size_bytes = int(target_size_mb * 1024 * 1024)
        
        # Check if trimming is needed
        current_size = input_file.stat().st_size
        if current_size <= target_size_bytes:
            print(f"Dataset already smaller than target ({current_size/1024/1024:.1f}MB <= {target_size_mb}MB)")
            return input_file
        
        # Create trimmed filename
        trimmed_file = input_file.parent / f"{input_file.stem}_trimmed{input_file.suffix}"
        
        if trimmed_file.exists():
            print(f"Using existing trimmed dataset: {trimmed_file}")
            return trimmed_file
        
        print(f"Trimming dataset from {current_size/1024/1024:.1f}MB to ~{target_size_mb}MB...")
        
        bytes_written = 0
        lines_written = 0
        
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as infile:
            with open(trimmed_file, 'w', encoding='utf-8') as outfile:
                for line in infile:
                    line_bytes = len(line.encode('utf-8'))
                    if bytes_written + line_bytes > target_size_bytes:
                        break
                    
                    outfile.write(line)
                    bytes_written += line_bytes
                    lines_written += 1
                    
                    if lines_written % 10000 == 0:
                        print(f"  Processed {lines_written:,} lines ({bytes_written/1024/1024:.1f}MB)...")
        
        final_size = trimmed_file.stat().st_size
        print(f"✅ Trimmed dataset created: {lines_written:,} lines, {final_size/1024/1024:.1f}MB")
        return trimmed_file
    
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

def generate_log_data(size: str, use_full_datasets: bool = True) -> Dict:
    """Generate log data for the specified size"""
    
    # Get full dataset configurations with Zenodo URLs
    try:
        if use_full_datasets:
            configs = get_full_dataset_configs()
        else:
            configs = DATASET_CONFIGS
    except Exception as e:
        print(f"⚠️  Warning: Failed to get full dataset configurations: {e}")
        print("   Falling back to sample datasets...")
        configs = DATASET_CONFIGS
        use_full_datasets = False
    
    if size not in configs:
        raise ValueError(f"Size must be one of: {list(configs.keys())}")
    
    config = configs[size]
    
    print("=" * 60)
    print(f"Phase 0: Generate Realistic Log Data ({size})")
    print("=" * 60)
    print(f"Dataset: {config['name']} - {config['description']}")
    
    if use_full_datasets and config.get('full_url'):
        print(f"Using full dataset (target size: {config.get('target_size_mb', 'unlimited')}MB)")
    else:
        print(f"Using sample dataset")
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Initialize data generator
    generator = LogHubDataGenerator(use_full_datasets=use_full_datasets)
    
    # Download the dataset
    try:
        source_file = generator.download_dataset(config)
        
        # If using full dataset, trim to target size
        if use_full_datasets and config.get('target_size_mb'):
            source_file = generator.trim_dataset_to_size(source_file, config['target_size_mb'])
            
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
        'source_url': config.get('full_url') if use_full_datasets else config.get('sample_url', config.get('url')),
        'dataset_type': 'full' if use_full_datasets and config.get('full_url') else 'sample',
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
    parser.add_argument('--sample-only', action='store_true',
                       help='Use only sample datasets (2k lines) instead of full datasets')
    
    args = parser.parse_args()
    
    try:
        result = generate_log_data(args.size, use_full_datasets=not args.sample_only)
        return result is not None
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)