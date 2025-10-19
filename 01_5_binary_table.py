#!/usr/bin/env python3
"""
Phase 1.5: Binary Table Format - Denormalized but Efficient

This script stores data in a binary table format that eliminates key repetition
but maintains row-based (denormalized) structure. This represents an intermediate
step between NDJSON and full columnar optimization.
"""

import os
import pickle
import struct
import msgpack
from typing import List, Dict, Any, Tuple

def create_string_table(data_points: List[Dict[str, Any]]) -> Tuple[Dict[str, int], List[str]]:
    """
    Create a string table to avoid repeating string values.
    
    Args:
        data_points: List of data point dictionaries
        
    Returns:
        Tuple of (string_to_id_map, id_to_string_list)
    """
    print("Building string table...")
    
    unique_strings = set()
    
    # Collect all unique strings
    for point in data_points:
        unique_strings.add(point["metric_name"])
        for key, value in point["labels"].items():
            unique_strings.add(key)
            unique_strings.add(value)
    
    # Create bidirectional mapping
    string_list = sorted(list(unique_strings))
    string_to_id = {string: idx for idx, string in enumerate(string_list)}
    
    print(f"  Created string table with {len(string_list)} unique strings")
    return string_to_id, string_list

def encode_binary_table_format(data_points: List[Dict[str, Any]]) -> bytes:
    """
    Encode data points in binary table format.
    
    Each row contains:
    - timestamp (8 bytes, big-endian uint64)
    - metric_name_id (2 bytes, big-endian uint16)  
    - value (8 bytes, big-endian double)
    - label_count (1 byte, uint8)
    - labels: pairs of (key_id, value_id) each 2 bytes
    
    Args:
        data_points: List of data point dictionaries
        
    Returns:
        Encoded binary data
    """
    string_to_id, string_list = create_string_table(data_points)
    
    print(f"Encoding {len(data_points):,} data points in binary table format...")
    
    # Encode header: magic + version + string table
    header = bytearray()
    header.extend(b"BINTABLE")  # 8-byte magic
    header.extend(struct.pack(">I", 1))  # 4-byte version
    
    # Encode string table
    string_table_data = msgpack.packb(string_list, use_bin_type=True)
    header.extend(struct.pack(">I", len(string_table_data)))  # string table length
    header.extend(string_table_data)
    
    # Encode data points
    data_section = bytearray()
    
    for i, point in enumerate(data_points):
        if i % 100000 == 0:
            print(f"  Encoded {i:,} / {len(data_points):,} points")
        
        # Timestamp (8 bytes)
        data_section.extend(struct.pack(">Q", point["timestamp"]))
        
        # Metric name ID (2 bytes)
        metric_id = string_to_id[point["metric_name"]]
        if metric_id > 65535:
            raise ValueError(f"Too many unique metric names (max 65536)")
        data_section.extend(struct.pack(">H", metric_id))
        
        # Value (8 bytes)
        data_section.extend(struct.pack(">d", point["value"]))
        
        # Labels
        labels = point["labels"]
        if len(labels) > 255:
            raise ValueError(f"Too many labels per point (max 255)")
        
        # Label count (1 byte)
        data_section.extend(struct.pack(">B", len(labels)))
        
        # Label key-value pairs (2 bytes each for key_id and value_id)
        for key, value in labels.items():
            key_id = string_to_id[key]
            value_id = string_to_id[value]
            if key_id > 65535 or value_id > 65535:
                raise ValueError(f"String table too large (max 65536 entries)")
            data_section.extend(struct.pack(">HH", key_id, value_id))
    
    # Combine header and data
    result = bytes(header) + bytes(data_section)
    
    print(f"  Binary table encoding completed")
    print(f"  Header size: {len(header):,} bytes")
    print(f"  Data size: {len(data_section):,} bytes")
    print(f"  Total size: {len(result):,} bytes")
    
    return result

