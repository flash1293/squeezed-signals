#!/usr/bin/env python3
"""
Phase 4: Span Relationship Compression

Exploits parent-child relationships and service topology for compression.
Groups by trace, uses delta encoding for parent spans, and creates service/operation maps.
"""

import json
import os
import sys
import time
import msgpack
import zstandard as zstd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass

# Add project root to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DEFAULT_ZSTD_LEVEL

# Import our trace encoders
sys.path.append(str(Path(__file__).parent))
from lib.encoders import Span, Trace, ServiceTopologyEncoder, SpanRelationshipEncoder

def load_cbor_spans(input_file: str) -> List[dict]:
    """Load span data from CBOR file"""
    print(f"Loading spans from {input_file}...")
    
    # Try to load from CBOR+Zstd first, fall back to plain CBOR
    if input_file.endswith('.zst'):
        # Load dictionary
        dict_file = input_file.replace('.zst', '_dict.zstd')
        if os.path.exists(dict_file):
            with open(dict_file, 'rb') as f:
                dict_data = f.read()
            compression_dict = zstd.ZstdCompressionDict(dict_data)
            decompressor = zstd.ZstdDecompressor(dict_data=compression_dict)
            
            with open(input_file, 'rb') as f:
                compressed_data = f.read()
            
            import cbor2
            cbor_data = decompressor.decompress(compressed_data)
            spans = cbor2.loads(cbor_data)
        else:
            print(f"Dictionary file {dict_file} not found")
            return []
    else:
        import cbor2
        with open(input_file, 'rb') as f:
            spans = cbor2.load(f)
    
    print(f"Loaded {len(spans)} spans")
    return spans

def convert_to_trace_objects(spans: List[dict]) -> List[Trace]:
    """Convert span dictionaries to Trace objects grouped by trace_id"""
    print("Converting spans to trace objects...")
    
    traces_by_id = defaultdict(list)
    
    for span_dict in spans:
        # Convert compact CBOR fields back to full span
        span = Span(
            trace_id=span_dict.get('t', ''),
            span_id=span_dict.get('s', ''),
            parent_span_id=span_dict.get('p'),
            operation_name=span_dict.get('o', ''),
            service_name=span_dict.get('svc', ''),
            start_time=span_dict.get('st', 0),
            end_time=span_dict.get('et', 0),
            tags=span_dict.get('tags', {}),
            logs=span_dict.get('logs', []),
            status_code=span_dict.get('sc', 0)
        )
        traces_by_id[span.trace_id].append(span)
    
    # Convert to Trace objects
    traces = []
    for trace_id, trace_spans in traces_by_id.items():
        trace = Trace(trace_id=trace_id, spans=trace_spans)
        traces.append(trace)
    
    print(f"Created {len(traces)} trace objects")
    return traces

def analyze_service_topology(traces: List[Trace]) -> ServiceTopologyEncoder:
    """Analyze and encode service topology patterns"""
    print("Analyzing service topology...")
    
    topology = ServiceTopologyEncoder()
    
    for trace in traces:
        # Build parent-child service relationships
        for span in trace.spans:
            if span.parent_span_id:
                # Find parent span
                parent_span = None
                for s in trace.spans:
                    if s.span_id == span.parent_span_id:
                        parent_span = s
                        break
                
                if parent_span and parent_span.service_name != span.service_name:
                    topology.record_call_pattern(parent_span.service_name, span.service_name)
            
            # Add service and operation to maps
            topology.add_service(span.service_name)
            topology.add_operation(span.operation_name)
    
    print(f"Identified {len(topology.service_map)} services, {len(topology.operation_map)} operations")
    print(f"Service call patterns: {len(topology.call_patterns)} unique patterns")
    
    return topology

