#!/usr/bin/env python3
"""
Phase 6: Maximum Compression - Drop Order Preservation

This phase achieves maximum compression by eliminating the order mapping overhead.
Instead of preserving the ability to reconstruct the original chronological order,
we accept that timestamps alone will provide approximate ordering.

This is ideal for:
- Long-term archival where original order doesn't matter
- Logs that are indexed externally (Elasticsearch, Splunk)
- Compliance storage with no query requirements
- Maximum cost optimization scenarios

Expected result: 50-60x compression (vs 42x with order preservation)
Trade-off: Cannot reconstruct original chronological order
"""

import json
import time
import pickle
import zstandard as zstd
from pathlib import Path
from typing import Dict, Any
import argparse


def process_log_file(input_file: Path, output_file: Path, metadata_file: Path, strategy: str = 'template_grouped') -> Dict[str, Any]:
    """
    Process Phase 5 data to create Phase 6 (no order preservation)
    
    This takes Phase 5 data and removes the order mapping to achieve maximum compression.
    """
    print(f"Processing Phase 5 data to create maximum compression version...")
    print(f"⚠️  WARNING: Original chronological order will NOT be preserved")
    print(f"   Timestamps will still be available for approximate ordering")
    
    start_time = time.time()
    
    # Load Phase 5 data
    phase5_file = input_file.parent / f"phase5_logs_{input_file.stem.split('_')[-1]}.pkl"
    
    if not phase5_file.exists():
        raise FileNotFoundError(f"Phase 5 output not found: {phase5_file}")
    
    print(f"Loading Phase 5 data from {phase5_file}...")
    
    # Load compressed Phase 5 data
    with open(phase5_file, 'rb') as f:
        compressed_data = f.read()
    
    # Decompress Phase 5 data
    decompressor = zstd.ZstdDecompressor()
    decompressed_data = decompressor.decompress(compressed_data)
    phase5_data = pickle.loads(decompressed_data)
    
    print(f"Phase 5 data loaded: {phase5_data['total_lines']:,} lines with {phase5_data['unique_templates']:,} templates")
    
    # Create Phase 6 data by removing order preservation
    phase6_data = {
        'templates': phase5_data['templates'],
        'encoded_variable_columns': phase5_data['encoded_variable_columns'],
        'line_to_template': phase5_data['line_to_template'],
        'line_variable_counts': phase5_data['line_variable_counts'],
        'template_variable_patterns': phase5_data['template_variable_patterns'],
        'total_lines': phase5_data['total_lines'],
        'unique_templates': phase5_data['unique_templates'],
        'encoding_metadata': phase5_data['encoding_metadata'],
        'ordering_metadata': {
            'strategy': strategy,
            'order_preservation': 'disabled',
            'warning': 'Original chronological order cannot be recovered',
            'timestamp_based_ordering': 'available',
            'phase': 6,
            'description': 'Maximum compression - order mapping dropped for space savings'
        }
    }
    
    # Calculate original size (from Phase 0)
    original_file = input_file.parent / f"logs_{input_file.stem.split('_')[-1]}.log"
    if original_file.exists():
        original_size = original_file.stat().st_size
    else:
        # Fallback: get from Phase 5 metadata
        phase5_metadata_file = input_file.parent / f"phase5_logs_metadata_{input_file.stem.split('_')[-1]}.json"
        if phase5_metadata_file.exists():
            with open(phase5_metadata_file, 'r') as f:
                phase5_metadata = json.load(f)
            original_size = phase5_metadata['original_size_bytes']
        else:
            raise FileNotFoundError("Cannot determine original size")
    
    # Get Phase 5 size for comparison
    phase5_size = phase5_file.stat().st_size
    
    # Serialize Phase 6 data (without order mapping)
    uncompressed_data = pickle.dumps(phase6_data, protocol=pickle.HIGHEST_PROTOCOL)
    uncompressed_size = len(uncompressed_data)
    
    # Apply Zstd Level 6 compression
    print("Applying Zstd Level 6 compression (without order mapping)...")
    compressor = zstd.ZstdCompressor(level=6)
    compressed_data = compressor.compress(uncompressed_data)
    
    # Save compressed data
    with open(output_file, 'wb') as f:
        f.write(compressed_data)
    
    file_size = output_file.stat().st_size
    processing_time = time.time() - start_time
    
    # Calculate compression ratios
    overall_compression_ratio = original_size / file_size
    structure_compression_ratio = original_size / uncompressed_size
    zstd_compression_ratio = uncompressed_size / file_size
    
    # Compare with Phase 5
    phase5_improvement = phase5_size / file_size if file_size > 0 else 1.0
    space_saved_vs_phase5 = phase5_size - file_size
    
    # Create metadata
    metadata = {
        'phase': 6,
        'phase_name': 'Maximum Compression - Drop Order Preservation',
        'strategy': strategy,
        'lines_processed': phase6_data['total_lines'],
        'unique_templates': phase6_data['unique_templates'],
        'template_reuse_ratio': phase6_data['total_lines'] / phase6_data['unique_templates'],
        'original_size_bytes': original_size,
        'uncompressed_size_bytes': uncompressed_size,
        'file_size_bytes': file_size,
        'structure_compression_ratio': structure_compression_ratio,
        'zstd_compression_ratio': zstd_compression_ratio,
        'overall_compression_ratio': overall_compression_ratio,
        'phase5_size_bytes': phase5_size,
        'phase6_improvement_ratio': phase5_improvement,
        'space_saved_vs_phase5_bytes': space_saved_vs_phase5,
        'space_saved_vs_phase5_percent': (space_saved_vs_phase5 / phase5_size * 100) if phase5_size > 0 else 0,
        'processing_time_seconds': processing_time,
        'optimizations_stack': {
            'phase1_baseline': True,
            'phase2_zstd_level6': True,
            'phase3_template_extraction': True,
            'phase4_advanced_variable_encoding': True,
            'phase5_smart_row_ordering': True,
            'phase6_drop_order_preservation': True
        },
        'ordering_stats': {
            'preserved_original_order': False,
            'ordering_overhead_bytes': 0,
            'strategy_applied': strategy,
            'order_preservation_enabled': False,
            'timestamp_based_ordering_available': True,
            'reconstruction_capability': 'Approximate only (via timestamps)'
        },
        'trade_offs': {
            'space_savings': f'{overall_compression_ratio:.1f}x compression',
            'capability_loss': 'Cannot reconstruct original chronological order',
            'workaround': 'Use timestamps for approximate time-based ordering',
            'use_case': 'Long-term archival, external indexing, maximum cost optimization'
        }
    }
    
    # Save metadata
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n📊 Phase 6 Results:")
    print(f"  Lines processed: {metadata['lines_processed']:,}")
    print(f"  Unique templates: {metadata['unique_templates']:,}")
    print(f"  Original size: {original_size:,} bytes ({original_size/1024:.1f} KB)")
    print(f"  Phase 5 size: {phase5_size:,} bytes ({phase5_size/1024:.1f} KB)")
    print(f"  Phase 6 size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    print(f"  Overall compression: {overall_compression_ratio:.2f}x")
    print(f"  Improvement over Phase 5: {phase5_improvement:.2f}x")
    print(f"  Space saved vs Phase 5: {space_saved_vs_phase5:,} bytes ({metadata['space_saved_vs_phase5_percent']:.1f}%)")
    print(f"  Processing time: {processing_time:.2f} seconds")
    
    return metadata


def verify_data_integrity(phase6_file: Path) -> bool:
    """
    Verify Phase 6 data can be loaded and has expected structure
    (Note: Cannot verify reconstruction since order is dropped)
    """
    print("🔍 Verifying Phase 6 data integrity...")
    
    try:
        # Load Phase 6 data
        with open(phase6_file, 'rb') as f:
            compressed_data = f.read()
        
        decompressor = zstd.ZstdDecompressor()
        decompressed_data = decompressor.decompress(compressed_data)
        phase6_data = pickle.loads(decompressed_data)
        
        # Verify structure
        required_keys = [
            'templates', 'encoded_variable_columns', 'line_to_template',
            'line_variable_counts', 'template_variable_patterns',
            'total_lines', 'unique_templates', 'encoding_metadata',
            'ordering_metadata'
        ]
        
        for key in required_keys:
            if key not in phase6_data:
                print(f"❌ Missing required key: {key}")
                return False
        
        # Verify ordering metadata
        ordering_meta = phase6_data['ordering_metadata']
        if ordering_meta.get('order_preservation') != 'disabled':
            print(f"❌ Order preservation should be disabled")
            return False
        
        if 'original_order_mapping_compressed' in ordering_meta:
            print(f"❌ Order mapping should not be present in Phase 6")
            return False
        
        print(f"✅ Phase 6 data integrity verified")
        print(f"   Total lines: {phase6_data['total_lines']:,}")
        print(f"   Unique templates: {phase6_data['unique_templates']:,}")
        print(f"   Order preservation: {ordering_meta['order_preservation']}")
        print(f"   Timestamp-based ordering: {ordering_meta['timestamp_based_ordering']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False


def compare_with_phase5(size: str):
    """Compare Phase 6 results with Phase 5 to show space savings"""
    print("\n📊 Phase 5 vs Phase 6 Comparison:")
    print("=" * 60)
    
    phase5_metadata_file = Path(f'output/phase5_logs_metadata_{size}.json')
    phase6_metadata_file = Path(f'output/phase6_logs_metadata_{size}.json')
    
    if not phase5_metadata_file.exists() or not phase6_metadata_file.exists():
        print("❌ Cannot compare - metadata files not found")
        return
    
    with open(phase5_metadata_file, 'r') as f:
        phase5_meta = json.load(f)
    
    with open(phase6_metadata_file, 'r') as f:
        phase6_meta = json.load(f)
    
    print(f"\nMetric                          Phase 5           Phase 6           Improvement")
    print("-" * 80)
    print(f"File size:                      {phase5_meta['file_size_bytes']:>10,} bytes  {phase6_meta['file_size_bytes']:>10,} bytes  -{phase6_meta['space_saved_vs_phase5_bytes']:>8,} bytes")
    print(f"Compression ratio:              {phase5_meta['overall_compression_ratio']:>10.2f}x       {phase6_meta['overall_compression_ratio']:>10.2f}x       +{phase6_meta['overall_compression_ratio']-phase5_meta['overall_compression_ratio']:>7.2f}x")
    print(f"Order preservation:             {'Yes':>10}         {'No':>10}         Dropped")
    print(f"Order mapping overhead:         {phase5_meta['ordering_stats'].get('ordering_overhead_bytes', 0):>10,} bytes  {phase6_meta['ordering_stats']['ordering_overhead_bytes']:>10,} bytes  -{phase5_meta['ordering_stats'].get('ordering_overhead_bytes', 0):>8,} bytes")
    print(f"Chronological reconstruction:   {'Possible':>10}         {'Not possible':>10}         Trade-off")
    print(f"Timestamp-based ordering:       {'Available':>10}         {'Available':>10}         Retained")
    
    print(f"\n🎯 Space Savings:")
    print(f"   Phase 6 is {phase6_meta['space_saved_vs_phase5_percent']:.1f}% smaller than Phase 5")
    print(f"   Additional compression: {phase6_meta['phase6_improvement_ratio']:.2f}x")
    print(f"   Bytes saved: {phase6_meta['space_saved_vs_phase5_bytes']:,}")


def main():
    """Main function to process logs with Phase 6 (maximum compression)"""
    parser = argparse.ArgumentParser(
        description='Phase 6: Maximum Compression - Drop Order Preservation',
        epilog='WARNING: This phase drops the ability to reconstruct original chronological order'
    )
    parser.add_argument('--size', choices=['small', 'big', 'huge'], default='small',
                       help='Dataset size to process (default: small)')
    parser.add_argument('--verify', action='store_true',
                       help='Verify data integrity after compression')
    parser.add_argument('--compare', action='store_true',
                       help='Compare Phase 6 results with Phase 5')
    parser.add_argument('--strategy', default='template_grouped',
                       choices=['template_grouped', 'timestamp_clustered', 'variable_clustered', 'hybrid_optimal'],
                       help='Ordering strategy used in Phase 5 (for metadata)')
    
    args = parser.parse_args()
    
    # Setup paths
    input_file = Path(f'output/logs_{args.size}.log')
    output_file = Path(f'output/phase6_logs_{args.size}.pkl')
    metadata_file = Path(f'output/phase6_logs_metadata_{args.size}.json')
    
    # Ensure output directory exists
    output_file.parent.mkdir(exist_ok=True)
    
    # Check input file exists
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        print(f"   Run Phase 0 first: python 00_generate_data.py --size {args.size}")
        return 1
    
    # Check Phase 5 exists
    phase5_file = Path(f'output/phase5_logs_{args.size}.pkl')
    if not phase5_file.exists():
        print(f"❌ Phase 5 output not found: {phase5_file}")
        print(f"   Run Phase 5 first: python 05_smart_row_ordering.py --size {args.size}")
        return 1
    
    print("=" * 60)
    print(f"Phase 6: Maximum Compression - Drop Order ({args.size})")
    print("=" * 60)
    print(f"Input: {input_file}")
    print(f"Phase 5: {phase5_file}")
    print(f"Output: {output_file}")
    
    try:
        # Process the file
        metadata = process_log_file(input_file, output_file, metadata_file, args.strategy)
        
        # Verify if requested
        if args.verify:
            print("\n" + "=" * 60)
            if not verify_data_integrity(output_file):
                print("❌ Data integrity verification failed!")
                return 1
        
        # Compare with Phase 5 if requested
        if args.compare:
            compare_with_phase5(args.size)
        
        print("\n📊 Phase 6 Maximum Compression Results:")
        print(f"  Lines processed: {metadata['lines_processed']:,}")
        print(f"  Unique templates: {metadata['unique_templates']:,}")
        print(f"  Original size: {metadata['original_size_bytes']:,} bytes ({metadata['original_size_bytes']/1024:.1f} KB)")
        print(f"  Phase 5 size: {metadata['phase5_size_bytes']:,} bytes ({metadata['phase5_size_bytes']/1024:.1f} KB)")
        print(f"  Phase 6 size: {metadata['file_size_bytes']:,} bytes ({metadata['file_size_bytes']/1024:.1f} KB)")
        print(f"  Overall compression: {metadata['overall_compression_ratio']:.2f}x")
        print(f"  Improvement over Phase 5: {metadata['phase6_improvement_ratio']:.2f}x")
        print(f"  Space saved: {(1 - metadata['file_size_bytes']/metadata['original_size_bytes'])*100:.1f}%")
        print(f"  Processing time: {metadata['processing_time_seconds']:.2f} seconds")
        
        print(f"\n⚠️  Trade-offs:")
        print(f"  ✅ Maximum compression achieved")
        print(f"  ✅ Timestamps still available for ordering")
        print(f"  ❌ Cannot reconstruct original chronological order")
        print(f"  ❌ Order mapping removed (saves {metadata['space_saved_vs_phase5_bytes']:,} bytes)")
        
        print(f"\n✅ Phase 6 completed successfully!")
        print(f"   Output: {output_file}")
        print(f"   Metadata: {metadata_file}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error in Phase 6 processing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
