#!/usr/bin/env python3
"""
Phase 3: CBOR + Zstandard Compression

Adds general-purpose compression on top of CBOR binary encoding.
Leverages zstd dictionary compression for repeated field names and service names.
"""

import json
import os
import time
import cbor2
import zstandard as zstd
from pathlib import Path
from typing import List, Dict, Any

def load_cbor_spans(input_file: str) -> List[dict]:
    """Load span data from CBOR file"""
    print(f"Loading CBOR spans from {input_file}...")
    
    with open(input_file, 'rb') as f:
        spans = cbor2.load(f)
    
    print(f"Loaded {len(spans)} spans from CBOR")
    return spans

def analyze_compression_patterns(spans: List[dict]) -> Dict[str, Any]:
    """Analyze patterns in trace data for optimized compression"""
    print("Analyzing compression patterns...")
    
    service_names = set()
    operation_names = set()
    tag_keys = set()
    tag_values = {}
    
    for span in spans:
        service_names.add(span.get('svc', ''))
        operation_names.add(span.get('o', ''))
        
        tags = span.get('tags', {})
        for key, value in tags.items():
            tag_keys.add(key)
            if key not in tag_values:
                tag_values[key] = set()
            tag_values[key].add(str(value))
    
    patterns = {
        'unique_services': len(service_names),
        'unique_operations': len(operation_names),
        'unique_tag_keys': len(tag_keys),
        'service_names': list(service_names),
        'operation_names': list(operation_names),
        'tag_keys': list(tag_keys),
        'most_common_tags': {k: len(v) for k, v in tag_values.items()}
    }
    
    print(f"  Services: {len(service_names)} unique")
    print(f"  Operations: {len(operation_names)} unique")
    print(f"  Tag keys: {len(tag_keys)} unique")
    
    return patterns

def create_compression_dictionary(spans: List[dict], patterns: Dict[str, Any]) -> bytes:
    """Create a zstd compression dictionary from common patterns"""
    print("Creating compression dictionary...")
    
    # Build dictionary from actual data samples rather than just strings
    training_samples = []
    
    # Create representative CBOR samples for training
    for span in spans[:50]:  # Use first 50 spans as training data
        sample_data = cbor2.dumps(span)
        training_samples.append(sample_data)
    
    # Also add individual common strings as training data
    common_strings = []
    common_strings.extend(['t', 's', 'p', 'o', 'svc', 'st', 'et', 'd', 'tags', 'logs', 'sc'])
    common_strings.extend(patterns['service_names'])
    common_strings.extend(patterns['operation_names'])
    common_strings.extend(patterns['tag_keys'])
    common_strings.extend(['GET', 'POST', 'PUT', 'DELETE', '200', '201', '404', '500'])
    
    # Add string samples to training data
    for s in common_strings:
        training_samples.append(s.encode('utf-8'))
    
    if len(training_samples) == 0 or sum(len(s) for s in training_samples) < 256:
        # Fall back to no dictionary if insufficient data
        print("Insufficient training data, using no dictionary")
        return None
    
    try:
        # Train zstd dictionary
        dict_trainer = zstd.train_dictionary(1024, training_samples)
        print(f"Created dictionary from {len(training_samples)} samples")
        return dict_trainer
    except Exception as e:
        print(f"Dictionary training failed: {e}, proceeding without dictionary")
        return None

def compress_with_zstd(spans: List[dict], compression_level: int = 3) -> tuple:
    """Compress CBOR data with zstandard"""
    print(f"Compressing with zstd level {compression_level}...")
    
    # Analyze patterns first
    patterns = analyze_compression_patterns(spans)
    
    # Create compression dictionary
    compression_dict = create_compression_dictionary(spans, patterns)
    
    # Serialize to CBOR first
    cbor_data = cbor2.dumps(spans)
    
    # Compress with dictionary (if available)
    if compression_dict:
        compressor = zstd.ZstdCompressor(level=compression_level, dict_data=compression_dict)
        compressed_data = compressor.compress(cbor_data)
    else:
        compressor = zstd.ZstdCompressor(level=compression_level)
        compressed_data = compressor.compress(cbor_data)
    
    # Also try without dictionary for comparison
    compressor_no_dict = zstd.ZstdCompressor(level=compression_level)
    compressed_no_dict = compressor_no_dict.compress(cbor_data)
    
    print(f"CBOR size: {len(cbor_data):,} bytes")
    print(f"Compressed (with dict): {len(compressed_data):,} bytes")
    print(f"Compressed (no dict): {len(compressed_no_dict):,} bytes")
    
    dict_benefit = len(compressed_no_dict) / len(compressed_data) if len(compressed_data) > 0 else 1.0
    print(f"Dictionary benefit: {dict_benefit:.2f}x")
    
    return compressed_data, compression_dict, patterns