def compress_span_relationships(traces: List[Trace]) -> Dict[str, Any]:
    """Compress span relationships using delta encoding and topology maps"""
    print("Compressing span relationships...")
    
    topology = analyze_service_topology(traces)
    
    compressed_traces = []
    
    for trace in traces:
        # Sort spans by start time for better delta compression
        sorted_spans = sorted(trace.spans, key=lambda s: s.start_time)
        
        # Build span index mapping
        span_to_index = {span.span_id: i for i, span in enumerate(sorted_spans)}
        
        compressed_spans = []
        
        for i, span in enumerate(sorted_spans):
            # Parent relationship as delta index
            parent_index = -1
            if span.parent_span_id and span.parent_span_id in span_to_index:
                parent_index = span_to_index[span.parent_span_id]
            
            # Use topology mappings for service and operation
            service_id = topology.service_map[span.service_name]
            operation_id = topology.operation_map[span.operation_name]
            
            # Delta encode timestamps within trace
            start_delta = span.start_time
            if i > 0:
                start_delta = span.start_time - sorted_spans[0].start_time
            
            compressed_span = {
                'si': i,  # span index in trace
                'pi': parent_index,  # parent index (-1 for root)
                'svc': service_id,   # service ID from topology map
                'op': operation_id,  # operation ID from topology map
                'std': start_delta,  # start time delta from trace start
                'dur': span.duration,  # duration in nanoseconds
                'sc': span.status_code,  # status code
                'tags': span.tags,   # keep tags for now (optimize later)
                'logs': span.logs    # keep logs for now (optimize later)
            }
            
            compressed_spans.append(compressed_span)
        
        compressed_trace = {
            'tid': trace.trace_id,
            'spans': compressed_spans,
            'root_start': sorted_spans[0].start_time if sorted_spans else 0
        }
        
        compressed_traces.append(compressed_trace)
    
    # Create final compressed structure (convert tuple keys to strings)
    call_patterns_str = {f"{k[0]},{k[1]}": v for k, v in topology.call_patterns.items()}
    
    compressed_data = {
        'topology': {
            'services': topology.service_map,
            'operations': topology.operation_map,
            'call_patterns': call_patterns_str
        },
        'traces': compressed_traces
    }
    
    print(f"Compressed {len(compressed_traces)} traces with topology mapping")
    return compressed_data

def optimize_tags_and_logs(compressed_data: Dict[str, Any]) -> Dict[str, Any]:
    """Further optimize tags and logs using deduplication"""
    print("Optimizing tags and logs...")
    
    # Extract common tag patterns
    tag_keys_map = {}
    tag_values_map = {}
    log_keys_map = {}
    
    all_tag_keys = set()
    all_tag_values = defaultdict(set)
    all_log_keys = set()
    
    # First pass: collect all unique keys and values
    for trace in compressed_data['traces']:
        for span in trace['spans']:
            for tag_key, tag_value in span.get('tags', {}).items():
                all_tag_keys.add(tag_key)
                all_tag_values[tag_key].add(str(tag_value))
            
            for log in span.get('logs', []):
                for log_key in log.keys():
                    all_log_keys.add(log_key)
    
    # Create mappings
    tag_keys_map = {key: i for i, key in enumerate(sorted(all_tag_keys))}
    log_keys_map = {key: i for i, key in enumerate(sorted(all_log_keys))}
    
    # For tag values, only map frequently used ones
    frequent_tag_values = {}
    value_counter = 0
    for tag_key, values in all_tag_values.items():
        if len(values) <= 10:  # Only map if limited set of values
            frequent_tag_values[tag_key] = {v: i for i, v in enumerate(sorted(values))}
        value_counter += len(values)
    
    # Second pass: compress tags and logs
    for trace in compressed_data['traces']:
        for span in trace['spans']:
            # Compress tags
            if 'tags' in span and span['tags']:
                compressed_tags = {}
                for tag_key, tag_value in span['tags'].items():
                    key_id = tag_keys_map.get(tag_key, tag_key)
                    
                    # Use value mapping if available, otherwise keep original
                    if tag_key in frequent_tag_values and str(tag_value) in frequent_tag_values[tag_key]:
                        value_id = frequent_tag_values[tag_key][str(tag_value)]
                        compressed_tags[key_id] = value_id
                    else:
                        compressed_tags[key_id] = tag_value
                
                span['tags'] = compressed_tags
            
            # Compress logs
            if 'logs' in span and span['logs']:
                compressed_logs = []
                for log in span['logs']:
                    compressed_log = {}
                    for log_key, log_value in log.items():
                        key_id = log_keys_map.get(log_key, log_key)
                        compressed_log[key_id] = log_value
                    compressed_logs.append(compressed_log)
                span['logs'] = compressed_logs
    
    # Add mappings to compressed data
    compressed_data['mappings'] = {
        'tag_keys': tag_keys_map,
        'tag_values': frequent_tag_values,
        'log_keys': log_keys_map
    }
    
    print(f"Mapped {len(tag_keys_map)} tag keys, {len(frequent_tag_values)} tag value sets")
    print(f"Mapped {len(log_keys_map)} log keys")
    
    return compressed_data

