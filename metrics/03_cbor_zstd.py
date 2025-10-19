#!/usr/bin/env python3
"""
Phase 3: CBOR + zstd Compression

This phase introduces general-purpose compression using zstd on top of CBOR format.
zstd is an excellent general-purpose compression algorithm that can achieve significant
compression ratios on structured data with minimal implementation complexity.
"""

import os
import sys
import time
import zstandard as zstd
from pathlib import Path

# Add lib directory to path for imports
lib_path = Path(__file__).parent / "lib"
sys.path.insert(0, str(lib_path))

from data_generator import load_dataset
import cbor2


def store_as_cbor_zstd(data_points, output_file, compression_level=3):
    """Store data points in zstd-compressed CBOR format"""
    print(f"Writing {len(data_points):,} data points to zstd-compressed CBOR format...")
    
    # First, serialize all data to CBOR in memory
    cbor_data = bytearray()
    for point in data_points:
        cbor_data.extend(cbor2.dumps(point))
    
    # Then compress with zstd
    compressor = zstd.ZstdCompressor(level=compression_level)
    compressed_data = compressor.compress(cbor_data)
    
    # Write compressed data to file
    with open(output_file, 'wb') as f:
        f.write(compressed_data)
    
    file_size = len(compressed_data)
    bytes_per_point = file_size / len(data_points)
    
    return file_size, bytes_per_point, len(cbor_data)


def verify_cbor_zstd_format(input_file, expected_count):
    """Verify zstd-compressed CBOR format integrity"""
    print("Verifying zstd-compressed CBOR format...")
    
    try:
        # Read and decompress
        with open(input_file, 'rb') as f:
            compressed_data = f.read()
        
        decompressor = zstd.ZstdDecompressor()
        cbor_data = decompressor.decompress(compressed_data)
        
        # Parse CBOR data using BytesIO
        from io import BytesIO
        count = 0
        stream = BytesIO(cbor_data)
        
        while stream.tell() < len(cbor_data):
            try:
                # Decode CBOR object from stream
                data = cbor2.load(stream)
                count += 1
                
                # Verify structure of first few points
                if count <= 3:
                    assert 'timestamp' in data
                    assert 'metric_name' in data
                    assert 'value' in data
                    assert 'labels' in data
                    
            except Exception as e:
                if count == 0:
                    print(f"  ❌ CBOR verification failed: {e}")
                    return False
                break
        
        if count == expected_count:
            print(f"  ✅ zstd CBOR format verified: {count:,} data points")
            return True
        else:
            print(f"  ❌ Point count mismatch: expected {expected_count:,}, got {count:,}")
            return False
            
    except Exception as e:
        print(f"  ❌ Decompression failed: {e}")
        return False


def main():
    print("=" * 60)
    print("Phase 3: CBOR + zstd Compression")
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
    
    # Store as zstd-compressed CBOR
    cbor_zstd_file = output_dir / "metrics.cbor.zst"
    file_size, bytes_per_point, uncompressed_size = store_as_cbor_zstd(data_points, cbor_zstd_file)
    
    # Verify format
    if not verify_cbor_zstd_format(cbor_zstd_file, len(data_points)):
        return 1
    
    # Compare with previous phases
    ndjson_file = output_dir / "metrics.ndjson"
    cbor_file = output_dir / "metrics.cbor"
    
    print(f"\n📉 Compression Comparison:")
    
    if ndjson_file.exists():
        ndjson_size = os.path.getsize(ndjson_file)
        compression_vs_ndjson = ndjson_size / file_size
        space_saved = ndjson_size - file_size
        space_saved_pct = (space_saved / ndjson_size) * 100
        
        print(f"  vs NDJSON:")
        print(f"    NDJSON size: {ndjson_size:,} bytes")
        print(f"    zstd CBOR size: {file_size:,} bytes")
        print(f"    Compression ratio: {compression_vs_ndjson:.2f}x")
        print(f"    Space saved: {space_saved:,} bytes ({space_saved_pct:.1f}%)")
    
    if cbor_file.exists():
        cbor_size = os.path.getsize(cbor_file)
        compression_vs_cbor = cbor_size / file_size
        
        print(f"  vs CBOR:")
        print(f"    CBOR size: {cbor_size:,} bytes")
        print(f"    zstd CBOR size: {file_size:,} bytes")
        print(f"    Additional compression: {compression_vs_cbor:.2f}x")
    
    # Internal compression stats
    internal_compression = uncompressed_size / file_size
    print(f"  zstd compression ratio: {internal_compression:.2f}x")
    
    # Results summary
    print(f"\n📊 zstd CBOR Storage Results:")
    print(f"  Output file: {cbor_zstd_file}")
    print(f"  File size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
    print(f"  Bytes per data point: {bytes_per_point:.2f}")
    
    print(f"\n✅ Phase 3 completed successfully!")
    return 0


if __name__ == "__main__":
    start_time = time.time()
    result = main()
    end_time = time.time()
    
    if result == 0:
        print(f"\n✅ Phase 3 completed in {end_time - start_time:.2f} seconds")
    else:
        print(f"\n❌ Phase 3 failed after {end_time - start_time:.2f} seconds")
    
    sys.exit(result)