def decode_binary_table_format(binary_data: bytes) -> List[Dict[str, Any]]:
    """
    Decode binary table format back to data points.
    
    Args:
        binary_data: Encoded binary data
        
    Returns:
        List of data point dictionaries
    """
    print("Decoding binary table format...")
    
    offset = 0
    
    # Read header
    magic = binary_data[offset:offset+8]
    offset += 8
    if magic != b"BINTABLE":
        raise ValueError(f"Invalid magic number: {magic}")
    
    version = struct.unpack(">I", binary_data[offset:offset+4])[0]
    offset += 4
    print(f"  Version: {version}")
    
    # Read string table
    string_table_length = struct.unpack(">I", binary_data[offset:offset+4])[0]
    offset += 4
    
    string_table_data = binary_data[offset:offset+string_table_length]
    offset += string_table_length
    
    string_list = msgpack.unpackb(string_table_data, raw=False)
    print(f"  String table: {len(string_list)} entries")
    
    # Decode data points
    data_points = []
    data_section = binary_data[offset:]
    data_offset = 0
    
    while data_offset < len(data_section):
        # Read timestamp (8 bytes)
        timestamp = struct.unpack(">Q", data_section[data_offset:data_offset+8])[0]
        data_offset += 8
        
        # Read metric name ID (2 bytes)
        metric_id = struct.unpack(">H", data_section[data_offset:data_offset+2])[0]
        data_offset += 2
        metric_name = string_list[metric_id]
        
        # Read value (8 bytes)
        value = struct.unpack(">d", data_section[data_offset:data_offset+8])[0]
        data_offset += 8
        
        # Read label count (1 byte)
        label_count = struct.unpack(">B", data_section[data_offset:data_offset+1])[0]
        data_offset += 1
        
        # Read labels
        labels = {}
        for _ in range(label_count):
            key_id = struct.unpack(">H", data_section[data_offset:data_offset+2])[0]
            data_offset += 2
            value_id = struct.unpack(">H", data_section[data_offset:data_offset+2])[0]
            data_offset += 2
            
            key = string_list[key_id]
            label_value = string_list[value_id]
            labels[key] = label_value
        
        data_point = {
            "timestamp": timestamp,
            "metric_name": metric_name,
            "value": value,
            "labels": labels
        }
        data_points.append(data_point)
    
    print(f"  Decoded {len(data_points):,} data points")
    return data_points

def analyze_binary_table_benefits(original_data: List[Dict[str, Any]], binary_size: int) -> None:
    """Analyze the benefits of binary table format."""
    print("\nAnalyzing binary table format benefits:")
    
    # Calculate string repetition elimination
    all_strings = []
    for point in original_data:
        all_strings.append(point["metric_name"])
        for key, value in point["labels"].items():
            all_strings.append(key)
            all_strings.append(value)
    
    total_string_chars = sum(len(s) for s in all_strings)
    unique_strings = set(all_strings)
    unique_string_chars = sum(len(s) for s in unique_strings)
    
    print(f"  String deduplication:")
    print(f"    Total string characters: {total_string_chars:,}")
    print(f"    Unique string characters: {unique_string_chars:,}")
    print(f"    Redundancy eliminated: {total_string_chars - unique_string_chars:,} chars")
    print(f"    String compression ratio: {total_string_chars / unique_string_chars:.2f}x")
    
    # Fixed-width benefits
    print(f"\n  Fixed-width encoding benefits:")
    print(f"    No field delimiters or quotes needed")
    print(f"    Predictable parsing performance")
    print(f"    No escaping of special characters")
    
    # Calculate bytes per data point
    bytes_per_point = binary_size / len(original_data)
    print(f"    Bytes per data point: {bytes_per_point:.2f}")