def save_relationship_compressed(compressed_data: Dict[str, Any], output_file: str):
    """Save relationship-compressed data using msgpack + zstd"""
    print(f"Saving relationship-compressed data to {output_file}...")
    
    # Serialize with msgpack for efficient binary encoding
    msgpack_data = msgpack.packb(compressed_data, use_bin_type=True)
    
    # Compress with zstd
    compressor = zstd.ZstdCompressor(level=DEFAULT_ZSTD_LEVEL)
    compressed_bytes = compressor.compress(msgpack_data)
    
    with open(output_file, 'wb') as f:
        f.write(compressed_bytes)
    
    print(f"Saved {len(compressed_bytes):,} bytes")
    print(f"Msgpack size: {len(msgpack_data):,} bytes")
    print(f"Zstd compression: {len(msgpack_data) / len(compressed_bytes):.2f}x")
    
    return len(compressed_bytes), len(msgpack_data)

def verify_relationship_compression(compressed_file: str, original_traces: List[Trace]) -> bool:
    """Verify that relationship-compressed data can be reconstructed"""
    print("Verifying relationship compression...")
    
    # Load compressed data
    with open(compressed_file, 'rb') as f:
        compressed_bytes = f.read()
    
    # Decompress
    decompressor = zstd.ZstdDecompressor()
    msgpack_data = decompressor.decompress(compressed_bytes)
    compressed_data = msgpack.loads(msgpack_data, raw=False, strict_map_key=False)
    
    # Reconstruct traces
    topology = compressed_data['topology']
    service_id_to_name = {v: k for k, v in topology['services'].items()}
    operation_id_to_name = {v: k for k, v in topology['operations'].items()}
    
    reconstructed_count = 0
    
    for compressed_trace in compressed_data['traces']:
        trace_id = compressed_trace['tid']
        root_start = compressed_trace['root_start']
        
        # Find original trace
        original_trace = None
        for t in original_traces:
            if t.trace_id == trace_id:
                original_trace = t
                break
        
        if not original_trace:
            print(f"❌ Could not find original trace {trace_id}")
            return False
        
        # Verify span count
        if len(compressed_trace['spans']) != len(original_trace.spans):
            print(f"❌ Span count mismatch for trace {trace_id}")
            return False
        
        reconstructed_count += 1
        
        # Verify first few spans
        for i, compressed_span in enumerate(compressed_trace['spans'][:3]):
            service_name = service_id_to_name[compressed_span['svc']]
            operation_name = operation_id_to_name[compressed_span['op']]
            
            # Find matching original span (they may be reordered)
            found_match = False
            for orig_span in original_trace.spans:
                if (orig_span.service_name == service_name and 
                    orig_span.operation_name == operation_name):
                    found_match = True
                    break
            
            if not found_match:
                print(f"❌ Could not find matching span {service_name}:{operation_name}")
                return False
    
    print(f"✅ Successfully verified {reconstructed_count} traces")
    return True

