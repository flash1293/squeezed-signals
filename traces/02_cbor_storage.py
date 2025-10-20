#!/usr/bin/env python3
"""
Phase 2: CBOR Binary Encoding

Applies binary serialization for basic size reduction.
CBOR encoding for all span data, binary timestamps, compact field names.
"""

import json
import os
import time
import cbor2
from pathlib import Path
from typing import List

def load_ndjson_spans(input_file: str) -> List[dict]:
    """Load span data from NDJSON file"""
    spans = []
    
    print(f"Loading NDJSON spans from {input_file}...")
    
    with open(input_file, 'r') as f:
        for line in f:
            if line.strip():
                span = json.loads(line)
                spans.append(span)
    
    print(f"Loaded {len(spans)} spans")
    return spans

def convert_to_cbor(spans: List[dict], output_file: str):
    """Convert spans to CBOR binary format"""
    print(f"Converting to CBOR format: {output_file}")
    
    # Optimize field names for space efficiency
    field_mapping = {
        'trace_id': 't',
        'span_id': 's', 
        'parent_span_id': 'p',
        'operation_name': 'o',
        'service_name': 'svc',
        'start_time': 'st',
        'end_time': 'et',
        'duration_ns': 'd',
        'tags': 'tags',
        'logs': 'logs',
        'status_code': 'sc',
        'status': 'stat'
    }
    
    # Convert spans to compact format
    compact_spans = []
    
    for span in spans:
        compact_span = {}
        for original_field, compact_field in field_mapping.items():
            if original_field in span:
                value = span[original_field]
                
                # Additional optimizations
                if original_field == 'status' and value in ['OK', 'ERROR']:
                    # Skip status string if we have status_code
                    continue
                elif original_field in ['start_time', 'end_time', 'duration_ns']:
                    # Keep as integers for binary efficiency
                    compact_span[compact_field] = int(value) if value is not None else None
                else:
                    compact_span[compact_field] = value
        
        compact_spans.append(compact_span)
    
    # Write CBOR data
    with open(output_file, 'wb') as f:
        cbor2.dump(compact_spans, f)
    
    file_size = os.path.getsize(output_file)
    print(f"Converted {len(spans):,} spans to CBOR ({file_size:,} bytes)")
    return file_size

def analyze_cbor_compression(original_size: int, cbor_size: int):
    """Analyze CBOR compression characteristics"""
    compression_ratio = original_size / cbor_size if cbor_size > 0 else 0
    space_saved = original_size - cbor_size
    space_saved_pct = (space_saved / original_size * 100) if original_size > 0 else 0
    
    print(f"\nCBOR Compression Analysis:")
    print(f"  Original (NDJSON): {original_size:,} bytes ({original_size/1024/1024:.2f} MB)")
    print(f"  CBOR binary: {cbor_size:,} bytes ({cbor_size/1024/1024:.2f} MB)")
    print(f"  Space saved: {space_saved:,} bytes ({space_saved_pct:.1f}%)")
    print(f"  Compression ratio: {compression_ratio:.2f}x")
    
    return compression_ratio

def verify_cbor_data(cbor_file: str, sample_size: int = 10):
    """Verify CBOR data integrity by loading and checking samples"""
    print(f"\nVerifying CBOR data integrity...")
    
    with open(cbor_file, 'rb') as f:
        spans = cbor2.load(f)
    
    print(f"Successfully loaded {len(spans)} spans from CBOR")
    
    # Check sample spans
    print(f"\nSample spans (first {min(sample_size, len(spans))}):")
    for i, span in enumerate(spans[:sample_size]):
        trace_id = span.get('t', 'unknown')
        service = span.get('svc', 'unknown')
        operation = span.get('o', 'unknown')
        duration = span.get('d', 0)
        status = span.get('sc', 0)
        
        print(f"  {i+1}. {service}:{operation} (trace: {trace_id[:8]}..., "
              f"duration: {duration/1_000_000:.1f}ms, status: {status})")
    
    # Verify data types and structure
    required_fields = ['t', 's', 'svc', 'o', 'st', 'et', 'd', 'sc']
    valid_spans = 0
    
    for span in spans:
        if all(field in span for field in required_fields):
            valid_spans += 1
    
    validity_pct = (valid_spans / len(spans) * 100) if spans else 0
    print(f"\nData validation: {valid_spans}/{len(spans)} spans valid ({validity_pct:.1f}%)")
    
    return len(spans), valid_spans == len(spans)

