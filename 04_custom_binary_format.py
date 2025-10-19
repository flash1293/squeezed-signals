#!/usr/bin/env python3
"""
Phase 4: A Simple Custom Binary Format

This script formalizes the compressed data into a self-contained binary file format
with proper headers, index sections, and data sections, similar to real database files.
"""

import os
import struct
import msgpack
from typing import List, Dict, Any, Tuple, BinaryIO

# File format constants
MAGIC_NUMBER = b"METRICS!"  # 8 bytes
VERSION = 1                 # 4 bytes
HEADER_SIZE = 12           # Magic + Version

def write_file_header(f: BinaryIO) -> None:
    """Write the file header with magic number and version."""
    f.write(MAGIC_NUMBER)
    f.write(struct.pack('>I', VERSION))  # Big-endian 4-byte unsigned int

def read_file_header(f: BinaryIO) -> Tuple[bytes, int]:
    """Read and validate the file header."""
    magic = f.read(8)
    if magic != MAGIC_NUMBER:
        raise ValueError(f"Invalid magic number: {magic}")
    
    version = struct.unpack('>I', f.read(4))[0]
    return magic, version

def create_index_section(series_metadata: Dict[str, Any], data_offsets: Dict[str, int]) -> bytes:
    """
    Create the index section containing series metadata and data offsets.
    
    Args:
        series_metadata: Series metadata dictionary
        data_offsets: Dictionary mapping series_id to byte offset in data section
        
    Returns:
        Serialized index section as bytes
    """
    index_data = {
        "series_count": len(series_metadata),
        "series_index": {}
    }
    
    for series_id, metadata in series_metadata.items():
        index_data["series_index"][series_id] = {
            "metadata": metadata,
            "data_offset": data_offsets.get(series_id, 0),
            "data_size": 0  # Will be filled in when we know the size
        }
    
    return msgpack.packb(index_data, use_bin_type=True)

def write_data_section(f: BinaryIO, compressed_series_data: Dict[str, Any]) -> Dict[str, Tuple[int, int]]:
    """
    Write the data section and return offsets and sizes.
    
    Args:
        f: File handle positioned at start of data section
        compressed_series_data: Compressed series data
        
    Returns:
        Dictionary mapping series_id to (offset, size) tuples
    """
    data_info = {}
    
    for series_id, series_data in compressed_series_data.items():
        offset = f.tell()
        
        # Serialize the series data
        serialized_data = msgpack.packb(series_data, use_bin_type=True)
        
        # Write data length followed by data
        f.write(struct.pack('>I', len(serialized_data)))
        f.write(serialized_data)
        
        size = f.tell() - offset
        data_info[series_id] = (offset, size)
    
    return data_info

