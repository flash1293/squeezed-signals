#!/usr/bin/env python3
"""
Distributed Traces Storage Evolution Pipeline

Demonstrates progressive optimization techniques for trace storage,
from baseline NDJSON to advanced pattern-aware compression.
"""

import sys
import os
import time
import subprocess
from pathlib import Path
import argparse

# Add project root to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DEFAULT_ZSTD_LEVEL

def run_phase(phase_script: str, size: str):
    """Run a specific phase script"""
    script_path = Path(phase_script)
    
    if not script_path.exists():
        print(f"⚠️  Phase script {phase_script} not found")
        return False
    
    print(f"\n{'='*60}")
    print(f"Running {script_path.name} (size: {size})")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Run the phase script
        result = subprocess.run([sys.executable, str(script_path), size], 
                              capture_output=False, text=True, cwd=str(script_path.parent))
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ {script_path.name} completed successfully in {duration:.2f}s")
            return True
        else:
            print(f"❌ {script_path.name} failed with return code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Error running {script_path.name}: {e}")
        return False

def get_file_size(filepath: str) -> int:
    """Get file size in bytes, return 0 if file doesn't exist"""
    try:
        return os.path.getsize(filepath)
    except (OSError, FileNotFoundError):
        return 0

def display_compression_summary(size: str):
    """Display compression results summary"""
    print(f"\n{'='*60}")
    print(f"COMPRESSION SUMMARY (size: {size})")
    print(f"{'='*60}")
    
    # File patterns to check
    files_to_check = [
        ('Original JSON', f'output/traces_{size}.json'),
        ('Phase 1 - NDJSON', f'output/traces_{size}_ndjson.jsonl'),
        ('Phase 2 - CBOR', f'output/traces_{size}_cbor.cbor'),
        ('Phase 3 - CBOR+Zstd', f'output/traces_{size}_cbor_zstd.zst'),
        ('Phase 4 - Relationships', f'output/traces_{size}_relationships.msgpack.zst'),
        ('Phase 5 - Columnar', f'output/traces_{size}_columnar.msgpack.zst'),
        # Add more phases as they're implemented
    ]
    
    baseline_size = get_file_size(f'output/traces_{size}_ndjson.jsonl')
    
    print(f"{'Phase':<25} {'Size':<15} {'Compression':<15} {'vs Baseline'}")
    print("-" * 60)
    
    for phase_name, filepath in files_to_check:
        file_size = get_file_size(filepath)
        
        if file_size > 0:
            if baseline_size > 0:
                ratio = baseline_size / file_size
                size_str = f"{file_size:,} bytes"
                ratio_str = f"{ratio:.2f}x" if ratio != 1.0 else "1.0x (baseline)"
            else:
                size_str = f"{file_size:,} bytes"
                ratio_str = "N/A"
            
            print(f"{phase_name:<25} {size_str:<15} {ratio_str:<15}")
        else:
            print(f"{phase_name:<25} {'Not found':<15} {'N/A':<15}")

def check_dependencies():
    """Check if required dependencies are available"""
    print("Checking dependencies...")
    
    missing_deps = []
    
    try:
        import cbor2
        print("✅ cbor2 available")
    except ImportError:
        missing_deps.append("cbor2")
        print("❌ cbor2 not available")
    
    try:
        import msgpack
        print("✅ msgpack available")
    except ImportError:
        missing_deps.append("msgpack")
        print("❌ msgpack not available")
    
    try:
        import zstandard
        print("✅ zstandard available")
    except ImportError:
        missing_deps.append("zstandard")
        print("❌ zstandard not available")
    
    if missing_deps:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install " + " ".join(missing_deps))
        return False
    
    print("✅ All dependencies available")
    return True

def main():
    """Main pipeline runner"""
    parser = argparse.ArgumentParser(description='Run distributed traces storage evolution pipeline')
    parser.add_argument('--size', choices=['small', 'medium', 'big', 'huge'], default='small',
                       help='Dataset size to generate/process')
    parser.add_argument('--phase', type=str, help='Run specific phase (e.g., "01" for phase 1)')
    parser.add_argument('--skip-deps', action='store_true', help='Skip dependency check')
    parser.add_argument('--zstd-level', type=int, default=None, choices=range(1, 23),
                       help=f'Zstd compression level (1-22, default: {DEFAULT_ZSTD_LEVEL})')
    
    args = parser.parse_args()
    
    # Set zstd level globally if specified
    if args.zstd_level is not None:
        import config
        config.DEFAULT_ZSTD_LEVEL = args.zstd_level
        print(f"Using zstd compression level: {args.zstd_level}")
    
    print("🚀 Distributed Traces Storage Evolution Pipeline")
    print("=" * 60)
    
    # Check dependencies unless skipped
    if not args.skip_deps and not check_dependencies():
        print("\n❌ Please install missing dependencies before continuing")
        return
    
    # Create output directory
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Define available phases
    phases = [
        ('00', '00_generate_data.py', 'Generate realistic trace data'),
        ('01', '01_ndjson_storage.py', 'NDJSON baseline storage'),
        ('02', '02_cbor_storage.py', 'CBOR binary encoding'),
        ('03', '03_cbor_zstd.py', 'CBOR + Zstandard compression'),
        ('04', '04_span_relationships.py', 'Span relationship compression'),
        ('05', '05_columnar_storage.py', 'Columnar trace storage'),
        # Add more phases as they're implemented
    ]
    
    # Run specific phase if requested
    if args.phase:
        phase_found = False
        for phase_num, script, description in phases:
            if phase_num == args.phase:
                print(f"Running Phase {phase_num}: {description}")
                success = run_phase(script, args.size)
                if success:
                    display_compression_summary(args.size)
                phase_found = True
                break
        
        if not phase_found:
            print(f"❌ Phase {args.phase} not found")
            print(f"Available phases: {', '.join(p[0] for p in phases)}")
        return
    
    # Run all available phases
    print(f"Running all phases with size: {args.size}")
    
    successful_phases = 0
    total_start_time = time.time()
    
    for phase_num, script, description in phases:
        print(f"\n🔄 Phase {phase_num}: {description}")
        
        success = run_phase(script, args.size)
        if success:
            successful_phases += 1
        else:
            print(f"⚠️  Phase {phase_num} failed, but continuing...")
    
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    # Display final summary
    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETE")
    print(f"{'='*60}")
    print(f"Successful phases: {successful_phases}/{len(phases)}")
    print(f"Total runtime: {total_duration:.2f}s")
    
    display_compression_summary(args.size)
    
    print(f"\n📁 Output files available in: output/")
    print(f"🔍 Check individual phase metadata files for detailed analysis")

if __name__ == '__main__':
    main()