def main():
    """Main function to execute Phase 1.5."""
    print("=" * 60)
    print("Phase 1.5: Binary Table Format - Denormalized but Efficient")
    print("=" * 60)
    
    # Load the generated dataset
    raw_data_file = "output/raw_dataset.pkl"
    if not os.path.exists(raw_data_file):
        print(f"❌ Error: {raw_data_file} not found. Please run 00_generate_data.py first.")
        return
    
    with open(raw_data_file, "rb") as f:
        data_points = pickle.load(f)
    
    print(f"Loaded {len(data_points):,} data points from dataset")
    
    # Encode in binary table format
    binary_data = encode_binary_table_format(data_points)
    
    # Store the binary data
    output_file = "output/metrics.bintable.bin"
    with open(output_file, "wb") as f:
        f.write(binary_data)
    
    file_size = len(binary_data)
    
    # Verify by decoding
    print("\nVerifying binary table format...")
    decoded_points = decode_binary_table_format(binary_data)
    
    if len(decoded_points) != len(data_points):
        print(f"❌ Verification failed: {len(decoded_points)} != {len(data_points)}")
        return
    
    # Spot check a few data points
    verification_errors = 0
    for i in [0, len(data_points)//2, len(data_points)-1]:
        original = data_points[i]
        decoded = decoded_points[i]
        
        if (original["timestamp"] != decoded["timestamp"] or
            original["metric_name"] != decoded["metric_name"] or
            abs(original["value"] - decoded["value"]) > 1e-10 or
            original["labels"] != decoded["labels"]):
            print(f"❌ Verification error at index {i}")
            verification_errors += 1
    
    if verification_errors == 0:
        print("✅ Binary table format verification successful")
    
    # Analyze benefits
    analyze_binary_table_benefits(data_points, file_size)
    
    # Compare with NDJSON
    ndjson_file = "output/metrics.ndjson"
    ndjson_zst_file = "output/metrics.ndjson.zst"
    
    ndjson_size = os.path.getsize(ndjson_file) if os.path.exists(ndjson_file) else None
    ndjson_zst_size = os.path.getsize(ndjson_zst_file) if os.path.exists(ndjson_zst_file) else None
    
    print(f"\n📊 Binary Table Results:")
    print(f"  Output file: {output_file}")
    print(f"  File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
    print(f"  Bytes per data point: {file_size / len(data_points):.2f}")
    
    if ndjson_size:
        compression_ratio = ndjson_size / file_size
        print(f"\n📉 Compression vs NDJSON:")
        print(f"  NDJSON size: {ndjson_size:,} bytes")
        print(f"  Binary table size: {file_size:,} bytes")
        print(f"  Compression ratio: {compression_ratio:.2f}x")
    
    if ndjson_zst_size:
        compression_ratio_zst = ndjson_zst_size / file_size
        print(f"\n📉 Comparison vs NDJSON (zstd):")
        print(f"  NDJSON (zstd) size: {ndjson_zst_size:,} bytes")
        print(f"  Binary table size: {file_size:,} bytes")
        print(f"  Ratio: {compression_ratio_zst:.2f}x {'better' if compression_ratio_zst < 1 else 'worse'}")
    
    print(f"\n💡 Binary Table Characteristics:")
    print(f"  ✅ Pros:")
    print(f"    - Eliminates string repetition via string table")
    print(f"    - Fixed-width fields for predictable parsing")
    print(f"    - No JSON parsing overhead")
    print(f"    - More compact than text representation")
    print(f"    - Still maintains row-based structure")
    print(f"  ❌ Cons:")
    print(f"    - Not human-readable")
    print(f"    - Requires custom parser")
    print(f"    - Still denormalized (metadata repeated)")
    print(f"    - String table lookup overhead")
    
    print(f"\n✅ Phase 1.5 completed successfully!")
    
    return {
        "format": "Binary Table",
        "file_size": file_size,
        "compression_ratio": ndjson_size / file_size if ndjson_size else 1.0,
        "data_points": len(data_points)
    }

if __name__ == "__main__":
    main()