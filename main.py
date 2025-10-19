#!/usr/bin/env python3
"""
Main orchestration script for the metrics storage evolution demonstration.

This script runs all phases sequentially and provides a comprehensive
comparison of different storage formats and their trade-offs.
"""

import os
import sys
import time
from typing import List, Dict, Any

def run_phase(phase_number: int, phase_name: str, script_name: str) -> Dict[str, Any]:
    """
    Run a single phase and capture its results.
    
    Args:
        phase_number: Phase number (0-5)
        phase_name: Human-readable phase name
        script_name: Python script filename
        
    Returns:
        Dictionary with phase results
    """
    print(f"\n{'='*80}")
    print(f"RUNNING PHASE {phase_number}: {phase_name}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        # Run the phase module using subprocess to avoid import conflicts
        import subprocess
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, 
                              text=True,
                              cwd=os.getcwd())
        
        if result.returncode != 0:
            print(f"❌ Phase {phase_number} failed with return code {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return {
                "phase": phase_number,
                "name": phase_name,
                "error": f"Failed with return code {result.returncode}",
                "execution_time": 0,
                "status": "failed"
            }
        else:
            # Print the output from the phase
            print(result.stdout)
            if result.stderr:
                print(f"STDERR: {result.stderr}")
        
    except Exception as e:
        print(f"❌ Phase {phase_number} failed with error: {e}")
        return {
            "phase": phase_number,
            "name": phase_name,
            "error": str(e),
            "execution_time": 0,
            "status": "failed"
        }
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"\n✅ Phase {phase_number} completed in {execution_time:.2f} seconds")
    
    return {
        "phase": phase_number,
        "name": phase_name,
        "execution_time": execution_time,
        "status": "success"
    }

def collect_file_sizes() -> Dict[str, int]:
    """Collect file sizes from all output files."""
    output_files = {
        "raw_dataset.pkl": "Raw Dataset (Pickle)",
        "metrics.ndjson": "Phase 1: NDJSON",
        "metrics.columnar.msgpack": "Phase 2: Columnar",
        "metrics.compressed.msgpack": "Phase 3: Compressed",
        "metrics.final.tsdb": "Phase 4: Custom Binary",
    }
    
    file_sizes = {}
    
    for filename, description in output_files.items():
        filepath = os.path.join("output", filename)
        if os.path.exists(filepath):
            file_sizes[description] = os.path.getsize(filepath)
    
    # Collect downsampled files
    for filename in os.listdir("output"):
        if filename.startswith("metrics.downsampled.") and filename.endswith(".msgpack"):
            filepath = os.path.join("output", filename)
            interval = filename.replace("metrics.downsampled.", "").replace(".msgpack", "")
            description = f"Phase 5: Downsampled ({interval})"
            file_sizes[description] = os.path.getsize(filepath)
    
    return file_sizes

