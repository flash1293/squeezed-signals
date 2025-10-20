#!/usr/bin/env python3
"""
Phase 1: NDJSON Baseline Storage

Establishes baseline with standard NDJSON trace format.
One span per line, human-readable timestamps, complete metadata preservation.
"""

import json
import os
import time
from pathlib import Path
from typing import List

def load_trace_data(input_file: str) -> List[dict]:
    """Load trace data from JSON file"""
    traces = []
    
    print(f"Loading trace data from {input_file}...")
    
    with open(input_file, 'r') as f:
        for line in f:
            if line.strip():
                trace_data = json.loads(line)
                traces.append(trace_data)
    
    print(f"Loaded {len(traces)} traces")
    return traces

def convert_to_ndjson_spans(traces: List[dict], output_file: str):
    """Convert traces to NDJSON format with one span per line"""
    print(f"Converting to NDJSON format: {output_file}")
    
    total_spans = 0
    
    with open(output_file, 'w') as f:
        for trace in traces:
            for span in trace['spans']:
                # Convert to human-readable format
                span_record = {
                    'trace_id': span['trace_id'],
                    'span_id': span['span_id'],
                    'parent_span_id': span['parent_span_id'],
                    'operation_name': span['operation_name'],
                    'service_name': span['service_name'],
                    'start_time': span['start_time'],
                    'end_time': span['end_time'], 
                    'duration_ns': span['duration'],
                    'tags': span['tags'],
                    'logs': span['logs'],
                    'status_code': span['status_code'],
                    'status': 'OK' if span['status_code'] == 0 else 'ERROR'
                }
                
                f.write(json.dumps(span_record) + '\n')
                total_spans += 1
    
    file_size = os.path.getsize(output_file)
    print(f"Converted {total_spans:,} spans to NDJSON ({file_size:,} bytes)")
    return file_size

def analyze_ndjson_characteristics(input_file: str):
    """Analyze characteristics of NDJSON trace data"""
    print(f"\nAnalyzing NDJSON characteristics...")
    
    total_spans = 0
    services = set()
    operations = set()
    trace_ids = set()
    error_count = 0
    total_duration = 0
    
    with open(input_file, 'r') as f:
        for line in f:
            if line.strip():
                span = json.loads(line)
                total_spans += 1
                
                services.add(span['service_name'])
                operations.add(span['operation_name'])
                trace_ids.add(span['trace_id'])
                
                if span['status_code'] != 0:
                    error_count += 1
                
                total_duration += span['duration_ns']
    
    avg_duration = total_duration / total_spans if total_spans > 0 else 0
    error_rate = error_count / total_spans if total_spans > 0 else 0
    
    print(f"NDJSON Analysis:")
    print(f"  Total spans: {total_spans:,}")
    print(f"  Unique traces: {len(trace_ids):,}")
    print(f"  Unique services: {len(services):,}")
    print(f"  Unique operations: {len(operations):,}")
    print(f"  Error rate: {error_rate:.2%}")
    print(f"  Average span duration: {avg_duration/1_000_000:.1f}ms")
    
    print(f"\nTop services:")
    service_counts = {}
    with open(input_file, 'r') as f:
        for line in f:
            if line.strip():
                span = json.loads(line)
                service = span['service_name']
                service_counts[service] = service_counts.get(service, 0) + 1
    
    for service, count in sorted(service_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {service}: {count:,} spans")

def main():
    """Convert traces to NDJSON baseline format"""
    import sys
    
    # Get size parameter
    size = sys.argv[1] if len(sys.argv) > 1 else 'small'
    
    # Create output directory
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Input and output files
    input_file = f'output/traces_{size}.json'
    output_file = f'output/traces_{size}_ndjson.jsonl'
    
    if not os.path.exists(input_file):
        print(f"Input file {input_file} not found. Please run 00_generate_data.py first.")
        return
    
    # Load and convert data
    start_time = time.time()
    traces = load_trace_data(input_file)
    file_size = convert_to_ndjson_spans(traces, output_file)
    end_time = time.time()
    
    # Analyze characteristics
    analyze_ndjson_characteristics(output_file)
    
    # Performance metrics
    processing_time = end_time - start_time
    print(f"\nPerformance:")
    print(f"  Processing time: {processing_time:.2f}s")
    print(f"  File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
    print(f"  Compression ratio: 1.0x (baseline)")
    
    # Save metadata
    metadata = {
        'phase': 'Phase 1 - NDJSON Baseline',
        'input_file': input_file,
        'output_file': output_file,
        'file_size_bytes': file_size,
        'processing_time_seconds': processing_time,
        'compression_ratio': 1.0,
        'format': 'NDJSON (one span per line)',
        'characteristics': {
            'human_readable': True,
            'preserves_all_metadata': True,
            'streaming_friendly': True,
            'compression': 'none'
        }
    }
    
    with open(f'output/phase1_ndjson_metadata_{size}.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nPhase 1 (NDJSON Baseline) complete!")
    print(f"Output: {output_file}")
    print(f"Metadata: output/phase1_ndjson_metadata_{size}.json")

if __name__ == '__main__':
    main()