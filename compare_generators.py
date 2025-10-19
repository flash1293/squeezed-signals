#!/usr/bin/env python3
"""
Data Generator Selection Script

Helper script to easily switch between synthetic and real data generators
and compare their characteristics and compression ratios.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_with_generator(generator: str, size: str):
    """Run the complete pipeline with specified generator and size."""
    print(f"\n{'='*60}")
    print(f"Running with {generator.upper()} data generator, size: {size}")
    print(f"{'='*60}")
    
    env = os.environ.copy()
    env['DATA_GENERATOR'] = generator
    env['DATASET_SIZE'] = size
    
    # Run main pipeline
    result = subprocess.run([
        sys.executable, 'main.py', '--size', size
    ], env=env, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Error running {generator} generator:")
        print(result.stderr)
        return False
    
    print(result.stdout)
    return True

def compare_generators():
    """Compare synthetic vs real data generators."""
    print("🔄 Comparing Synthetic vs Real Data Generators")
    print("=" * 60)
    
    # Test both generators with small size
    generators = ['synthetic', 'real']
    
    for generator in generators:
        success = run_with_generator(generator, 'small')
        if not success:
            print(f"Failed to run {generator} generator")
            continue
            
        # Show file sizes
        output_dir = Path("output")
        if output_dir.exists():
            print(f"\n📁 Output files from {generator} generator:")
            for file in sorted(output_dir.glob("*.ndjson")):
                size = file.stat().st_size
                print(f"  {file.name}: {size:,} bytes ({size/1024/1024:.2f} MB)")
    
    print("\n✨ Comparison completed!")

def main():
    """Main function with CLI interface."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python compare_generators.py synthetic [small|big]")
        print("  python compare_generators.py real [small|big]") 
        print("  python compare_generators.py compare")
        print("")
        print("Examples:")
        print("  python compare_generators.py synthetic small")
        print("  python compare_generators.py real big")
        print("  python compare_generators.py compare")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "compare":
        compare_generators()
    elif command in ['synthetic', 'real']:
        size = sys.argv[2] if len(sys.argv) > 2 else 'small'
        if size not in ['small', 'big']:
            print("Size must be 'small' or 'big'")
            sys.exit(1)
        run_with_generator(command, size)
    else:
        print(f"Unknown command: {command}")
        print("Use 'synthetic', 'real', or 'compare'")
        sys.exit(1)

if __name__ == "__main__":
    main()