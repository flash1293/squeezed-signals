#!/usr/bin/env python3
"""
Phase 1: Plain Text Baseline Storage

This phase establishes our baseline by storing logs in plain text format
with basic line-by-line indexing. This gives us our reference point for
measuring compression improvements in subsequent phases.

Expected result: ~1x compression (no compression)
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any


class PlainTextLogStorage:
    """
    Baseline storage that simply stores log lines as-is with basic metadata.
    This establishes our reference point for compression measurement.
    """
    
    def __init__(self):
        self.lines: List[str] = []
        self.metadata = {
            'total_lines': 0,
            'total_characters': 0,
            'line_index': [],  # Store start position of each line
            'storage_format': 'plain_text',
            'phase': 'Phase 1 - Plain Text Baseline'
        }
    
    def add_line(self, line: str) -> None:
        """Add a log line to storage"""
        # Record where this line starts in our character stream
        char_position = self.metadata['total_characters']
        self.metadata['line_index'].append(char_position)
        
        # Store the line as-is
        self.lines.append(line)
        self.metadata['total_lines'] += 1
        self.metadata['total_characters'] += len(line) + 1  # +1 for newline
    
    def get_line(self, line_number: int) -> str:
        """Retrieve a specific line (0-indexed)"""
        if 0 <= line_number < len(self.lines):
            return self.lines[line_number]
        raise IndexError(f"Line {line_number} not found")
    
    def get_lines_range(self, start: int, end: int) -> List[str]:
        """Retrieve a range of lines"""
        return self.lines[start:end]
    
    def search_lines(self, pattern: str) -> List[int]:
        """Search for lines containing a pattern (returns line numbers)"""
        matches = []
        for i, line in enumerate(self.lines):
            if pattern in line:
                matches.append(i)
        return matches
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get statistics about the stored data"""
        if not self.lines:
            return {'error': 'No data stored'}
        
        line_lengths = [len(line) for line in self.lines]
        
        return {
            'total_lines': self.metadata['total_lines'],
            'total_characters': self.metadata['total_characters'],
            'average_line_length': sum(line_lengths) / len(line_lengths),
            'min_line_length': min(line_lengths),
            'max_line_length': max(line_lengths),
            'storage_efficiency': 1.0,  # Baseline is 1.0 (no compression)
            'index_overhead_bytes': len(self.metadata['line_index']) * 8,  # Rough estimate
            'format': self.metadata['storage_format'],
            'phase': self.metadata['phase']
        }
    
    def save_to_file(self, output_path: Path) -> Dict[str, Any]:
        """Save the stored logs to a file"""
        # Write the plain text file
        with open(output_path, 'w', encoding='utf-8') as f:
            for line in self.lines:
                f.write(line + '\n')
        
        # Calculate file size
        file_size = output_path.stat().st_size
        
        # Calculate compression ratio (baseline = 1.0)
        original_size = sum(len(line) + 1 for line in self.lines)  # +1 for newlines
        compression_ratio = original_size / file_size if file_size > 0 else 1.0
        
        # Create metadata
        metadata = {
            'phase': self.metadata['phase'],
            'storage_format': self.metadata['storage_format'],
            'file_size_bytes': file_size,
            'original_size_bytes': original_size,
            'compression_ratio': compression_ratio,
            'storage_stats': self.get_storage_stats(),
            'processing_time': time.time()
        }
        
        return metadata


def process_log_file(input_file: Path, output_file: Path, metadata_file: Path) -> Dict[str, Any]:
    """Process a log file with plain text baseline storage"""
    print(f"Processing {input_file.name} with plain text baseline storage...")
    
    start_time = time.time()
    storage = PlainTextLogStorage()
    
    # Read and store each line
    lines_processed = 0
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.rstrip('\n\r')  # Remove newlines but keep other whitespace
            storage.add_line(line)
            lines_processed += 1
            
            if lines_processed % 1000 == 0:
                print(f"  Processed {lines_processed:,} lines...")
    
    processing_time = time.time() - start_time
    
    # Save the result
    metadata = storage.save_to_file(output_file)
    metadata['processing_time_seconds'] = processing_time
    metadata['lines_processed'] = lines_processed
    
    # Save metadata
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"  Completed in {processing_time:.2f} seconds")
    print(f"  Lines processed: {lines_processed:,}")
    print(f"  Output size: {metadata['file_size_bytes']:,} bytes")
    print(f"  Compression ratio: {metadata['compression_ratio']:.2f}x")
    
    return metadata


def main():
    """Main function to process logs with phase 1 baseline storage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 1: Plain Text Baseline Log Storage')
    parser.add_argument('--size', choices=['small', 'big', 'huge'], default='small',
                       help='Dataset size to process (default: small)')
    
    args = parser.parse_args()
    
    # Setup paths
    input_file = Path(f'output/logs_{args.size}.log')
    output_file = Path(f'output/phase1_logs_{args.size}.log')
    metadata_file = Path(f'output/phase1_logs_metadata_{args.size}.json')
    
    # Ensure output directory exists
    output_file.parent.mkdir(exist_ok=True)
    
    # Check input file exists
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        print(f"   Run Phase 0 first: python 00_generate_data.py --size {args.size}")
        return 1
    
    print("=" * 60)
    print(f"Phase 1: Plain Text Baseline Storage ({args.size})")
    print("=" * 60)
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    
    try:
        # Process the file
        metadata = process_log_file(input_file, output_file, metadata_file)
        
        print("\n📊 Phase 1 Baseline Results:")
        print(f"  Lines processed: {metadata['lines_processed']:,}")
        print(f"  Original size: {metadata['original_size_bytes']:,} bytes ({metadata['original_size_bytes']/1024:.1f} KB)")
        print(f"  Output size: {metadata['file_size_bytes']:,} bytes ({metadata['file_size_bytes']/1024:.1f} KB)")
        print(f"  Compression ratio: {metadata['compression_ratio']:.2f}x")
        print(f"  Processing time: {metadata['processing_time_seconds']:.2f} seconds")
        
        print(f"\n✅ Phase 1 completed successfully!")
        print(f"   Output: {output_file}")
        print(f"   Metadata: {metadata_file}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error in Phase 1 processing: {e}")
        return 1


if __name__ == '__main__':
    exit(main())