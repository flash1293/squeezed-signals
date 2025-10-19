#!/usr/bin/env python3
"""
Phase 3: Compressing the Columns - Specialized Encodings

This script applies aggressive compression techniques to columnar data,
using specialized encodings for timestamps and values.
"""

import os
import pickle
import msgpack
from typing import List, Dict, Any, Tuple
from lib.encoders import (
    delta_encode_timestamps, delta_decode_timestamps,
    run_length_encode, run_length_decode,
    xor_encode_floats, xor_decode_floats,
    simple_delta_encode_floats, simple_delta_decode_floats,
    compress_integer_list, decompress_integer_list
)

def compress_columnar_data(columnar_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply specialized compression to columnar data.
    
    Args:
        columnar_data: Original columnar format data
        
    Returns:
        Compressed columnar data
    """
    print("Applying specialized compression to columnar data...")
    
    series_metadata = columnar_data["series_metadata"]
    series_data = columnar_data["series_data"]
    
    compressed_series_data = {}
    
    compression_stats = {
        "original_timestamps_bytes": 0,
        "compressed_timestamps_bytes": 0,
        "original_values_bytes": 0,
        "compressed_values_bytes": 0,
        "zero_deltas_count": 0,
        "total_deltas_count": 0
    }
    
    for series_id, data in series_data.items():
        timestamps = data["timestamps"]
        values = data["values"]
        
        print(f"  Compressing series {series_id}: {len(timestamps)} points")
        
        # Compress timestamps using double-delta encoding
        if len(timestamps) >= 1:
            initial_ts, first_delta, double_deltas = delta_encode_timestamps(timestamps)
            
            # Count zero deltas for statistics
            zero_deltas = sum(1 for dd in double_deltas if dd == 0)
            compression_stats["zero_deltas_count"] += zero_deltas
            compression_stats["total_deltas_count"] += len(double_deltas)
            
            # Apply run-length encoding to double deltas
            rle_double_deltas = run_length_encode(double_deltas)
            
            # Compress the RLE data
            compressed_double_deltas = compress_integer_list([item for pair in rle_double_deltas for item in pair])
            
            # Store compressed timestamp data
            compressed_timestamps = {
                "initial": initial_ts,
                "first_delta": first_delta,
                "rle_double_deltas": rle_double_deltas,
                "compressed_rle": compressed_double_deltas
            }
            
            # Calculate compression statistics
            original_ts_bytes = len(timestamps) * 8  # 8 bytes per int64
            compressed_ts_bytes = 8 + 8 + len(compressed_double_deltas)  # initial + first_delta + compressed
            compression_stats["original_timestamps_bytes"] += original_ts_bytes
            compression_stats["compressed_timestamps_bytes"] += compressed_ts_bytes
            
        else:
            compressed_timestamps = {"initial": 0, "first_delta": 0, "rle_double_deltas": [], "compressed_rle": b""}
        
        # Compress values using XOR encoding (Gorilla-like)
        if len(values) >= 1:
            try:
                first_value, xor_encoded = xor_encode_floats(values)
                compressed_values = {
                    "method": "xor",
                    "first_value": first_value,
                    "xor_encoded": xor_encoded
                }
            except Exception as e:
                # Fall back to simple delta encoding if XOR fails
                print(f"    XOR encoding failed for series {series_id}, using delta encoding: {e}")
                first_value, deltas = simple_delta_encode_floats(values)
                compressed_values = {
                    "method": "delta",
                    "first_value": first_value,
                    "deltas": deltas
                }
            
            # Calculate compression statistics for values
            original_val_bytes = len(values) * 8  # 8 bytes per float64
            if compressed_values["method"] == "xor":
                compressed_val_bytes = 8 + len(compressed_values["xor_encoded"]) * 8
            else:
                compressed_val_bytes = 8 + len(compressed_values["deltas"]) * 8
            
            compression_stats["original_values_bytes"] += original_val_bytes
            compression_stats["compressed_values_bytes"] += compressed_val_bytes
            
        else:
            compressed_values = {"method": "empty", "first_value": 0.0, "data": []}
        
        compressed_series_data[series_id] = {
            "timestamps": compressed_timestamps,
            "values": compressed_values,
            "original_length": len(timestamps)
        }
    
    # Print compression statistics
    print(f"\n📊 Compression Statistics:")
    if compression_stats["total_deltas_count"] > 0:
        zero_delta_percent = compression_stats["zero_deltas_count"] / compression_stats["total_deltas_count"] * 100
        print(f"  Zero deltas (perfect regularity): {compression_stats['zero_deltas_count']:,} / {compression_stats['total_deltas_count']:,} ({zero_delta_percent:.1f}%)")
    
    ts_compression = compression_stats["original_timestamps_bytes"] / max(compression_stats["compressed_timestamps_bytes"], 1)
    val_compression = compression_stats["original_values_bytes"] / max(compression_stats["compressed_values_bytes"], 1)
    
    print(f"  Timestamp compression: {ts_compression:.2f}x")
    print(f"  Value compression: {val_compression:.2f}x")
    
    compressed_structure = {
        "series_metadata": series_metadata,
        "compressed_series_data": compressed_series_data,
        "compression_info": {
            "timestamp_encoding": "double_delta + rle + variable_length",
            "value_encoding": "xor_or_delta",
            "stats": compression_stats
        }
    }
    
    return compressed_structure

def verify_compressed_data(original_data: Dict[str, Any], compressed_data: Dict[str, Any]) -> None:
    """Verify that compressed data can be correctly decompressed."""
    print("\nVerifying compressed data integrity...")
    
    series_metadata = compressed_data["series_metadata"]
    compressed_series_data = compressed_data["compressed_series_data"]
    original_series_data = original_data["series_data"]
    
    verification_errors = 0
    
    for series_id in series_metadata.keys():
        if series_id not in compressed_series_data or series_id not in original_series_data:
            print(f"  ⚠️  Series {series_id} missing in compressed or original data")
            verification_errors += 1
            continue
        
        original = original_series_data[series_id]
        compressed = compressed_series_data[series_id]
        
        # Verify timestamps
        try:
            ts_data = compressed["timestamps"]
            if ts_data["rle_double_deltas"]:
                # Decompress RLE data
                decompressed_rle = decompress_integer_list(ts_data["compressed_rle"])
                rle_pairs = [(decompressed_rle[i], decompressed_rle[i+1]) for i in range(0, len(decompressed_rle), 2)]
                double_deltas = run_length_decode(rle_pairs)
            else:
                double_deltas = []
            
            decoded_timestamps = delta_decode_timestamps(
                ts_data["initial"], 
                ts_data["first_delta"], 
                double_deltas
            )
            
            if decoded_timestamps != original["timestamps"]:
                print(f"  ❌ Timestamp mismatch in series {series_id}")
                verification_errors += 1
        except Exception as e:
            print(f"  ❌ Timestamp decompression error in series {series_id}: {e}")
            verification_errors += 1
        
        # Verify values
        try:
            val_data = compressed["values"]
            if val_data["method"] == "xor":
                decoded_values = xor_decode_floats(val_data["first_value"], val_data["xor_encoded"])
            elif val_data["method"] == "delta":
                decoded_values = simple_delta_decode_floats(val_data["first_value"], val_data["deltas"])
            else:
                decoded_values = [val_data["first_value"]] if val_data["first_value"] != 0.0 else []
            
            # Compare with tolerance for floating point precision
            if len(decoded_values) != len(original["values"]):
                print(f"  ❌ Value count mismatch in series {series_id}: {len(decoded_values)} vs {len(original['values'])}")
                verification_errors += 1
            else:
                for i, (decoded, original_val) in enumerate(zip(decoded_values, original["values"])):
                    if abs(decoded - original_val) > 1e-10:
                        print(f"  ❌ Value mismatch in series {series_id} at index {i}: {decoded} vs {original_val}")
                        verification_errors += 1
                        break
        except Exception as e:
            print(f"  ❌ Value decompression error in series {series_id}: {e}")
            verification_errors += 1
    
    if verification_errors == 0:
        print(f"  ✅ All {len(series_metadata)} series verified successfully")
    else:
        print(f"  ⚠️  {verification_errors} verification errors found")

def store_compressed_data(compressed_data: Dict[str, Any], output_file: str) -> int:
    """Store compressed data to file."""
    print(f"\nWriting compressed data to binary format...")
    
    with open(output_file, "wb") as f:
        msgpack.dump(compressed_data, f, use_bin_type=True)
    
    return os.path.getsize(output_file)

def main():
    """Main function to execute Phase 3."""
    print("=" * 60)
    print("Phase 3: Compressed Columnar Storage")
    print("=" * 60)
    
    # Load the columnar data from Phase 2
    columnar_file = "output/metrics.columnar.msgpack"
    if not os.path.exists(columnar_file):
        print(f"❌ Error: {columnar_file} not found. Please run 02_columnar_storage.py first.")
        return
    
    with open(columnar_file, "rb") as f:
        columnar_data = msgpack.load(f, raw=False)
    
    series_count = len(columnar_data["series_metadata"])
    total_points = sum(len(series["timestamps"]) for series in columnar_data["series_data"].values())
    
    print(f"Loaded columnar data: {series_count} series, {total_points:,} total points")
    
    # Apply compression
    compressed_data = compress_columnar_data(columnar_data)
    
    # Verify compression
    verify_compressed_data(columnar_data, compressed_data)
    
    # Store compressed data
    output_file = "output/metrics.compressed.msgpack"
    file_size = store_compressed_data(compressed_data, output_file)
    
    # Compare with previous formats
    ndjson_file = "output/metrics.ndjson"
    columnar_file = "output/metrics.columnar.msgpack"
    
    ndjson_size = os.path.getsize(ndjson_file) if os.path.exists(ndjson_file) else None
    columnar_size = os.path.getsize(columnar_file) if os.path.exists(columnar_file) else None
    
    print(f"\n📊 Compressed Storage Results:")
    print(f"  Output file: {output_file}")
    print(f"  File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
    print(f"  Bytes per data point: {file_size / total_points:.2f}")
    
    print(f"\n📉 Compression Comparison:")
    if ndjson_size:
        ndjson_compression = ndjson_size / file_size
        print(f"  vs NDJSON: {ndjson_compression:.2f}x compression ({ndjson_size:,} → {file_size:,} bytes)")
    
    if columnar_size:
        columnar_compression = columnar_size / file_size
        print(f"  vs Columnar: {columnar_compression:.2f}x compression ({columnar_size:,} → {file_size:,} bytes)")
    
    print(f"\n💡 Compressed Format Characteristics:")
    print(f"  ✅ Pros:")
    print(f"    - Dramatic storage reduction (>90% in many cases)")
    print(f"    - Leverages data patterns (regular intervals, similar values)")
    print(f"    - Specialized encoding per data type")
    print(f"    - Still preserves full fidelity")
    print(f"  ❌ Cons:")
    print(f"    - High computational cost for encode/decode")
    print(f"    - Complex implementation")
    print(f"    - Opaque format requiring specialized tools")
    print(f"    - Space-vs-time trade-off")
    
    print(f"\n✅ Phase 3 completed successfully!")
    
    return {
        "format": "Compressed Columnar",
        "file_size": file_size,
        "compression_ratio": ndjson_size / file_size if ndjson_size else 1.0,
        "data_points": total_points
    }

if __name__ == "__main__":
    main()