def print_comprehensive_summary(phase_results: List[Dict[str, Any]], file_sizes: Dict[str, int]) -> None:
    """Print a comprehensive summary of all phases and results."""
    print(f"\n{'='*80}")
    print("COMPREHENSIVE STORAGE EVOLUTION SUMMARY")
    print(f"{'='*80}")
    
    # Phase execution summary
    print(f"\n📋 Phase Execution Summary:")
    total_time = 0
    for result in phase_results:
        status = "✅ SUCCESS" if result.get("status") == "success" else "❌ FAILED"
        exec_time = result.get("execution_time", 0)
        total_time += exec_time
        
        phase_num = result.get("phase", "?")
        phase_name = result.get("name", "Unknown")
        
        print(f"  Phase {phase_num}: {phase_name}")
        print(f"    Status: {status}")
        print(f"    Time: {exec_time:.2f}s")
        if "error" in result:
            print(f"    Error: {result['error']}")
    
    print(f"\n  Total execution time: {total_time:.2f} seconds")
    
    # File size comparison
    print(f"\n📊 Storage Format Comparison:")
    if not file_sizes:
        print("  No output files found for comparison")
        return
    
    # Find baseline (NDJSON) for compression ratios
    baseline_size = None
    for desc, size in file_sizes.items():
        if "NDJSON" in desc:
            baseline_size = size
            break
    
    if not baseline_size:
        baseline_size = max(file_sizes.values())  # Use largest as baseline
    
    print(f"  {'Format':<35} {'Size (bytes)':<15} {'Size (MB)':<12} {'Compression':<12} {'% of Original':<12}")
    print(f"  {'-'*35} {'-'*15} {'-'*12} {'-'*12} {'-'*12}")
    
    sorted_files = sorted(file_sizes.items(), key=lambda x: x[1], reverse=True)
    
    for description, size in sorted_files:
        size_mb = size / (1024 * 1024)
        compression_ratio = baseline_size / size if size > 0 else 0
        percent_of_original = (size / baseline_size * 100) if baseline_size > 0 else 0
        
        print(f"  {description:<35} {size:>14,} {size_mb:>11.2f} {compression_ratio:>11.2f}x {percent_of_original:>11.1f}%")
    
    # Calculate total downsampled size
    downsampled_total = sum(size for desc, size in file_sizes.items() if "Downsampled" in desc)
    if downsampled_total > 0:
        ds_compression = baseline_size / downsampled_total if downsampled_total > 0 else 0
        ds_percent = (downsampled_total / baseline_size * 100) if baseline_size > 0 else 0
        print(f"  {'-'*35} {'-'*15} {'-'*12} {'-'*12} {'-'*12}")
        print(f"  {'Total Downsampled':<35} {downsampled_total:>14,} {downsampled_total/(1024*1024):>11.2f} {ds_compression:>11.2f}x {ds_percent:>11.1f}%")
    
    # Key insights
    print(f"\n💡 Key Insights:")
    
    best_compression = max((baseline_size / size, desc) for desc, size in file_sizes.items() if size > 0)
    print(f"  🏆 Best compression: {best_compression[1]} ({best_compression[0]:.1f}x reduction)")
    
    if baseline_size and downsampled_total > 0:
        total_reduction = baseline_size / downsampled_total
        print(f"  📉 Long-term storage efficiency: {total_reduction:.1f}x with downsampling")
    
    # Data journey summary
    print(f"\n🛤️  The Data Journey:")
    print(f"  1️⃣  Started with human-readable JSON - easy to debug but massively inefficient")
    print(f"  2️⃣  Restructured to columnar format - eliminated metadata repetition")
    print(f"  3️⃣  Applied specialized compression - leveraged data patterns for huge gains")
    print(f"  4️⃣  Created self-contained binary format - production-ready structure")
    print(f"  5️⃣  Added downsampling - essential for long-term retention at scale")
    
    # Real-world implications
    print(f"\n🌍 Real-world Implications:")
    
    if baseline_size > 0:
        # Extrapolate to realistic scale
        daily_data_gb = (baseline_size / (1024**3)) * (86400 / 15) * 1000  # Assume 15s intervals, scale to 1000 series
        
        print(f"  📈 Scaling to production (1000 series, 1 day):")
        print(f"    Raw NDJSON: ~{daily_data_gb:.1f} GB/day")
        
        for desc, size in file_sizes.items():
            if "Custom Binary" in desc:
                compressed_daily = daily_data_gb * (size / baseline_size)
                print(f"    Compressed: ~{compressed_daily:.2f} GB/day ({daily_data_gb/compressed_daily:.0f}x reduction)")
            elif "Total Downsampled" in desc or downsampled_total > 0:
                ds_daily = daily_data_gb * (downsampled_total / baseline_size)
                annual_ds = ds_daily * 365
                print(f"    Downsampled: ~{ds_daily:.3f} GB/day (~{annual_ds:.1f} GB/year)")
    
    print(f"\n🎯 Production Recommendations:")
    print(f"  • Use columnar compression for high-resolution recent data (hours to days)")
    print(f"  • Implement automatic downsampling for medium-term storage (days to months)")
    print(f"  • Keep only essential aggregates for long-term retention (months to years)")
    print(f"  • Monitor compression ratios - they indicate data pattern health")
    print(f"  • Consider tiered storage: SSD for recent, HDD for historical")

def main():
    """Main function to orchestrate all phases."""
    print("🚀 Starting Metrics Storage Engine Evolution Demonstration")
    print(f"Working directory: {os.getcwd()}")
    
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Define all phases
    phases = [
        (0, "Data Generation", "00_generate_data.py"),
        (1, "Baseline NDJSON Storage", "01_ndjson_storage.py"),
        (2, "Columnar Storage", "02_columnar_storage.py"),
        (3, "Compressed Columnar", "03_compressed_columnar.py"),
        (4, "Custom Binary Format", "04_custom_binary_format.py"),
        (5, "Downsampling Storage", "05_downsampling_storage.py"),
    ]
    
    phase_results = []
    
    # Run each phase
    for phase_num, phase_name, script_name in phases:
        if not os.path.exists(script_name):
            print(f"⚠️  Warning: {script_name} not found, skipping Phase {phase_num}")
            continue
        
        result = run_phase(phase_num, phase_name, script_name)
        phase_results.append(result)
        
        # Stop if phase failed
        if "error" in result:
            print(f"❌ Stopping execution due to Phase {phase_num} failure")
            break
    
    # Collect final results
    file_sizes = collect_file_sizes()
    
    # Print comprehensive summary
    print_comprehensive_summary(phase_results, file_sizes)
    
    print(f"\n🎉 Metrics Storage Evolution demonstration completed!")
    print(f"📁 All output files are in the 'output/' directory")
    print(f"📖 Check individual phase scripts for detailed implementation")

if __name__ == "__main__":
    main()