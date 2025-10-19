#!/usr/bin/env python3
"""
Phase 7: General-Purpose Compression Comparison

This phase demonstrates that general-purpose compression algorithms like zstd
can also achieve significant compression on text-based formats. This serves as
a comparison to show that while specialized techniques are powerful, sometimes
simple solutions can be surprisingly effective.
"""

import os
import sys
import time
from pathlib import Path
import zstandard as zstd

# Add lib directory to path for imports
lib_path = Path(__file__).parent / "lib"
sys.path.insert(0, str(lib_path))

from data_generator import load_dataset


def store_ndjson_with_zstd(data_points, output_file):
    """Store data points as zstd-compressed NDJSON"""
    print(f"Writing {len(data_points):,} data points to zstd-compressed NDJSON format...")
    
    # Create zstd compressor
    compressor = zstd.ZstdCompressor(level=3)  # Level 3 is a good balance of speed/compression
    
    with open(output_file, 'wb') as f:
        with compressor.stream_writer(f) as writer:
            for point in data_points:
                # Convert to JSON and encode
                import json
                json_line = json.dumps(point, separators=(',', ':')) + '\n'
                writer.write(json_line.encode('utf-8'))
    
    file_size = os.path.getsize(output_file)
    bytes_per_point = file_size / len(data_points)
    
    return file_size, bytes_per_point


def verify_zstd_ndjson(input_file, expected_count):
    """Verify zstd-compressed NDJSON integrity"""
    print("Verifying zstd-compressed NDJSON...")
    
    decompressor = zstd.ZstdDecompressor()
    count = 0
    
    try:
        with open(input_file, 'rb') as f:
            with decompressor.stream_reader(f) as reader:
                text_stream = reader.read().decode('utf-8')
                lines = text_stream.strip().split('\n')
                
                for line in lines:
                    if line:  # Skip empty lines
                        import json
                        data = json.loads(line)
                        count += 1
                        
                        # Verify structure of first few points
                        if count <= 3:
                            assert 'timestamp' in data
                            assert 'metric_name' in data
                            assert 'value' in data
                            assert 'labels' in data
        
        if count == expected_count:
            print(f"  ✅ zstd NDJSON verified: {count:,} data points")
            return True
        else:
            print(f"  ❌ Point count mismatch: expected {expected_count:,}, got {count:,}")
            return False
            
    except Exception as e:
        print(f"  ❌ zstd NDJSON verification failed: {e}")
        return False


def analyze_compression_comparison(zstd_size, data_points):
    """Compare zstd compression with other formats"""
    print("\nComparing general-purpose compression with specialized techniques:")
    
    output_dir = Path("output")
    comparisons = []
    
    # Check various format files
    formats = {
        "NDJSON": "metrics.ndjson",
        "CBOR": "metrics.cbor", 
        "Binary Table": "metrics.bintable.bin",
        "Columnar": "metrics.columnar.msgpack",
        "Compressed Columnar": "metrics.compressed.msgpack"
    }
    
    for format_name, filename in formats.items():
        file_path = output_dir / filename
        if file_path.exists():
            file_size = os.path.getsize(file_path)
            ratio_vs_zstd = file_size / zstd_size
            comparisons.append((format_name, file_size, ratio_vs_zstd))
    
    if comparisons:
        print("\n📊 Format Size Comparison vs zstd NDJSON:")
        print("  Format                          Size (MB)    vs zstd")
        print("  -------------------------------- ------------ --------")
        
        # Sort by file size
        comparisons.sort(key=lambda x: x[1])
        
        for format_name, file_size, ratio in comparisons:
            size_mb = file_size / (1024 * 1024)
            if ratio > 1:
                comparison = f"{ratio:.2f}x larger"
            else:
                comparison = f"{1/ratio:.2f}x smaller"
            print(f"  {format_name:<30} {size_mb:>10.2f}    {comparison}")
        
        # Add zstd NDJSON itself
        zstd_mb = zstd_size / (1024 * 1024)
        print(f"  {'zstd NDJSON':<30} {zstd_mb:>10.2f}    baseline")


def main():
    print("=" * 60)
    print("Phase 7: General-Purpose Compression Comparison")
    print("=" * 60)
    
    # Load the dataset
    try:
        data_points = load_dataset()
        print(f"Loaded {len(data_points):,} data points from dataset")
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return 1
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Store as zstd-compressed NDJSON
    zstd_file = output_dir / "metrics.ndjson.zst"
    file_size, bytes_per_point = store_ndjson_with_zstd(data_points, zstd_file)
    
    # Verify format
    if not verify_zstd_ndjson(zstd_file, len(data_points)):
        return 1
    
    # Compare with original NDJSON
    ndjson_file = output_dir / "metrics.ndjson"
    if ndjson_file.exists():
        ndjson_size = os.path.getsize(ndjson_file)
        compression_ratio = ndjson_size / file_size
        space_saved = ndjson_size - file_size
        space_saved_pct = (space_saved / ndjson_size) * 100
        
        print(f"\n📉 Compression vs raw NDJSON:")
        print(f"  Raw NDJSON size: {ndjson_size:,} bytes")
        print(f"  zstd compressed size: {file_size:,} bytes")
        print(f"  Compression ratio: {compression_ratio:.2f}x")
        print(f"  Space saved: {space_saved:,} bytes ({space_saved_pct:.1f}%)")
    
    # Analyze compression vs other techniques
    analyze_compression_comparison(file_size, data_points)
    
    # Results summary
    print(f"\n📊 zstd Compression Results:")
    print(f"  Output file: {zstd_file}")
    print(f"  File size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
    print(f"  Bytes per data point: {bytes_per_point:.2f}")
    
    print(f"\n💡 General-Purpose Compression Characteristics:")
    print(f"  ✅ Pros:")
    print(f"    - Excellent compression ratios with no code changes")
    print(f"    - Works on any data format (JSON, XML, CSV, etc.)")
    print(f"    - Battle-tested and widely supported")
    print(f"    - Can decompress to original human-readable format")
    print(f"    - Fast compression and decompression")
    print(f"    - Easy to implement (just wrap existing code)")
    print(f"  ❌ Cons:")
    print(f"    - Still preserves all the redundancy of the original format")
    print(f"    - Requires decompression for any data access")
    print(f"    - May not beat specialized techniques for specific data")
    print(f"    - Compression ratio depends heavily on data patterns")
    
    print(f"\n🎯 Key Insight:")
    print(f"  General-purpose compression like zstd can achieve excellent results")
    print(f"  on text formats, often competing with more complex specialized")
    print(f"  approaches. Sometimes the simplest solution is surprisingly effective!")
    
    print(f"\n✅ Phase 7 completed successfully!")
    return 0


if __name__ == "__main__":
    start_time = time.time()
    result = main()
    end_time = time.time()
    
    if result == 0:
        print(f"\n✅ Phase 7 completed in {end_time - start_time:.2f} seconds")
    else:
        print(f"\n❌ Phase 7 failed after {end_time - start_time:.2f} seconds")
    
    sys.exit(result)