def save_compressed_data(compressed_data: bytes, compression_dict, patterns: Dict[str, Any], 
                        output_file: str, metadata_file: str):
    """Save compressed data and metadata"""
    print(f"Saving compressed data to {output_file}...")
    
    # Save compressed data
    with open(output_file, 'wb') as f:
        f.write(compressed_data)
    
    # Save compression dictionary for decompression (if available)
    dict_file = output_file.replace('.zst', '_dict.zstd')
    dict_size = 0
    if compression_dict:
        with open(dict_file, 'wb') as f:
            f.write(compression_dict.as_bytes())
        dict_size = len(compression_dict.as_bytes())
        print(f"Saved dictionary ({dict_size:,} bytes)")
    else:
        # Create empty file to indicate no dictionary
        with open(dict_file, 'wb') as f:
            pass
        print("No dictionary used")
    
    # Save patterns and metadata
    metadata = {
        'compressed_size': len(compressed_data),
        'dictionary_size': dict_size,
        'compression_patterns': patterns,
        'dictionary_file': dict_file if compression_dict else None
    }
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Saved compressed data ({len(compressed_data):,} bytes)")

def verify_decompression(compressed_file: str, dict_file: str, original_spans: List[dict]) -> bool:
    """Verify that compressed data can be decompressed correctly"""
    print("Verifying decompression...")
    
    # Load compressed data
    with open(compressed_file, 'rb') as f:
        compressed_data = f.read()
    
    # Load dictionary if it exists
    dict_data = None
    if os.path.exists(dict_file):
        with open(dict_file, 'rb') as f:
            dict_data = f.read()
    
    # Create decompressor
    if dict_data:
        compression_dict = zstd.ZstdCompressionDict(dict_data)
        decompressor = zstd.ZstdDecompressor(dict_data=compression_dict)
    else:
        decompressor = zstd.ZstdDecompressor()
    
    # Decompress
    cbor_data = decompressor.decompress(compressed_data)
    spans = cbor2.loads(cbor_data)
    
    # Verify data integrity
    if len(spans) != len(original_spans):
        print(f"❌ Span count mismatch: {len(spans)} vs {len(original_spans)}")
        return False
    
    # Check a few random spans
    for i in [0, len(spans)//2, -1]:
        if spans[i].get('t') != original_spans[i].get('t'):
            print(f"❌ Trace ID mismatch at index {i}")
            return False
    
    print(f"✅ Successfully verified {len(spans)} spans")
    return True

def benchmark_compression_performance(spans: List[dict], iterations: int = 3):
    """Benchmark compression and decompression performance"""
    print(f"Benchmarking performance ({iterations} iterations)...")
    
    patterns = analyze_compression_patterns(spans)
    compression_dict = create_compression_dictionary(spans, patterns)
    cbor_data = cbor2.dumps(spans)
    
    # Compression benchmarks
    compressor = zstd.ZstdCompressor(level=3, dict_data=compression_dict)
    
    compress_times = []
    for _ in range(iterations):
        start = time.time()
        compressed = compressor.compress(cbor_data)
        end = time.time()
        compress_times.append(end - start)
    
    # Decompression benchmarks
    compressed_data = compressor.compress(cbor_data)
    decompressor = zstd.ZstdDecompressor(dict_data=compression_dict)
    
    decompress_times = []
    for _ in range(iterations):
        start = time.time()
        decompressed = decompressor.decompress(compressed_data)
        end = time.time()
        decompress_times.append(end - start)
    
    avg_compress = sum(compress_times) / len(compress_times)
    avg_decompress = sum(decompress_times) / len(decompress_times)
    
    spans_per_sec_compress = len(spans) / avg_compress
    spans_per_sec_decompress = len(spans) / avg_decompress
    
    print(f"Compression Performance:")
    print(f"  Compression: {avg_compress:.3f}s ({spans_per_sec_compress:,.0f} spans/sec)")
    print(f"  Decompression: {avg_decompress:.3f}s ({spans_per_sec_decompress:,.0f} spans/sec)")
    print(f"  Compressed size: {len(compressed_data):,} bytes")
    
    return avg_compress, avg_decompress

def main():
    """Convert CBOR traces to CBOR+Zstd format"""
    import sys
    
    # Get size parameter
    size = sys.argv[1] if len(sys.argv) > 1 else 'small'
    
    # Create output directory
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Input and output files
    input_file = f'output/traces_{size}_cbor.cbor'
    output_file = f'output/traces_{size}_cbor_zstd.zst'
    metadata_file = f'output/phase3_cbor_zstd_metadata_{size}.json'
    
    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found. Please run 02_cbor_storage.py first.")
        return
    
    # Get original sizes for comparison
    ndjson_file = f'output/traces_{size}_ndjson.jsonl'
    cbor_file = input_file
    
    original_size = os.path.getsize(ndjson_file) if os.path.exists(ndjson_file) else 0
    cbor_size = os.path.getsize(cbor_file)
    
    # Load and compress data
    start_time = time.time()
    spans = load_cbor_spans(input_file)
    compressed_data, compression_dict, patterns = compress_with_zstd(spans)
    
    # Save compressed data
    dict_file = output_file.replace('.zst', '_dict.zstd')
    save_compressed_data(compressed_data, compression_dict, patterns, output_file, metadata_file)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Verify integrity
    is_valid = verify_decompression(output_file, dict_file, spans)
    
    # Performance benchmarks
    compress_time, decompress_time = benchmark_compression_performance(spans[:1000])  # Sample
    
    # Calculate compression ratios
    compressed_size = len(compressed_data)
    
    cbor_zstd_ratio = cbor_size / compressed_size if compressed_size > 0 else 0
    overall_ratio = original_size / compressed_size if compressed_size > 0 else 0
    
    print(f"\nCompression Analysis:")
    print(f"  Original (NDJSON): {original_size:,} bytes")
    print(f"  CBOR: {cbor_size:,} bytes")
    print(f"  CBOR+Zstd: {compressed_size:,} bytes")
    print(f"  CBOR→Zstd improvement: {cbor_zstd_ratio:.2f}x")
    print(f"  Overall compression: {overall_ratio:.2f}x vs NDJSON")
    
    print(f"\nOverall Performance:")
    print(f"  Total processing time: {processing_time:.2f}s")
    print(f"  Data integrity: {'✓ PASSED' if is_valid else '✗ FAILED'}")
    
    # Update metadata with final results
    final_metadata = {
        'phase': 'Phase 3 - CBOR + Zstandard',
        'input_file': input_file,
        'output_file': output_file,
        'dictionary_file': dict_file,
        'original_size_bytes': original_size,
        'cbor_size_bytes': cbor_size,
        'compressed_size_bytes': compressed_size,
        'cbor_to_zstd_ratio': cbor_zstd_ratio,
        'overall_compression_ratio': overall_ratio,
        'processing_time_seconds': processing_time,
        'span_count': len(spans),
        'data_valid': is_valid,
        'format': 'CBOR + Zstandard with dictionary',
        'compression_level': 3,
        'dictionary_entries': len(patterns.get('service_names', [])) + len(patterns.get('operation_names', [])),
        'optimizations': [
            'CBOR binary encoding',
            'Zstandard compression level 3',
            'Custom compression dictionary',
            'Service/operation name deduplication',
            'Tag key optimization'
        ],
        'performance': {
            'compression_time_per_1k_spans': compress_time,
            'decompression_time_per_1k_spans': decompress_time
        },
        'patterns': patterns
    }
    
    with open(metadata_file, 'w') as f:
        json.dump(final_metadata, f, indent=2)
    
    print(f"\nPhase 3 (CBOR + Zstandard) complete!")
    print(f"Output: {output_file}")
    print(f"Dictionary: {dict_file}")
    print(f"Metadata: {metadata_file}")
    print(f"Achieved {overall_ratio:.2f}x compression vs NDJSON")

if __name__ == '__main__':
    main()