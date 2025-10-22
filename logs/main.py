#!/usr/bin/env python3
"""
Log Compression Pipeline - Main Runner

This script runs all phases of the log compression pipeline, similar to the
metrics and traces projects. It automatically runs through all phases while
respecting caches and providing comprehensive results.

Expected compression evolution:
- Phase 0: Real-world log data generation from LogHub
- Phase 1: Plain text baseline (1.00x)
- Phase 2: Zstd compression (11-19x)
- Phase 3: Template extraction (TBD)
- Phase 4: Columnar variable encoding (TBD)
- Phase 5: Smart ordering optimization (TBD)
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

def run_phase_0(size: str, force: bool = False) -> bool:
    """Run Phase 0: Generate realistic log data from LogHub"""
    print("🔄 Phase 0: Generate Realistic Log Data")
    print("-" * 50)
    
    output_file = Path(f"output/logs_{size}.log")
    metadata_file = Path(f"output/phase0_logs_metadata_{size}.json")
    
    # Check if cached and not forcing regeneration
    if output_file.exists() and metadata_file.exists() and not force:
        print(f"✅ Phase 0 already completed (cached)")
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        print(f"   Dataset: {metadata.get('dataset', 'Unknown')}")
        print(f"   Lines: {metadata.get('analysis', {}).get('total_lines', 'Unknown'):,}")
        print(f"   Size: {metadata.get('analysis', {}).get('file_size_bytes', 0)/1024/1024:.1f} MB")
        return True
    
    try:
        # Import and run phase 0
        import importlib.util
        spec = importlib.util.spec_from_file_location("phase0", "00_generate_data.py")
        phase0_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(phase0_module)
        
        result = phase0_module.generate_log_data(size, use_full_datasets=True)
        
        if result:
            print("✅ Phase 0 completed successfully")
            return True
        else:
            print("❌ Phase 0 failed")
            return False
            
    except Exception as e:
        print(f"❌ Phase 0 failed: {e}")
        return False


def run_phase_1(size: str) -> bool:
    """Run Phase 1: Plain text baseline storage"""
    print("\n🔄 Phase 1: Plain Text Baseline Storage")
    print("-" * 50)
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("phase1", "01_plain_text_baseline.py")
        phase1_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(phase1_module)
        
        input_file = Path(f'output/logs_{size}.log')
        output_file = Path(f'output/phase1_logs_{size}.log')
        metadata_file = Path(f'output/phase1_logs_metadata_{size}.json')
        
        # Check if input exists
        if not input_file.exists():
            print(f"❌ Input file not found: {input_file}")
            return False
        
        # Run processing
        metadata = phase1_module.process_log_file(input_file, output_file, metadata_file)
        
        print(f"✅ Phase 1 completed successfully")
        print(f"   Compression ratio: {metadata['compression_ratio']:.2f}x")
        return True
        
    except Exception as e:
        print(f"❌ Phase 1 failed: {e}")
        return False


def run_phase_2(size: str) -> bool:
    """Run Phase 2: Zstd compression"""
    print("\n🔄 Phase 2: Zstd Compression (Level 22)")
    print("-" * 50)
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("phase2", "02_zstd_compression.py")
        phase2_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(phase2_module)
        
        input_file = Path(f'output/logs_{size}.log')
        output_file = Path(f'output/phase2_logs_{size}.zst')
        metadata_file = Path(f'output/phase2_logs_metadata_{size}.json')
        
        # Check if input exists
        if not input_file.exists():
            print(f"❌ Input file not found: {input_file}")
            return False
        
        # Run processing with level 22
        metadata = phase2_module.process_log_file(input_file, output_file, metadata_file, compression_level=22)
        
        print(f"✅ Phase 2 completed successfully")
        print(f"   Compression ratio: {metadata['compression_ratio']:.2f}x")
        print(f"   Space saved: {(1 - metadata['file_size_bytes']/metadata['original_size_bytes'])*100:.1f}%")
        return True
        
    except Exception as e:
        print(f"❌ Phase 2 failed: {e}")
        return False


def run_phase_3(size: str) -> bool:
    """Run Phase 3: Template extraction + columnar storage"""
    print("\n🔄 Phase 3: Template Extraction + Columnar Storage")
    print("-" * 50)
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("phase3", "03_template_extraction.py")
        phase3_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(phase3_module)
        
        input_file = Path(f'output/logs_{size}.log')
        output_file = Path(f'output/phase3_logs_{size}.pkl')
        metadata_file = Path(f'output/phase3_logs_metadata_{size}.json')
        
        # Check if input exists
        if not input_file.exists():
            print(f"❌ Input file not found: {input_file}")
            return False
        
        # Run processing
        metadata = phase3_module.process_log_file(input_file, output_file, metadata_file)
        
        print(f"✅ Phase 3 completed successfully")
        print(f"   Overall compression ratio: {metadata['overall_compression_ratio']:.2f}x")
        print(f"   Template reuse: {metadata['template_reuse_ratio']:.1f}x")
        print(f"   Space saved: {(1 - metadata['file_size_bytes']/metadata['original_size_bytes'])*100:.1f}%")
        return True
        
    except Exception as e:
        print(f"❌ Phase 3 failed: {e}")
        return False


def print_comprehensive_results(sizes: List[str]):
    """Print comprehensive results across all phases and sizes"""
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE LOG COMPRESSION RESULTS")
    print("=" * 70)
    
    phases = [
        ('Phase 1 (Baseline)', 'phase1'),
        ('Phase 2 (Zstd L22)', 'phase2'),
        ('Phase 3 (Template+Col)', 'phase3'),
    ]
    
    print(f"{'Phase':<20} {'Dataset':<8} {'Lines':<8} {'Original':<12} {'Compressed':<12} {'Ratio':<8} {'Saved':<8}")
    print("-" * 70)
    
    for size in sizes:
        dataset_names = {'small': 'Apache', 'big': 'HDFS', 'huge': 'OpenSSH'}
        dataset_name = dataset_names.get(size, size.title())
        
        for phase_name, phase_prefix in phases:
            try:
                metadata_file = Path(f'output/{phase_prefix}_logs_metadata_{size}.json')
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    orig_mb = metadata['original_size_bytes'] / (1024*1024)
                    comp_mb = metadata['file_size_bytes'] / (1024*1024)
                    
                    # Handle different metadata formats
                    if 'overall_compression_ratio' in metadata:
                        ratio = metadata['overall_compression_ratio']  # Phase 3 format
                    else:
                        ratio = metadata['compression_ratio']  # Phase 1 & 2 format
                    
                    saved = (1 - metadata['file_size_bytes']/metadata['original_size_bytes']) * 100
                    lines = metadata.get('lines_processed', metadata.get('storage_stats', {}).get('total_lines', 'N/A'))
                    
                    print(f"{phase_name:<20} {dataset_name:<8} {lines:>6} {orig_mb:>8.1f} MB {comp_mb:>8.1f} MB {ratio:>6.2f}x {saved:>6.1f}%")
                else:
                    print(f"{phase_name:<20} {dataset_name:<8} {'N/A':<8} {'N/A':<12} {'N/A':<12} {'N/A':<8} {'N/A':<8}")
            except Exception as e:
                print(f"{phase_name:<20} {dataset_name:<8} {'ERROR':<8} {'N/A':<12} {'N/A':<12} {'N/A':<8} {'N/A':<8}")
    
    print("\n🎯 Key Insights:")
    print("  • Real-world datasets from LogHub repository")
    print("  • Apache: Web server error logs (structured)")
    print("  • HDFS: Distributed file system logs (variable structure)")  
    print("  • OpenSSH: SSH authentication logs (security events)")
    print("  • Zstd Level 22: Maximum compression baseline")
    print("  • Foundation ready for CLP-inspired template extraction!")


def print_file_sizes():
    """Print actual file sizes for verification"""
    print("\n📁 Generated Files:")
    print("-" * 30)
    
    output_dir = Path("output")
    if output_dir.exists():
        files = list(output_dir.glob("*.log")) + list(output_dir.glob("*.zst"))
        files.sort()
        
        for file in files:
            size_mb = file.stat().st_size / (1024*1024)
            print(f"   {file.name:<30} {size_mb:>8.1f} MB")


def main():
    parser = argparse.ArgumentParser(description='Run log compression pipeline')
    parser.add_argument('--size', choices=['small', 'big', 'huge'], 
                       help='Run for specific size only')
    parser.add_argument('--phase', type=int, choices=[0, 1, 2],
                       help='Run specific phase only (requires --size)')
    parser.add_argument('--force-regen', action='store_true',
                       help='Force regeneration of Phase 0 data even if cached')
    
    args = parser.parse_args()
    
    # Determine sizes to run
    if args.size:
        sizes = [args.size]
    else:
        sizes = ['small', 'big', 'huge']
    
    # Determine phases to run
    if args.phase is not None:
        if not args.size:
            print("❌ --phase requires --size to be specified")
            return 1
        phases = [args.phase]
    else:
        phases = [0, 1, 2, 3]
    
    print("🚀 Log Compression Pipeline")
    print("=" * 40)
    print(f"Sizes: {', '.join(sizes)}")
    print(f"Phases: {', '.join(map(str, phases))}")
    
    start_time = time.time()
    success_count = 0
    total_operations = len(sizes) * len(phases)
    
    # Run all combinations
    for size in sizes:
        print(f"\n🎯 Processing {size.upper()} dataset")
        print("=" * 40)
        
        size_success = True
        
        # Run requested phases
        for phase in phases:
            if phase == 0:
                if not run_phase_0(size, force=args.force_regen):
                    size_success = False
                    break
            elif phase == 1:
                if not run_phase_1(size):
                    size_success = False
                    break
            elif phase == 2:
                if not run_phase_2(size):
                    size_success = False
                    break
            elif phase == 3:
                if not run_phase_3(size):
                    size_success = False
                    break
        
        if size_success:
            success_count += len(phases)
    
    # Print results
    if not args.phase:  # Only show comprehensive results when running all phases
        print_comprehensive_results(sizes)
        print_file_sizes()
    
    # Summary
    elapsed_time = time.time() - start_time
    print(f"\n⏱️  Total time: {elapsed_time:.2f} seconds")
    print(f"✅ Successful operations: {success_count}/{total_operations}")
    
    if success_count == total_operations:
        print("🎉 All operations completed successfully!")
        return 0
    else:
        print("❌ Some operations failed")
        return 1


if __name__ == '__main__':
    exit(main())