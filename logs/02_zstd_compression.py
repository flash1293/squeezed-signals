#!/usr/bin/env python3
"""
Phase 2: Zstd Compression

This phase applies Zstandard compression to the plain text logs.
Zstd provides excellent compression ratios while maintaining fast
decompression speeds, making it ideal for log storage.

Expected result: ~3-5x compression
"""

import json
import time
import zstandard as zstd
from pathlib import Path
from typing import Dict, List, Any, Optional


class ZstdLogStorage:
    """
    Storage that applies Zstandard compression to log data.
    This builds on the plain text baseline but adds compression.
    """
    
    def __init__(self, compression_level: int = 22):
        self.lines: List[str] = []
        self.compression_level = compression_level
        self.compressor = zstd.ZstdCompressor(level=compression_level)
        self.decompressor = zstd.ZstdDecompressor()
        self.metadata = {
            'total_lines': 0,
            'original_size_bytes': 0,
            'compressed_size_bytes': 0,
            'compression_level': compression_level,
            'storage_format': 'zstd_compressed',
            'phase': 'Phase 2 - Zstd Compression'
        }
    
    def add_line(self, line: str) -> None:
        """Add a log line to storage"""
        self.lines.append(line)
        self.metadata['total_lines'] += 1
        self.metadata['original_size_bytes'] += len(line) + 1  # +1 for newline
    
    def compress_data(self) -> bytes:
        """Compress all stored lines into a single byte array"""
        # Join all lines with newlines
        text_data = '\n'.join(self.lines).encode('utf-8')
        
        # Compress with zstd
        compressed_data = self.compressor.compress(text_data)
        self.metadata['compressed_size_bytes'] = len(compressed_data)
        
        return compressed_data
    
    def decompress_data(self, compressed_data: bytes) -> List[str]:
        """Decompress data back to original lines"""
        decompressed_text = self.decompressor.decompress(compressed_data).decode('utf-8')
        return decompressed_text.split('\n')
    
    def get_compression_ratio(self) -> float:
        """Calculate compression ratio"""
        if self.metadata['compressed_size_bytes'] == 0:
            return 1.0
        return self.metadata['original_size_bytes'] / self.metadata['compressed_size_bytes']
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get statistics about the stored data"""
        if not self.lines:
            return {'error': 'No data stored'}
        
        line_lengths = [len(line) for line in self.lines]
        
        return {
            'total_lines': self.metadata['total_lines'],
            'original_size_bytes': self.metadata['original_size_bytes'],
            'compressed_size_bytes': self.metadata['compressed_size_bytes'],
            'compression_ratio': self.get_compression_ratio(),
            'average_line_length': sum(line_lengths) / len(line_lengths),
            'min_line_length': min(line_lengths),
            'max_line_length': max(line_lengths),
            'compression_level': self.metadata['compression_level'],
            'storage_format': self.metadata['storage_format'],
            'phase': self.metadata['phase']
        }
    
    def save_to_file(self, output_path: Path) -> Dict[str, Any]:
        """Save the compressed logs to a file"""
        # Compress the data
        compressed_data = self.compress_data()
        
        # Write the compressed file
        with open(output_path, 'wb') as f:
            f.write(compressed_data)
        
        # Verify file size matches our calculation
        file_size = output_path.stat().st_size
        assert file_size == self.metadata['compressed_size_bytes'], \
            f"File size mismatch: {file_size} != {self.metadata['compressed_size_bytes']}"
        
        # Create metadata
        metadata = {
            'phase': self.metadata['phase'],
            'storage_format': self.metadata['storage_format'],
            'compression_level': self.metadata['compression_level'],
            'file_size_bytes': file_size,
            'original_size_bytes': self.metadata['original_size_bytes'],
            'compression_ratio': self.get_compression_ratio(),
            'storage_stats': self.get_storage_stats(),
            'processing_time': time.time()
        }
        
        return metadata
    
    def verify_decompression(self, compressed_file: Path) -> bool:
        """Verify that we can decompress the file correctly"""
        try:
            with open(compressed_file, 'rb') as f:
                compressed_data = f.read()
            
            decompressed_lines = self.decompress_data(compressed_data)
            
            # Check that we get the same number of lines
            if len(decompressed_lines) != len(self.lines):
                print(f"❌ Line count mismatch: {len(decompressed_lines)} != {len(self.lines)}")
                return False
            
            # Check that the content matches (sample check)
            for i in range(min(10, len(self.lines))):
                if decompressed_lines[i] != self.lines[i]:
                    print(f"❌ Content mismatch at line {i}")
                    print(f"   Original: {repr(self.lines[i])}")
                    print(f"   Decompressed: {repr(decompressed_lines[i])}")
                    return False
            
            print(f"✅ Decompression verification passed")
            return True
            
        except Exception as e:
            print(f"❌ Decompression verification failed: {e}")
            return False


def process_log_file(input_file: Path, output_file: Path, metadata_file: Path, 
                    compression_level: int = 22) -> Dict[str, Any]:
    """Process a log file with Zstd compression"""
    print(f"Processing {input_file.name} with Zstd compression (level {compression_level})...")
    
    start_time = time.time()
    storage = ZstdLogStorage(compression_level=compression_level)
    
    # Read and store each line
    lines_processed = 0
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.rstrip('\n\r')  # Remove newlines but keep other whitespace
            storage.add_line(line)
            lines_processed += 1
            
            if lines_processed % 1000 == 0:
                print(f"  Loaded {lines_processed:,} lines...")
    
    print(f"  Compressing {lines_processed:,} lines...")
    
    # Save the result (this triggers compression)
    metadata = storage.save_to_file(output_file)
    
    processing_time = time.time() - start_time
    metadata['processing_time_seconds'] = processing_time
    metadata['lines_processed'] = lines_processed
    
    # Verify decompression works
    if not storage.verify_decompression(output_file):
        raise ValueError("Decompression verification failed")
    
    # Save metadata
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"  Completed in {processing_time:.2f} seconds")
    print(f"  Lines processed: {lines_processed:,}")
    print(f"  Original size: {metadata['original_size_bytes']:,} bytes")
    print(f"  Compressed size: {metadata['file_size_bytes']:,} bytes")
    print(f"  Compression ratio: {metadata['compression_ratio']:.2f}x")
    
    return metadata


def main():
    """Main function to process logs with phase 2 Zstd compression"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 2: Zstd Compressed Log Storage')
    parser.add_argument('--size', choices=['small', 'big', 'huge'], default='small',
                       help='Dataset size to process (default: small)')
    parser.add_argument('--level', type=int, default=22, choices=range(1, 23),
                       help='Zstd compression level (1-22, default: 22)')
    
    args = parser.parse_args()
    
    # Setup paths
    input_file = Path(f'output/logs_{args.size}.log')
    output_file = Path(f'output/phase2_logs_{args.size}.zst')
    metadata_file = Path(f'output/phase2_logs_metadata_{args.size}.json')
    
    # Ensure output directory exists
    output_file.parent.mkdir(exist_ok=True)
    
    # Check input file exists
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        print(f"   Run Phase 0 first: python 00_generate_data.py --size {args.size}")
        return 1
    
    print("=" * 60)
    print(f"Phase 2: Zstd Compression ({args.size})")
    print("=" * 60)
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print(f"Compression level: {args.level}")
    
    try:
        # Process the file
        metadata = process_log_file(input_file, output_file, metadata_file, args.level)
        
        print("\n📊 Phase 2 Compression Results:")
        print(f"  Lines processed: {metadata['lines_processed']:,}")
        print(f"  Original size: {metadata['original_size_bytes']:,} bytes ({metadata['original_size_bytes']/1024:.1f} KB)")
        print(f"  Compressed size: {metadata['file_size_bytes']:,} bytes ({metadata['file_size_bytes']/1024:.1f} KB)")
        print(f"  Compression ratio: {metadata['compression_ratio']:.2f}x")
        print(f"  Space saved: {(1 - metadata['file_size_bytes']/metadata['original_size_bytes'])*100:.1f}%")
        print(f"  Processing time: {metadata['processing_time_seconds']:.2f} seconds")
        
        print(f"\n✅ Phase 2 completed successfully!")
        print(f"   Output: {output_file}")
        print(f"   Metadata: {metadata_file}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error in Phase 2 processing: {e}")
        return 1


if __name__ == '__main__':
    exit(main())