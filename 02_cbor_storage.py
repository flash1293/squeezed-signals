#!/usr/bin/env python3
"""
Phase 2: CBOR Storage - Better Binary Serialization

CBOR (Concise Binary Object Representation) is a binary data serialization format
that's more efficient than JSON while maintaining similar structure and readability.
It's standardized (RFC 7049) and provides better type support.
"""

import os
import sys
import time
from pathlib import Path

# Add lib directory to path for imports
lib_path = Path(__file__).parent / "lib"
sys.path.insert(0, str(lib_path))

from data_generator import load_dataset
import cbor2


def analyze_cbor_benefits(data_points):
    """Analyze the benefits of CBOR over JSON"""
    print("Analyzing CBOR format benefits:")
    
    # Count data types that benefit from CBOR
    numeric_values = sum(1 for point in data_points if isinstance(point['value'], (int, float)))
    timestamp_values = len(data_points)  # All timestamps are integers
    string_values = sum(len(point['labels']) + 1 for point in data_points)  # labels + metric_name
    
    print(f"  Numeric values: {numeric_values:,} (benefit from binary encoding)")
    print(f"  Timestamp values: {timestamp_values:,} (benefit from integer encoding)")
    print(f"  String values: {string_values:,} (benefit from length-prefixed encoding)")
    print(f"  Boolean/null optimization: Available but not used in this dataset")
    
    # Estimate size benefits
    json_overhead = len(data_points) * 50  # Rough estimate of JSON syntax overhead
    print(f"  Estimated JSON syntax overhead eliminated: ~{json_overhead:,} bytes")


def store_as_cbor(data_points, output_file):
    """Store data points in CBOR format"""
    print(f"Writing {len(data_points):,} data points to CBOR format...")
    
    with open(output_file, 'wb') as f:
        for point in data_points:
            # CBOR can encode each data point efficiently
            cbor_data = cbor2.dumps(point)
            f.write(cbor_data)
    
    file_size = os.path.getsize(output_file)
    bytes_per_point = file_size / len(data_points)
    
    return file_size, bytes_per_point


def verify_cbor_format(input_file, expected_count):
    """Verify CBOR format integrity"""
    print("Verifying CBOR format...")
    
    count = 0
    with open(input_file, 'rb') as f:
        while True:
            try:
                # Try to decode a CBOR object
                data = cbor2.load(f)
                count += 1
                
                # Verify structure of first few points
                if count <= 3:
                    assert 'timestamp' in data
                    assert 'metric_name' in data
                    assert 'value' in data
                    assert 'labels' in data
                    
            except cbor2.CBORDecodeEOF:
                break
            except Exception as e:
                print(f"  ❌ CBOR verification failed at point {count}: {e}")
                return False
    
    if count == expected_count:
        print(f"  ✅ CBOR format verified: {count:,} data points")
        return True
    else:
        print(f"  ❌ Point count mismatch: expected {expected_count:,}, got {count:,}")
        return False


def main():
    print("=" * 60)
    print("Phase 2: CBOR Storage - Better Binary Serialization")
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
    
    # Store as CBOR
    cbor_file = output_dir / "metrics.cbor"
    file_size, bytes_per_point = store_as_cbor(data_points, cbor_file)
    
    # Verify CBOR format
    if not verify_cbor_format(cbor_file, len(data_points)):
        return 1
    
    # Analyze benefits
    analyze_cbor_benefits(data_points)
    
    # Compare with NDJSON (if it exists)
    ndjson_file = output_dir / "metrics.ndjson"
    if ndjson_file.exists():
        ndjson_size = os.path.getsize(ndjson_file)
        compression_ratio = ndjson_size / file_size
        space_saved = ndjson_size - file_size
        space_saved_pct = (space_saved / ndjson_size) * 100
        
        print(f"\n📉 Compression vs NDJSON:")
        print(f"  NDJSON size: {ndjson_size:,} bytes")
        print(f"  CBOR size: {file_size:,} bytes")
        print(f"  Compression ratio: {compression_ratio:.2f}x")
        print(f"  Space saved: {space_saved:,} bytes ({space_saved_pct:.1f}%)")
    
    # Results summary
    print(f"\n📊 CBOR Storage Results:")
    print(f"  Output file: {cbor_file}")
    print(f"  File size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
    print(f"  Bytes per data point: {bytes_per_point:.2f}")
    
    print(f"\n💡 CBOR Format Characteristics:")
    print(f"  ✅ Pros:")
    print(f"    - More efficient than JSON (binary encoding)")
    print(f"    - Preserves data types (integers, floats, strings)")
    print(f"    - Standardized format (RFC 7049)")
    print(f"    - Self-describing and schema-less")
    print(f"    - Faster parsing than JSON")
    print(f"    - Smaller than JSON due to binary encoding")
    print(f"  ❌ Cons:")
    print(f"    - Not human-readable")
    print(f"    - Still denormalized (same redundancy as JSON)")
    print(f"    - Requires CBOR library to read")
    print(f"    - No compression of repeated keys/values")
    
    print(f"\n✅ Phase 2 completed successfully!")
    return 0


if __name__ == "__main__":
    start_time = time.time()
    result = main()
    end_time = time.time()
    
    if result == 0:
        print(f"\n✅ Phase 2 completed in {end_time - start_time:.2f} seconds")
    else:
        print(f"\n❌ Phase 2 failed after {end_time - start_time:.2f} seconds")
    
    sys.exit(result)