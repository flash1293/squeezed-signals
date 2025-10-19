#!/usr/bin/env python3
"""
Compression comparison script - demonstrates the impact of enhanced data generation
on compression ratios.
"""

import os
import subprocess
import time
from pathlib import Path

def run_compression_test(regularity_level="standard", size="small"):
    """Run compression test with specified regularity level."""
    print(f"\n{'='*80}")
    print(f"TESTING: {regularity_level.upper()} REGULARITY ({size} dataset)")
    print(f"{'='*80}")
    
    # Set environment variables
    env = os.environ.copy()
    env["DATASET_SIZE"] = size
    
    if regularity_level != "standard":
        env["USE_ENHANCED_GENERATOR"] = "true"
        env["REGULARITY_LEVEL"] = regularity_level
    
    # Run the main script
    start_time = time.time()
    result = subprocess.run(
        [".venv/bin/python", "main.py", "--size", size],
        env=env,
        capture_output=True,
        text=True
    )
    end_time = time.time()
    
    if result.returncode != 0:
        print(f"❌ Error running test: {result.stderr}")
        return None
    
    # Extract compression results from output
    output_lines = result.stdout.split('\n')
    
    # Find Phase 5 compression ratio
    phase5_compression = None
    for line in output_lines:
        if "vs NDJSON:" in line and "compression" in line:
            try:
                # Extract compression ratio like "14.42x compression"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.endswith('x') and 'compression' in parts[i+1:i+3]:
                        phase5_compression = float(part[:-1])
                        break
            except (ValueError, IndexError):
                continue
    
    # Find file sizes
    sizes = {}
    for line in output_lines:
        if "Size (MB)" in line or "Size (bytes)" in line:
            continue
        if "Phase 1: NDJSON" in line and "bytes" in line:
            sizes["ndjson"] = int(line.split()[3])
        elif "Phase 5: Compression Tricks" in line and "bytes" in line:
            sizes["compressed"] = int(line.split()[4])
    
    # Find additional metrics
    zero_deltas = None
    value_compression = None
    timestamp_compression = None
    
    for line in output_lines:
        if "Zero deltas (perfect regularity):" in line:
            try:
                pct_str = line.split('(')[1].split('%')[0]
                zero_deltas = float(pct_str)
            except:
                pass
        elif "Value compression:" in line:
            try:
                ratio_str = line.split(':')[1].strip().split('x')[0]
                value_compression = float(ratio_str)
            except:
                pass
        elif "Timestamp compression:" in line:
            try:
                ratio_str = line.split(':')[1].strip().split('x')[0]
                timestamp_compression = float(ratio_str)
            except:
                pass
    
    execution_time = end_time - start_time
    
    return {
        "regularity": regularity_level,
        "phase5_compression": phase5_compression,
        "sizes": sizes,
        "zero_deltas": zero_deltas,
        "value_compression": value_compression,
        "timestamp_compression": timestamp_compression,
        "execution_time": execution_time
    }

def main():
    """Run compression comparison tests."""
    print("🚀 Compression Tricks Enhancement Demonstration")
    print("=" * 80)
    print("This script compares compression ratios with different data regularity levels.")
    print("Enhanced data generation adds realistic patterns that improve compression.")
    
    # Ensure we're in the right directory
    if not Path("main.py").exists():
        print("❌ Error: main.py not found. Please run from the project root directory.")
        return
    
    # Run tests with different regularity levels
    test_configs = [
        ("standard", "small"),
        ("medium", "small"), 
        ("high", "small")
    ]
    
    results = []
    for regularity, size in test_configs:
        result = run_compression_test(regularity, size)
        if result:
            results.append(result)
    
    # Print comparison summary
    print(f"\n{'='*80}")
    print("COMPRESSION COMPARISON SUMMARY")
    print(f"{'='*80}")
    
    print(f"{'Regularity Level':<18} {'Phase 5 Ratio':<15} {'Zero Deltas':<12} {'Value Comp':<12} {'Timestamp Comp':<15} {'Time (s)':<10}")
    print("-" * 80)
    
    for result in results:
        regularity = result["regularity"].title()
        phase5 = f"{result['phase5_compression']:.2f}x" if result['phase5_compression'] else "N/A"
        zero_deltas = f"{result['zero_deltas']:.1f}%" if result['zero_deltas'] is not None else "N/A"
        value_comp = f"{result['value_compression']:.2f}x" if result['value_compression'] else "N/A"
        timestamp_comp = f"{result['timestamp_compression']:.2f}x" if result['timestamp_compression'] else "N/A"
        exec_time = f"{result['execution_time']:.1f}s"
        
        print(f"{regularity:<18} {phase5:<15} {zero_deltas:<12} {value_comp:<12} {timestamp_comp:<15} {exec_time:<10}")
    
    # Calculate improvements
    if len(results) >= 2:
        standard_ratio = results[0]['phase5_compression']
        high_ratio = results[-1]['phase5_compression'] if results[-1]['regularity'] == 'high' else None
        
        if standard_ratio and high_ratio:
            improvement = high_ratio / standard_ratio
            print(f"\n💡 Key Insights:")
            print(f"   📈 High regularity achieves {improvement:.1f}x better compression than standard")
            print(f"   🎯 Compression improved from {standard_ratio:.1f}x to {high_ratio:.1f}x")
            print(f"   ⚡ File size reduced from {results[0]['sizes'].get('compressed', 0)/1024:.0f}KB to {results[-1]['sizes'].get('compressed', 0)/1024:.0f}KB")
    
    print(f"\n🔬 Technical Details:")
    print(f"   • Enhanced generator adds realistic timestamp regularity")
    print(f"   • Value quantization reduces floating-point precision appropriately") 
    print(f"   • Infrastructure correlation creates shared patterns")
    print(f"   • All enhancements based on real monitoring system behaviors")
    
    print(f"\n📚 For detailed analysis, see: docs/enhanced-compression-analysis.md")

if __name__ == "__main__":
    main()