def create_custom_binary_format(compressed_data: Dict[str, Any], output_file: str) -> int:
    """
    Create a custom binary file format with proper structure.
    
    File layout:
    - Header (12 bytes): Magic number (8) + Version (4)
    - Index Section Length (4 bytes): Length of index section
    - Index Section: Series metadata + data offsets (MessagePack)
    - Data Section: Compressed series data blocks
    
    Args:
        compressed_data: Compressed data from Phase 3
        output_file: Path to output file
        
    Returns:
        File size in bytes
    """
    print(f"Creating custom binary format...")
    
    series_metadata = compressed_data["series_metadata"]
    compressed_series_data = compressed_data["compressed_series_data"]
    compression_info = compressed_data["compression_info"]
    
    with open(output_file, "wb") as f:
        # Write file header
        write_file_header(f)
        
        # Reserve space for index section length (will fill in later)
        index_length_pos = f.tell()
        f.write(struct.pack('>I', 0))  # Placeholder
        
        # Reserve space for data section offset (will fill in later)
        data_section_offset_pos = f.tell()
        f.write(struct.pack('>Q', 0))  # 8-byte offset placeholder
        
        # Write a temporary index section to calculate data offsets
        # (we'll rewrite this with correct offsets later)
        index_start = f.tell()
        temp_index = create_index_section(series_metadata, {})
        f.write(temp_index)
        
        # Calculate where data section starts
        data_section_start = f.tell()
        
        # Write data section and get actual offsets and sizes
        print(f"  Writing {len(compressed_series_data)} series data blocks...")
        data_info = write_data_section(f, compressed_series_data)
        
        # Update data offsets to be relative to data section start
        adjusted_data_offsets = {}
        updated_index_data = {
            "series_count": len(series_metadata),
            "series_index": {},
            "compression_info": compression_info,
            "data_section_offset": data_section_start
        }
        
        for series_id, (offset, size) in data_info.items():
            relative_offset = offset - data_section_start
            adjusted_data_offsets[series_id] = relative_offset
            
            updated_index_data["series_index"][series_id] = {
                "metadata": series_metadata[series_id],
                "data_offset": relative_offset,
                "data_size": size
            }
        
        # Serialize the final index section
        final_index = msgpack.packb(updated_index_data, use_bin_type=True)
        
        # Go back and write the correct index section length
        current_pos = f.tell()
        f.seek(index_length_pos)
        f.write(struct.pack('>I', len(final_index)))
        
        # Write the correct data section offset
        f.seek(data_section_offset_pos)
        f.write(struct.pack('>Q', data_section_start))
        
        # Rewrite the index section with correct data
        f.seek(index_start)
        f.write(final_index)
        
        # Return to end of file
        f.seek(current_pos)
    
    return os.path.getsize(output_file)

def read_and_verify_custom_format(file_path: str) -> Dict[str, Any]:
    """
    Read and verify the custom binary format file.
    
    Args:
        file_path: Path to the binary file
        
    Returns:
        Loaded data structure
    """
    print(f"Reading and verifying custom binary format...")
    
    with open(file_path, "rb") as f:
        # Read header
        magic, version = read_file_header(f)
        print(f"  Magic: {magic}, Version: {version}")
        
        # Read index section length
        index_length = struct.unpack('>I', f.read(4))[0]
        print(f"  Index section length: {index_length:,} bytes")
        
        # Read data section offset
        data_section_offset = struct.unpack('>Q', f.read(8))[0]
        print(f"  Data section offset: {data_section_offset:,}")
        
        # Read index section
        index_data = msgpack.unpackb(f.read(index_length), raw=False)
        series_count = index_data["series_count"]
        print(f"  Series count: {series_count}")
        
        # Verify we're at the expected data section offset
        current_pos = f.tell()
        if current_pos != data_section_offset:
            print(f"  ⚠️  Warning: Expected data section at {data_section_offset}, but at {current_pos}")
        
        # Read and verify a few series data blocks
        series_index = index_data["series_index"]
        verified_series = 0
        
        for series_id, series_info in list(series_index.items())[:3]:  # Verify first 3 series
            # Seek to series data
            f.seek(data_section_offset + series_info["data_offset"])
            
            # Read data length
            data_length = struct.unpack('>I', f.read(4))[0]
            
            # Verify length matches index
            expected_size = series_info["data_size"]
            actual_size = data_length + 4  # +4 for the length field itself
            
            if actual_size != expected_size:
                print(f"  ⚠️  Series {series_id} size mismatch: expected {expected_size}, got {actual_size}")
            else:
                # Read and deserialize the data
                series_data = msgpack.unpackb(f.read(data_length), raw=False)
                if "timestamps" in series_data and "values" in series_data:
                    verified_series += 1
        
        print(f"  ✅ Verified {verified_series} series data blocks")
    
    return index_data