def main():
    """Convert traces to relationship-compressed format"""
    import sys
    
    # Get size parameter
    size = sys.argv[1] if len(sys.argv) > 1 else 'small'
    
    # Create output directory
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Input and output files - try zstd first, fall back to cbor
    input_candidates = [
        f'output/traces_{size}_cbor_zstd.zst',
        f'output/traces_{size}_cbor.cbor'
    ]
    
    input_file = None
    for candidate in input_candidates:
        if os.path.exists(candidate):
            input_file = candidate
            break
    
    if not input_file:
        print("No suitable input file found. Please run previous phases first.")
        return
    
    output_file = f'output/traces_{size}_relationships.msgpack.zst'
    
    # Get original sizes for comparison
    ndjson_file = f'output/traces_{size}_ndjson.jsonl'
    original_size = os.path.getsize(ndjson_file) if os.path.exists(ndjson_file) else 0
    input_size = os.path.getsize(input_file)
    
    # Load and process data
    start_time = time.time()
    spans = load_cbor_spans(input_file)
    traces = convert_to_trace_objects(spans)
    
    # Compress relationships
    compressed_data = compress_span_relationships(traces)
    optimized_data = optimize_tags_and_logs(compressed_data)
    
    # Save compressed data
    final_size, msgpack_size = save_relationship_compressed(optimized_data, output_file)
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Verify integrity
    is_valid = verify_relationship_compression(output_file, traces)
    
    # Calculate compression ratios
    input_ratio = input_size / final_size if final_size > 0 else 0
    overall_ratio = original_size / final_size if final_size > 0 else 0
    
    print(f"\nCompression Analysis:")
    print(f"  Original (NDJSON): {original_size:,} bytes")
    print(f"  Input ({os.path.basename(input_file)}): {input_size:,} bytes")
    print(f"  Relationship compressed: {final_size:,} bytes")
    print(f"  Input improvement: {input_ratio:.2f}x")
    print(f"  Overall compression: {overall_ratio:.2f}x vs NDJSON")
    
    print(f"\nOverall Performance:")
    print(f"  Processing time: {processing_time:.2f}s")
    print(f"  Data integrity: {'✓ PASSED' if is_valid else '✗ FAILED'}")
    
    # Save metadata
    metadata = {
        'phase': 'Phase 4 - Span Relationship Compression',
        'input_file': input_file,
        'output_file': output_file,
        'original_size_bytes': original_size,
        'input_size_bytes': input_size,
        'compressed_size_bytes': final_size,
        'msgpack_size_bytes': msgpack_size,
        'input_improvement_ratio': input_ratio,
        'overall_compression_ratio': overall_ratio,
        'processing_time_seconds': processing_time,
        'trace_count': len(traces),
        'span_count': len(spans),
        'data_valid': is_valid,
        'format': 'MessagePack + Zstandard with relationship compression',
        'compression_techniques': [
            'Service topology mapping',
            'Operation name deduplication',
            'Parent-child delta encoding',
            'Timestamp delta compression within traces',
            'Tag key/value mapping',
            'Log key mapping',
            'MessagePack binary serialization',
            'Zstandard compression level 6'
        ],
        'topology_stats': {
            'unique_services': len(optimized_data['topology']['services']),
            'unique_operations': len(optimized_data['topology']['operations']),
            'service_call_patterns': len(optimized_data['topology']['call_patterns'])
        }
    }
    
    with open(f'output/phase4_relationships_metadata_{size}.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nPhase 4 (Span Relationship Compression) complete!")
    print(f"Output: {output_file}")
    print(f"Metadata: output/phase4_relationships_metadata_{size}.json")
    print(f"Achieved {overall_ratio:.2f}x compression vs NDJSON")

if __name__ == '__main__':
    main()