def benchmark_cbor_performance(spans: List[dict], iterations: int = 3):
    """Benchmark CBOR encoding/decoding performance"""
    print(f"\nBenchmarking CBOR performance ({iterations} iterations)...")
    
    # Encoding benchmark
    encode_times = []
    for i in range(iterations):
        start = time.time()
        cbor_data = cbor2.dumps(spans)
        end = time.time()
        encode_times.append(end - start)
    
    avg_encode_time = sum(encode_times) / len(encode_times)
    
    # Decoding benchmark
    cbor_data = cbor2.dumps(spans)
    decode_times = []
    for i in range(iterations):
        start = time.time()
        decoded_spans = cbor2.loads(cbor_data)
        end = time.time()
        decode_times.append(end - start)
    
    avg_decode_time = sum(decode_times) / len(decode_times)
    
    spans_per_sec_encode = len(spans) / avg_encode_time
    spans_per_sec_decode = len(spans) / avg_decode_time
    
    print(f"CBOR Performance:")
    print(f"  Encoding: {avg_encode_time:.3f}s ({spans_per_sec_encode:,.0f} spans/sec)")
    print(f"  Decoding: {avg_decode_time:.3f}s ({spans_per_sec_decode:,.0f} spans/sec)")
    print(f"  Data size: {len(cbor_data):,} bytes")
    
    return avg_encode_time, avg_decode_time

def main():
    """Convert NDJSON traces to CBOR binary format"""
    import sys
    
    # Get size parameter
    size = sys.argv[1] if len(sys.argv) > 1 else 'small'
    
    # Create output directory
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Input and output files
    input_file = f'output/traces_{size}_ndjson.jsonl'
    output_file = f'output/traces_{size}_cbor.cbor'
    
    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found. Please run 01_ndjson_storage.py first.")
        return
    
    # Get original file size for comparison
    original_size = os.path.getsize(input_file)
    
    # Load and convert data
    start_time = time.time()
    spans = load_ndjson_spans(input_file)
    cbor_size = convert_to_cbor(spans, output_file)
    end_time = time.time()
    
    # Analyze compression
    compression_ratio = analyze_cbor_compression(original_size, cbor_size)
    
    # Verify data integrity
    span_count, is_valid = verify_cbor_data(output_file)
    
    # Performance benchmarks
    encode_time, decode_time = benchmark_cbor_performance(spans[:1000])  # Sample for performance
    
    # Overall performance metrics
    processing_time = end_time - start_time
    print(f"\nOverall Performance:")
    print(f"  Total processing time: {processing_time:.2f}s")
    print(f"  Compression ratio: {compression_ratio:.2f}x vs NDJSON")
    print(f"  Data integrity: {'✓ PASSED' if is_valid else '✗ FAILED'}")
    
    # Save metadata
    metadata = {
        'phase': 'Phase 2 - CBOR Binary Encoding',
        'input_file': input_file,
        'output_file': output_file,
        'original_size_bytes': original_size,
        'compressed_size_bytes': cbor_size,
        'compression_ratio': compression_ratio,
        'processing_time_seconds': processing_time,
        'span_count': span_count,
        'data_valid': is_valid,
        'format': 'CBOR binary',
        'optimizations': [
            'Binary encoding',
            'Compact field names',
            'Integer timestamps',
            'Removed redundant status field'
        ],
        'performance': {
            'encoding_time_per_1k_spans': encode_time,
            'decoding_time_per_1k_spans': decode_time
        }
    }
    
    with open(f'output/phase2_cbor_metadata_{size}.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nPhase 2 (CBOR Binary Encoding) complete!")
    print(f"Output: {output_file}")
    print(f"Metadata: output/phase2_cbor_metadata_{size}.json")
    print(f"Achieved {compression_ratio:.2f}x compression vs NDJSON")

if __name__ == '__main__':
    main()