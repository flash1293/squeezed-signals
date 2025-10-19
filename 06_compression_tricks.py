#!/usr/bin/env python3
"""
Phase 6: Compression Tricks + zstd - Specialized Algorithms with Compression

This script applies aggressive compression techniques to columnar data,
using specialized encodings for timestamps and values, followed by zstd 
compression for additional space savings.
"""

import os
import pickle
import msgpack
import struct
import zstandard as zstd
from typing import List, Dict, Any, Tuple
from lib.encoders import (
    delta_encode_timestamps, delta_decode_timestamps,
    run_length_encode, run_length_decode,
    xor_encode_floats, xor_decode_floats,
    simple_delta_encode_floats, simple_delta_decode_floats,
    compress_integer_list, decompress_integer_list
)

def detect_series_pattern(values: List[float]) -> str:
    """Detect the pattern in a series to choose optimal compression."""
    if not values or len(values) < 3:
        return "sparse"
    
    # Check for constant values (all identical)
    if all(v == values[0] for v in values):
        return "constant"
    
    # Check for mostly zeros or very sparse data
    zero_count = sum(1 for v in values if v == 0.0)
    if zero_count / len(values) > 0.5:  # More than 50% zeros
        return "sparse"
    
    # Check for repeating pattern (common in monitoring data)
    if len(values) >= 10:
        # Try different pattern lengths
        for pattern_len in [2, 3, 4, 5, 8, 12, 24]:
            if pattern_len * 3 <= len(values):  # Need at least 3 repetitions
                pattern = values[:pattern_len]
                is_repeating = True
                for i in range(pattern_len, len(values), pattern_len):
                    chunk = values[i:i+pattern_len]
                    if len(chunk) == pattern_len:
                        for j, val in enumerate(chunk):
                            if abs(val - pattern[j]) > 1e-10:
                                is_repeating = False
                                break
                    if not is_repeating:
                        break
                
                if is_repeating:
                    return f"repeat_{pattern_len}"
    
    # Check for linear trend (arithmetic progression)
    if len(values) >= 3:
        deltas = [values[i] - values[i-1] for i in range(1, len(values))]
        delta_variance = sum((d - deltas[0])**2 for d in deltas) / len(deltas)
        if delta_variance < 1e-10:  # Very low variance in deltas
            return "linear"
    
    # Check for quantized values (common in monitoring - only certain values appear)
    unique_values = list(set(values))
    if len(unique_values) <= min(20, len(values) // 10):  # Very few unique values
        return "quantized"
    
    # Check for smooth/similar values (good for XOR compression)
    value_variance = sum((v - values[0])**2 for v in values) / len(values)
    if value_variance < 100:  # Relatively low variance
        return "smooth"
    
    return "random"

def compress_series_optimized(timestamps: List[int], values: List[float], series_id: str) -> Tuple[Dict, Dict]:
    """Optimized compression for a single series based on detected patterns."""
    # Simple timestamp compression - just store first + deltas
    compressed_timestamps = None
    if timestamps:
        if len(timestamps) == 1:
            compressed_timestamps = {"method": "single", "value": timestamps[0]}
        else:
            # Check if all deltas are the same (regular intervals)
            deltas = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
            if all(d == deltas[0] for d in deltas):
                # Regular intervals - store first timestamp + interval + count
                compressed_timestamps = {
                    "method": "regular",
                    "start": timestamps[0], 
                    "interval": deltas[0],
                    "count": len(timestamps)
                }
            else:
                # Irregular intervals - use simple delta encoding
                compressed_timestamps = {
                    "method": "delta",
                    "start": timestamps[0],
                    "deltas": deltas
                }
    else:
        compressed_timestamps = {"method": "empty"}
    
    # Optimized value compression based on pattern
    compressed_values = None
    if values:
        pattern = detect_series_pattern(values)
        
        if pattern == "constant":
            # All values are the same
            compressed_values = {
                "method": "constant",
                "value": values[0],
                "count": len(values)
            }
            print(f"    Series {series_id}: Constant pattern - {len(values)} values = {values[0]}")
            
        elif pattern == "sparse":
            # Mostly zeros - store non-zero indices and values
            non_zero_data = [(i, v) for i, v in enumerate(values) if v != 0.0]
            if len(non_zero_data) < len(values) * 0.3:  # Less than 30% non-zero
                # Further optimize sparse data with delta compression on indices
                if len(non_zero_data) > 1:
                    indices = [item[0] for item in non_zero_data]
                    index_deltas = [indices[i] - indices[i-1] for i in range(1, len(indices))]
                    
                    compressed_values = {
                        "method": "sparse_optimized",
                        "length": len(values),
                        "first_index": indices[0],
                        "index_deltas": index_deltas,
                        "values": [item[1] for item in non_zero_data]
                    }
                    print(f"    Series {series_id}: Sparse optimized - {len(non_zero_data)} non-zero out of {len(values)} (delta-compressed indices)")
                else:
                    compressed_values = {
                        "method": "sparse",
                        "length": len(values),
                        "non_zero": non_zero_data
                    }
                    print(f"    Series {series_id}: Sparse pattern - {len(non_zero_data)} non-zero out of {len(values)}")
            else:
                # Fall back to delta encoding
                compressed_values = _compress_values_delta(values)
                print(f"    Series {series_id}: Delta fallback for sparse")
                
        elif pattern == "linear":
            # Linear trend - store first value + delta
            delta = values[1] - values[0] if len(values) > 1 else 0.0
            compressed_values = {
                "method": "linear",
                "start": values[0],
                "delta": delta,
                "count": len(values)
            }
            print(f"    Series {series_id}: Linear pattern - start={values[0]}, delta={delta}")
            
        elif pattern.startswith("repeat_"):
            # Repeating pattern
            pattern_len = int(pattern.split("_")[1])
            pattern_data = values[:pattern_len]
            compressed_values = {
                "method": "repeat",
                "pattern": pattern_data,
                "pattern_len": pattern_len,
                "total_count": len(values)
            }
            print(f"    Series {series_id}: Repeating pattern - {pattern_len} values repeated {len(values)//pattern_len} times")
            
        elif pattern == "quantized":
            # Quantized values - store unique values + indices  
            unique_values = list(set(values))
            value_to_index = {v: i for i, v in enumerate(unique_values)}
            indices = [value_to_index[v] for v in values]
            
            # Pack indices efficiently
            max_index = len(unique_values) - 1
            bits_needed = max_index.bit_length() if max_index > 0 else 1
            
            compressed_values = {
                "method": "quantized",
                "unique_values": unique_values,
                "indices": indices,
                "bits_per_index": bits_needed
            }
            print(f"    Series {series_id}: Quantized pattern - {len(unique_values)} unique values, {bits_needed} bits/index")
            
        else:
            # Use XOR or delta encoding for other patterns
            try:
                first_value, xor_data = xor_encode_floats(values)
                xor_result = {
                    "method": "xor",
                    "first": first_value,
                    "data": xor_data,
                    "count": len(values),  # Store expected count
                    "size": len(xor_data)
                }
            except:
                xor_result = None
            
            delta_result = _compress_values_delta(values)
            
            # Choose the better compression
            if xor_result and delta_result:
                if xor_result["size"] < len(delta_result["data"]):
                    compressed_values = xor_result
                    print(f"    Series {series_id}: XOR compression - {xor_result['size']} bytes")
                else:
                    compressed_values = delta_result  
                    print(f"    Series {series_id}: Delta compression - {len(delta_result['data'])} bytes")
            elif xor_result:
                compressed_values = xor_result
                print(f"    Series {series_id}: XOR compression - {xor_result['size']} bytes")
            else:
                compressed_values = delta_result
                print(f"    Series {series_id}: Delta compression - {len(delta_result['data'])} bytes")
    else:
        compressed_values = {"method": "empty"}
    
    return compressed_timestamps, compressed_values

def _compress_values_delta(values: List[float]) -> Dict:
    """Simple delta compression for values."""
    if not values:
        return {"method": "empty"}
    
    if len(values) == 1:
        return {"method": "single", "value": values[0]}
    
    # Store first value + deltas
    deltas = [values[i] - values[i-1] for i in range(1, len(values))]
    
    # Pack deltas efficiently
    delta_bytes = b''.join(struct.pack('>d', d) for d in deltas)
    
    return {
        "method": "delta",
        "first": values[0],
        "data": delta_bytes
    }

def compress_columnar_data(columnar_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply optimized compression to columnar data.
    
    Args:
        columnar_data: Original columnar format data
        
    Returns:
        Compressed columnar data
    """
    print("Applying optimized compression to columnar data...")
    
    series_metadata = columnar_data["series_metadata"]
    series_data = columnar_data["series_data"]
    
    compressed_series_data = {}
    
    total_original_bytes = 0
    total_compressed_bytes = 0
    
    for series_id, data in series_data.items():
        timestamps = data["timestamps"]
        values = data["values"]
        
        # Calculate original size
        original_bytes = len(timestamps) * 8 + len(values) * 8
        total_original_bytes += original_bytes
        
        # Compress the series
        compressed_timestamps, compressed_values = compress_series_optimized(
            timestamps, values, series_id
        )
        
        compressed_series_data[series_id] = {
            "timestamps": compressed_timestamps,
            "values": compressed_values,
            "original_length": len(timestamps)
        }
    
    # Estimate compressed size (rough calculation)
    compressed_msgpack = msgpack.packb({
        "series_metadata": series_metadata,
        "compressed_series_data": compressed_series_data
    }, use_bin_type=True)
    
    total_compressed_bytes = len(compressed_msgpack)
    
    compression_ratio = total_original_bytes / max(total_compressed_bytes, 1)
    
    print(f"\n📊 Optimized Compression Statistics:")
    print(f"  Original data size: {total_original_bytes:,} bytes")
    print(f"  Compressed data size: {total_compressed_bytes:,} bytes") 
    print(f"  Compression ratio: {compression_ratio:.2f}x")
    
    compressed_structure = {
        "series_metadata": series_metadata,
        "compressed_series_data": compressed_series_data,
        "compression_info": {
            "algorithm": "pattern_aware_optimized",
            "original_bytes": total_original_bytes,
            "compressed_bytes": total_compressed_bytes,
            "ratio": compression_ratio
        }
    }
    
    return compressed_structure

def decompress_timestamps(ts_data: Dict) -> List[int]:
    """Decompress timestamps from optimized format."""
    method = ts_data.get("method", "empty")
    
    if method == "empty":
        return []
    elif method == "single":
        return [ts_data["value"]]
    elif method == "regular":
        # Regular intervals
        start = ts_data["start"]
        interval = ts_data["interval"] 
        count = ts_data["count"]
        return [start + i * interval for i in range(count)]
    elif method == "delta":
        # Delta encoding
        start = ts_data["start"]
        deltas = ts_data["deltas"]
        timestamps = [start]
        for delta in deltas:
            timestamps.append(timestamps[-1] + delta)
        return timestamps
    else:
        raise ValueError(f"Unknown timestamp method: {method}")

def decompress_values(val_data: Dict) -> List[float]:
    """Decompress values from optimized format."""
    method = val_data.get("method", "empty")
    
    if method == "empty":
        return []
    elif method == "single":
        return [val_data["value"]]
    elif method == "constant":
        # All values are the same
        return [val_data["value"]] * val_data["count"]
    elif method == "sparse":
        # Sparse representation with non-zero indices
        result = [0.0] * val_data["length"]
        for idx, value in val_data["non_zero"]:
            result[idx] = value
        return result
    elif method == "sparse_optimized":
        # Sparse representation with delta-compressed indices
        result = [0.0] * val_data["length"]
        
        # Reconstruct indices from deltas
        indices = [val_data["first_index"]]
        for delta in val_data["index_deltas"]:
            indices.append(indices[-1] + delta)
        
        # Fill in non-zero values
        for i, value in enumerate(val_data["values"]):
            result[indices[i]] = value
        
        return result
    elif method == "linear":
        # Linear progression
        start = val_data["start"]
        delta = val_data["delta"]
        count = val_data["count"]
        return [start + i * delta for i in range(count)]
    elif method == "repeat":
        # Repeating pattern
        pattern = val_data["pattern"]
        pattern_len = val_data["pattern_len"]
        total_count = val_data["total_count"]
        
        result = []
        for i in range(total_count):
            result.append(pattern[i % pattern_len])
        return result
    elif method == "quantized":
        # Quantized values
        unique_values = val_data["unique_values"]
        indices = val_data["indices"]
        return [unique_values[idx] for idx in indices]
    elif method == "xor":
        # XOR compression
        expected_count = val_data.get("count", None)
        return xor_decode_floats(val_data["first"], val_data["data"], expected_count)
    elif method == "delta":
        # Delta compression
        deltas_bytes = val_data["data"]
        num_deltas = len(deltas_bytes) // 8
        deltas = [struct.unpack('>d', deltas_bytes[i*8:(i+1)*8])[0] for i in range(num_deltas)]
        
        values = [val_data["first"]]
        for delta in deltas:
            values.append(values[-1] + delta)
        return values
    else:
        raise ValueError(f"Unknown value method: {method}")

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
            decoded_timestamps = decompress_timestamps(compressed["timestamps"])
            
            if decoded_timestamps != original["timestamps"]:
                print(f"  ❌ Timestamp mismatch in series {series_id}")
                print(f"      Expected: {len(original['timestamps'])} items")
                print(f"      Got: {len(decoded_timestamps)} items")
                verification_errors += 1
        except Exception as e:
            print(f"  ❌ Timestamp decompression error in series {series_id}: {e}")
            verification_errors += 1
        
        # Verify values
        try:
            decoded_values = decompress_values(compressed["values"])
            
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
    """Main function to execute Phase 6."""
    print("=" * 60)
    print("Phase 6: Compression Tricks + zstd")
    print("=" * 60)
    
    # Load the columnar data from Phase 5
    columnar_file = "output/metrics.columnar.zst"
    if not os.path.exists(columnar_file):
        print(f"❌ Error: {columnar_file} not found. Please run 05_columnar_storage.py first.")
        return

    # Decompress and load columnar data
    with open(columnar_file, "rb") as f:
        compressed_data = f.read()
    
    decompressor = zstd.ZstdDecompressor()
    columnar_msgpack = decompressor.decompress(compressed_data)
    columnar_data = msgpack.loads(columnar_msgpack, raw=False)
    
    series_count = len(columnar_data["series_metadata"])
    total_points = sum(len(series["timestamps"]) for series in columnar_data["series_data"].values())
    
    print(f"Loaded columnar data from Phase 5: {series_count} series, {total_points:,} total points")
    
    # Apply compression tricks
    compressed_data = compress_columnar_data(columnar_data)
    
    # Verify compression
    verify_compressed_data(columnar_data, compressed_data)
    
    # Serialize compressed data and apply zstd
    print(f"\nWriting compressed data to binary format...")
    msgpack_data = msgpack.packb(compressed_data, use_bin_type=True)
    
    # Apply zstd compression
    print(f"Applying zstd compression to specialized compressed data...")
    compressor = zstd.ZstdCompressor(level=3)
    final_compressed_data = compressor.compress(msgpack_data)
    
    # Store final compressed data
    output_file = "output/metrics.compressed.zst"
    with open(output_file, "wb") as f:
        f.write(final_compressed_data)
    
    file_size = len(final_compressed_data)
    msgpack_size = len(msgpack_data)
    zstd_compression_ratio = msgpack_size / file_size
    
    # Compare with previous formats
    ndjson_file = "output/metrics.ndjson"
    columnar_file = "output/metrics.columnar.zst"
    
    ndjson_size = os.path.getsize(ndjson_file) if os.path.exists(ndjson_file) else None
    columnar_size = os.path.getsize(columnar_file) if os.path.exists(columnar_file) else None
    
    print(f"\n📊 Compression Tricks + zstd Results:")
    print(f"  Output file: {output_file}")
    print(f"  Specialized compression size: {msgpack_size:,} bytes")
    print(f"  Final compressed size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
    print(f"  zstd compression ratio: {zstd_compression_ratio:.2f}x")
    print(f"  Bytes per data point: {file_size / total_points:.2f}")
    
    print(f"\n📉 Compression Comparison:")
    if ndjson_size:
        ndjson_compression = ndjson_size / file_size
        print(f"  vs NDJSON: {ndjson_compression:.2f}x compression ({ndjson_size:,} → {file_size:,} bytes)")
    
    if columnar_size:
        columnar_compression = columnar_size / file_size
        print(f"  vs Columnar: {columnar_compression:.2f}x compression ({columnar_size:,} → {file_size:,} bytes)")
    
    print(f"\n✅ Phase 6 completed successfully!")
    
    return {
        "format": "Compressed Columnar",
        "file_size": file_size,
        "compression_ratio": ndjson_size / file_size if ndjson_size else 1.0,
        "data_points": total_points
    }

if __name__ == "__main__":
    import time
    start_time = time.time()
    result = main()
    end_time = time.time()
    
    if result:
        print(f"\n✅ Phase 6 completed in {end_time - start_time:.2f} seconds")
    else:
        print(f"\n❌ Phase 6 failed after {end_time - start_time:.2f} seconds")