def analyze_file_structure(file_path: str) -> None:
    """Analyze the structure and efficiency of the custom binary format."""
    print(f"\nAnalyzing file structure:")
    
    file_size = os.path.getsize(file_path)
    
    with open(file_path, "rb") as f:
        # Skip header
        f.seek(HEADER_SIZE)
        
        # Read section sizes
        index_length = struct.unpack('>I', f.read(4))[0]
        data_section_offset = struct.unpack('>Q', f.read(8))[0]
        
        header_size = HEADER_SIZE + 4 + 8  # Magic + version + index_length + data_offset
        index_size = index_length
        data_size = file_size - data_section_offset
        
        print(f"  File size: {file_size:,} bytes")
        print(f"  Header size: {header_size} bytes ({header_size/file_size*100:.1f}%)")
        print(f"  Index size: {index_size:,} bytes ({index_size/file_size*100:.1f}%)")
        print(f"  Data size: {data_size:,} bytes ({data_size/file_size*100:.1f}%)")
        
        # Read index to get series info
        f.seek(HEADER_SIZE + 4 + 8)  # Skip to index section
        index_data = msgpack.unpackb(f.read(index_length), raw=False)
        
        series_count = index_data["series_count"]
        avg_series_size = data_size / series_count if series_count > 0 else 0
        
        print(f"  Series count: {series_count}")
        print(f"  Average series data size: {avg_series_size:.1f} bytes")

def main():
    """Main function to execute Phase 4."""
    print("=" * 60)
    print("Phase 4: Custom Binary Format")
    print("=" * 60)
    
    # Load compressed data from Phase 3
    compressed_file = "output/metrics.compressed.msgpack"
    if not os.path.exists(compressed_file):
        print(f"❌ Error: {compressed_file} not found. Please run 03_compressed_columnar.py first.")
        return
    
    with open(compressed_file, "rb") as f:
        compressed_data = msgpack.load(f, raw=False)
    
    series_count = len(compressed_data["series_metadata"])
    print(f"Loaded compressed data: {series_count} series")
    
    # Create custom binary format
    output_file = "output/metrics.final.tsdb"
    file_size = create_custom_binary_format(compressed_data, output_file)
    
    # Verify the file
    loaded_index = read_and_verify_custom_format(output_file)
    
    # Analyze file structure
    analyze_file_structure(output_file)
    
    # Compare with previous formats
    ndjson_file = "output/metrics.ndjson"
    columnar_file = "output/metrics.columnar.msgpack"
    compressed_file = "output/metrics.compressed.msgpack"
    
    comparison_data = []
    if os.path.exists(ndjson_file):
        ndjson_size = os.path.getsize(ndjson_file)
        comparison_data.append(("NDJSON", ndjson_size))
    
    if os.path.exists(columnar_file):
        columnar_size = os.path.getsize(columnar_file)
        comparison_data.append(("Columnar", columnar_size))
    
    if os.path.exists(compressed_file):
        compressed_size = os.path.getsize(compressed_file)
        comparison_data.append(("Compressed", compressed_size))
    
    comparison_data.append(("Custom Binary", file_size))
    
    print(f"\n📊 Custom Binary Format Results:")
    print(f"  Output file: {output_file}")
    print(f"  File size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
    
    print(f"\n📉 Format Comparison:")
    if comparison_data:
        baseline_size = comparison_data[0][1]
        for format_name, size in comparison_data:
            compression_ratio = baseline_size / size if size > 0 else 0
            print(f"  {format_name}: {size:,} bytes ({compression_ratio:.2f}x)")
    
    print(f"\n💡 Custom Binary Format Characteristics:")
    print(f"  ✅ Pros:")
    print(f"    - Self-contained with metadata")
    print(f"    - Efficient random access via index")
    print(f"    - Version information for compatibility")
    print(f"    - Mimics real database file layout")
    print(f"    - No external dependencies to read structure")
    print(f"  ❌ Cons:")
    print(f"    - Maximum complexity")
    print(f"    - Requires dedicated reader/writer tools")
    print(f"    - Version management overhead")
    print(f"    - Not portable without custom parsers")
    
    print(f"\n✅ Phase 4 completed successfully!")
    
    return {
        "format": "Custom Binary Format",
        "file_size": file_size,
        "compression_ratio": baseline_size / file_size if comparison_data else 1.0,
        "data_points": sum(data.get("original_length", 0) for data in compressed_data["compressed_series_data"].values())
    }

if __name__ == "__main__":
    main()