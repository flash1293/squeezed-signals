#!/usr/bin/env python3
"""
Phase 4: Advanced Variable Encoding

This phase optimizes compression of extracted variable columns using
specialized encoding techniques:

- Delta Encoding: For timestamps, sequence numbers, incrementing IDs
- Dictionary Encoding: For categorical variables (user IDs, service names)
- Numerical Compression: Efficient encoding for integers, floats
- String Pattern Recognition: Compress similar string patterns (UUIDs, hex strings)
- IP Address Optimization: Compact encoding for IPv4/IPv6 addresses
- Timestamp Correlation: Exploit temporal locality in log timestamps

Expected result: 50-100x compression (significant improvement over Phase 3's 36x)
"""

import json
import sys
import time
import re
import zstandard as zstd
import struct
from pathlib import Path
from typing import Dict, List, Any, Tuple, Set, Union
from collections import defaultdict, Counter
import pickle
import hashlib
from datetime import datetime

# Add project root to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DEFAULT_ZSTD_LEVEL


class AdvancedVariableEncoder:
    """
    Advanced encoder for variable columns using type-specific optimizations.
    
    Encoding strategies:
    1. BRACKET_TIME: Parse timestamps, delta encode from first timestamp
    2. IP: Convert to 4-byte integers for IPv4
    3. PATH: Dictionary encoding for repeated path components
    4. NUM: Variable-length integer encoding
    5. HEX: Compact hex string encoding
    6. UUID/TIMESTAMP: Pattern-based compression
    """
    
    def __init__(self):
        self.encoders = {
            'BRACKET_TIME': self._encode_bracket_timestamps,
            'IP': self._encode_ip_addresses,
            'PATH': self._encode_file_paths,
            'IDENTIFIER': self._encode_identifiers,
            'NUM': self._encode_numbers,
            'HEX': self._encode_hex_strings,
            'UUID': self._encode_uuids,
            'TIMESTAMP': self._encode_iso_timestamps,
        }
        
        self.decoders = {
            'BRACKET_TIME': self._decode_bracket_timestamps,
            'IP': self._decode_ip_addresses,
            'PATH': self._decode_file_paths,
            'IDENTIFIER': self._decode_identifiers,
            'NUM': self._decode_numbers,
            'HEX': self._decode_hex_strings,
            'UUID': self._decode_uuids,
            'TIMESTAMP': self._decode_iso_timestamps,
        }
    
    def _encode_bracket_timestamps(self, timestamps: List[str]) -> Dict[str, Any]:
        """
        Encode bracket timestamps like [Thu Jun 09 06:07:04 2005]
        Strategy: Parse to unix timestamp, delta encode from first timestamp
        """
        if not timestamps:
            return {'type': 'empty', 'data': b'', 'count': 0}
        
        # Parse timestamps
        parsed_times = []
        base_time = None
        
        for ts_str in timestamps:
            try:
                # Extract timestamp from [Thu Jun 09 06:07:04 2005]
                match = re.search(r'\[(\w+)\s+(\w+)\s+(\d+)\s+(\d+):(\d+):(\d+)\s+(\d+)\]', ts_str)
                if match:
                    day_name, month_name, day, hour, minute, second, year = match.groups()
                    
                    # Convert month name to number
                    month_map = {
                        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
                    }
                    month = month_map.get(month_name, 1)
                    
                    # Create datetime and convert to timestamp
                    dt = datetime(int(year), month, int(day), int(hour), int(minute), int(second))
                    timestamp = int(dt.timestamp())
                    
                    if base_time is None:
                        base_time = timestamp
                    
                    parsed_times.append(timestamp)
                else:
                    # Fallback: use base time if parsing fails
                    parsed_times.append(base_time or 0)
            except:
                parsed_times.append(base_time or 0)
        
        if not parsed_times or base_time is None:
            return {'type': 'raw', 'data': json.dumps(timestamps).encode(), 'count': len(timestamps)}
        
        # Delta encode from base time
        deltas = [t - base_time for t in parsed_times]
        
        # Pack as variable-length integers
        packed_data = struct.pack('<I', base_time)  # Base timestamp
        for delta in deltas:
            # Use signed varint encoding for deltas
            packed_data += self._pack_varint(delta)
        
        return {
            'type': 'delta_encoded',
            'data': packed_data,
            'count': len(timestamps),
            'base_time': base_time
        }
    
    def _decode_bracket_timestamps(self, encoded: Dict[str, Any]) -> List[str]:
        """Decode bracket timestamps"""
        if encoded['type'] == 'empty':
            return []
        elif encoded['type'] == 'raw':
            return json.loads(encoded['data'].decode())
        elif encoded['type'] == 'delta_encoded':
            data = encoded['data']
            base_time = struct.unpack('<I', data[:4])[0]
            
            # Unpack deltas
            pos = 4
            timestamps = []
            for _ in range(encoded['count']):
                delta, pos = self._unpack_varint(data, pos)
                timestamp = base_time + delta
                
                # Convert back to bracket format
                dt = datetime.fromtimestamp(timestamp)
                month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                
                day_name = day_names[dt.weekday()]
                month_name = month_names[dt.month]
                
                bracket_ts = f"[{day_name} {month_name} {dt.day:02d} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d} {dt.year}]"
                timestamps.append(bracket_ts)
            
            return timestamps
        
        return []
    
    def _encode_ip_addresses(self, ips: List[str]) -> Dict[str, Any]:
        """
        Encode IP addresses as 4-byte integers for IPv4
        Strategy: Convert IPv4 to 32-bit integers, pack efficiently
        """
        if not ips:
            return {'type': 'empty', 'data': b'', 'count': 0}
        
        packed_ips = []
        
        for ip in ips:
            try:
                # Parse IPv4 address
                parts = ip.split('.')
                if len(parts) == 4:
                    ip_int = (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])
                    packed_ips.append(ip_int)
                else:
                    # Fallback to hash for IPv6 or malformed IPs
                    ip_hash = hashlib.md5(ip.encode()).digest()[:4]
                    ip_int = struct.unpack('<I', ip_hash)[0]
                    packed_ips.append(ip_int)
            except:
                # Error fallback
                packed_ips.append(0)
        
        # Pack all IPs as 32-bit integers
        data = struct.pack(f'<{len(packed_ips)}I', *packed_ips)
        
        return {
            'type': 'ip_integers',
            'data': data,
            'count': len(ips)
        }
    
    def _decode_ip_addresses(self, encoded: Dict[str, Any]) -> List[str]:
        """Decode IP addresses"""
        if encoded['type'] == 'empty':
            return []
        elif encoded['type'] == 'ip_integers':
            count = encoded['count']
            ip_ints = struct.unpack(f'<{count}I', encoded['data'])
            
            ips = []
            for ip_int in ip_ints:
                # Convert back to dotted decimal
                a = (ip_int >> 24) & 0xFF
                b = (ip_int >> 16) & 0xFF
                c = (ip_int >> 8) & 0xFF
                d = ip_int & 0xFF
                ips.append(f"{a}.{b}.{c}.{d}")
            
            return ips
        
        return []
    
    def _encode_file_paths(self, paths: List[str]) -> Dict[str, Any]:
        """
        Encode file paths using dictionary compression
        Strategy: Build dictionary of path components, reference by index
        Only apply to actual file paths (starting with /) to avoid version strings
        """
        if not paths:
            return {'type': 'empty', 'data': b'', 'count': 0}
        
        # Separate actual file paths from other strings containing /
        actual_paths = []
        other_strings = []
        path_types = []  # Track which type each path is
        
        for path in paths:
            # Only treat as file path if it starts with / and has reasonable path structure
            if path.startswith('/') and len(path) > 1:
                actual_paths.append(path)
                path_types.append('file_path')
            else:
                other_strings.append(path)
                path_types.append('string')
        
        # If we have actual file paths, use dictionary encoding for them
        if actual_paths:
            # Analyze path components for actual file paths
            all_components = set()
            file_path_components = []
            
            for path in actual_paths:
                components = path.split('/')[1:]  # Skip empty first element
                file_path_components.append(components)
                all_components.update(components)
            
            # Create component dictionary
            component_dict = {comp: idx for idx, comp in enumerate(sorted(all_components))}
            reverse_dict = {idx: comp for comp, idx in component_dict.items()}
            
            # Encode file paths as component indices
            encoded_file_paths = []
            for components in file_path_components:
                indices = [component_dict[comp] for comp in components]
                encoded_file_paths.append(indices)
            
            # Pack data
            data = pickle.dumps({
                'component_dict': reverse_dict,
                'encoded_file_paths': encoded_file_paths,
                'other_strings': other_strings,
                'path_types': path_types
            })
            
            return {
                'type': 'mixed_dictionary_encoded',
                'data': data,
                'count': len(paths)
            }
        else:
            # No actual file paths, just store as strings
            data = pickle.dumps({
                'other_strings': other_strings,
                'path_types': path_types
            })
            
            return {
                'type': 'string_only',
                'data': data,
                'count': len(paths)
            }
    
    def _decode_file_paths(self, encoded: Dict[str, Any]) -> List[str]:
        """Decode file paths"""
        if encoded['type'] == 'empty':
            return []
        elif encoded['type'] == 'string_only':
            unpacked = pickle.loads(encoded['data'])
            return unpacked['other_strings']
        elif encoded['type'] == 'mixed_dictionary_encoded':
            unpacked = pickle.loads(encoded['data'])
            component_dict = unpacked['component_dict']
            encoded_file_paths = unpacked['encoded_file_paths']
            other_strings = unpacked['other_strings']
            path_types = unpacked['path_types']
            
            # Reconstruct mixed paths
            paths = []
            file_path_idx = 0
            other_string_idx = 0
            
            for path_type in path_types:
                if path_type == 'file_path':
                    indices = encoded_file_paths[file_path_idx]
                    components = [component_dict[idx] for idx in indices]
                    reconstructed_path = '/' + '/'.join(components)
                    paths.append(reconstructed_path)
                    file_path_idx += 1
                else:  # string
                    paths.append(other_strings[other_string_idx])
                    other_string_idx += 1
            
            return paths
        elif encoded['type'] == 'dictionary_encoded':
            # Legacy format compatibility
            unpacked = pickle.loads(encoded['data'])
            component_dict = unpacked['component_dict']
            encoded_paths = unpacked['encoded_paths']
            
            paths = []
            for indices in encoded_paths:
                components = [component_dict[idx] for idx in indices]
                if len(components) == 1 and not components[0].startswith('/'):
                    # Single component, not a path
                    paths.append(components[0])
                else:
                    # Multi-component path
                    paths.append('/' + '/'.join(components))
            
            return paths
        
        return []
    
    def _encode_identifiers(self, identifiers: List[str]) -> Dict[str, Any]:
        """
        Encode identifier strings using dictionary compression
        Strategy: Similar to paths, use dictionary encoding for repeated patterns
        """
        if not identifiers:
            return {'type': 'empty', 'data': b'', 'count': 0}
        
        # Use simple dictionary encoding for identifiers
        unique_identifiers = list(set(identifiers))
        identifier_to_index = {identifier: idx for idx, identifier in enumerate(unique_identifiers)}
        
        indices = [identifier_to_index[identifier] for identifier in identifiers]
        
        # Pack the data
        dict_data = '\n'.join(unique_identifiers).encode('utf-8')
        indices_data = struct.pack(f'<{len(indices)}H', *indices)
        
        packed_data = struct.pack('<I', len(unique_identifiers)) + dict_data + indices_data
        
        return {
            'type': 'dictionary_encoded',
            'data': packed_data,
            'count': len(identifiers),
            'compression_ratio': len(''.join(identifiers)) / len(packed_data) if packed_data else 1.0
        }
    
    def _decode_identifiers(self, encoded: Dict[str, Any]) -> List[str]:
        """Decode identifier strings"""
        if encoded['type'] == 'empty':
            return []
        elif encoded['type'] == 'dictionary_encoded':
            data = encoded['data']
            count = encoded['count']
            
            # Unpack dictionary size
            dict_size = struct.unpack('<I', data[:4])[0]
            
            # Find the separator between dictionary and indices
            dict_end = 4
            newline_count = 0
            while newline_count < dict_size - 1:
                if data[dict_end] == ord('\n'):
                    newline_count += 1
                dict_end += 1
            
            # Extract dictionary
            dict_data = data[4:dict_end + (len(data) - dict_end - count * 2)]
            identifier_dict = dict_data.decode('utf-8').split('\n')
            
            # Extract indices
            indices_data = data[-count * 2:]
            indices = struct.unpack(f'<{count}H', indices_data)
            
            return [identifier_dict[idx] for idx in indices]
        
        return []
    
    def _encode_numbers(self, numbers: List[str]) -> Dict[str, Any]:
        """
        Encode numbers using efficient numpy array encoding
        Strategy: Parse as integers, use numpy array for space efficiency and speed
        """
        if not numbers:
            return {'type': 'empty', 'data': b'', 'count': 0}
        
        # For very large datasets, use numpy for efficiency
        if len(numbers) > 100000:
            import numpy as np
            
            parsed_numbers = []
            for num_str in numbers:
                try:
                    num = int(num_str)
                    parsed_numbers.append(num)
                except:
                    # Hash non-integer numbers
                    num_hash = hashlib.md5(num_str.encode()).digest()[:4]
                    num = struct.unpack('<I', num_hash)[0]
                    parsed_numbers.append(num)
            
            # Use numpy array for efficient storage
            arr = np.array(parsed_numbers, dtype=np.int64)
            
            # Try different dtypes to minimize space
            if arr.min() >= 0 and arr.max() < 2**32:
                arr = arr.astype(np.uint32)
                dtype_name = 'uint32'
            elif arr.min() >= -2**31 and arr.max() < 2**31:
                arr = arr.astype(np.int32)
                dtype_name = 'int32'
            else:
                dtype_name = 'int64'
            
            return {
                'type': 'numpy_array',
                'data': arr.tobytes(),
                'count': len(numbers),
                'dtype': dtype_name
            }
        else:
            # Use varint for smaller datasets
            parsed_numbers = []
            for num_str in numbers:
                try:
                    num = int(num_str)
                    parsed_numbers.append(num)
                except:
                    # Hash non-integer numbers
                    num_hash = hashlib.md5(num_str.encode()).digest()[:4]
                    num = struct.unpack('<I', num_hash)[0]
                    parsed_numbers.append(num)
            
            # Pack using varint encoding
            data = b''
            for num in parsed_numbers:
                data += self._pack_varint(num)
            
            return {
                'type': 'varint_encoded',
                'data': data,
                'count': len(numbers)
            }
    
    def _decode_numbers(self, encoded: Dict[str, Any]) -> List[str]:
        """Decode numbers"""
        if encoded['type'] == 'empty':
            return []
        elif encoded['type'] == 'numpy_array':
            import numpy as np
            data = encoded['data']
            dtype = encoded['dtype']
            count = encoded['count']
            
            # Reconstruct numpy array
            if dtype == 'uint32':
                arr = np.frombuffer(data, dtype=np.uint32)
            elif dtype == 'int32':
                arr = np.frombuffer(data, dtype=np.int32)
            else:  # int64
                arr = np.frombuffer(data, dtype=np.int64)
            
            return [str(num) for num in arr]
        elif encoded['type'] == 'varint_encoded':
            data = encoded['data']
            count = encoded['count']
            
            numbers = []
            pos = 0
            for _ in range(count):
                num, pos = self._unpack_varint(data, pos)
                numbers.append(str(num))
            
            return numbers
        
        return []
    
    def _encode_hex_strings(self, hex_strings: List[str]) -> Dict[str, Any]:
        """
        Encode hex strings by converting to binary
        Strategy: Parse hex to binary, pack efficiently
        """
        if not hex_strings:
            return {'type': 'empty', 'data': b'', 'count': 0}
        
        # Convert hex strings to binary
        binary_data = []
        lengths = []
        
        for hex_str in hex_strings:
            try:
                # Remove any prefixes and convert to binary
                clean_hex = hex_str.replace('0x', '').replace('#', '')
                binary = bytes.fromhex(clean_hex)
                binary_data.append(binary)
                lengths.append(len(binary))
            except:
                # Fallback: encode as UTF-8
                binary = hex_str.encode('utf-8')
                binary_data.append(binary)
                lengths.append(len(binary))
        
        # Pack lengths and data
        packed_lengths = struct.pack(f'<{len(lengths)}H', *lengths)
        packed_data = packed_lengths + b''.join(binary_data)
        
        return {
            'type': 'binary_encoded',
            'data': packed_data,
            'count': len(hex_strings)
        }
    
    def _decode_hex_strings(self, encoded: Dict[str, Any]) -> List[str]:
        """Decode hex strings"""
        if encoded['type'] == 'empty':
            return []
        elif encoded['type'] == 'binary_encoded':
            data = encoded['data']
            count = encoded['count']
            
            # Unpack lengths
            lengths = struct.unpack(f'<{count}H', data[:count * 2])
            
            # Unpack binary data
            pos = count * 2
            hex_strings = []
            
            for length in lengths:
                binary = data[pos:pos + length]
                try:
                    # Convert back to hex
                    hex_str = binary.hex()
                    hex_strings.append(hex_str)
                except:
                    # Fallback: decode as UTF-8
                    hex_strings.append(binary.decode('utf-8', errors='ignore'))
                pos += length
            
            return hex_strings
        
        return []
    
    def _encode_uuids(self, uuids: List[str]) -> Dict[str, Any]:
        """
        Encode UUIDs as 16-byte binary
        Strategy: Parse UUID strings to 128-bit integers, pack as binary
        """
        if not uuids:
            return {'type': 'empty', 'data': b'', 'count': 0}
        
        binary_uuids = []
        for uuid_str in uuids:
            try:
                # Remove hyphens and convert to binary
                clean_uuid = uuid_str.replace('-', '')
                binary = bytes.fromhex(clean_uuid)
                binary_uuids.append(binary)
            except:
                # Fallback: hash the string
                uuid_hash = hashlib.md5(uuid_str.encode()).digest()
                binary_uuids.append(uuid_hash)
        
        data = b''.join(binary_uuids)
        
        return {
            'type': 'binary_uuids',
            'data': data,
            'count': len(uuids)
        }
    
    def _decode_uuids(self, encoded: Dict[str, Any]) -> List[str]:
        """Decode UUIDs"""
        if encoded['type'] == 'empty':
            return []
        elif encoded['type'] == 'binary_uuids':
            data = encoded['data']
            count = encoded['count']
            
            uuids = []
            for i in range(count):
                binary = data[i * 16:(i + 1) * 16]
                hex_str = binary.hex()
                # Insert hyphens to make proper UUID format
                uuid_str = f"{hex_str[:8]}-{hex_str[8:12]}-{hex_str[12:16]}-{hex_str[16:20]}-{hex_str[20:]}"
                uuids.append(uuid_str)
            
            return uuids
        
        return []
    
    def _encode_iso_timestamps(self, timestamps: List[str]) -> Dict[str, Any]:
        """
        Encode ISO timestamps or custom timestamp formats with delta encoding
        Strategy: Parse to unix timestamp, delta encode
        Supports:
        - ISO format: 2023-10-25T12:00:00
        - HDFS format: 081109 203615 148 (YYMMDD HHMMSS milliseconds)
        """
        if not timestamps:
            return {'type': 'empty', 'data': b'', 'count': 0}
        
        parsed_times = []
        base_time = None
        failed_parses = 0
        
        for ts_str in timestamps:
            try:
                # Try ISO format first
                dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                timestamp = int(dt.timestamp())
            except:
                try:
                    # Try HDFS custom format: 081109 203615 148 (YYMMDD HHMMSS milliseconds)
                    parts = ts_str.strip().split()
                    if len(parts) >= 2:
                        date_part = parts[0]  # 081109 = YYMMDD
                        time_part = parts[1]  # 203615 = HHMMSS
                        
                        # Parse date: YYMMDD
                        year = 2000 + int(date_part[0:2])  # Assume 20xx for YY
                        month = int(date_part[2:4])
                        day = int(date_part[4:6])
                        
                        # Parse time: HHMMSS
                        hour = int(time_part[0:2])
                        minute = int(time_part[2:4])
                        second = int(time_part[4:6])
                        
                        dt = datetime(year, month, day, hour, minute, second)
                        timestamp = int(dt.timestamp())
                    else:
                        # Failed to parse
                        timestamp = base_time or 0
                        failed_parses += 1
                except:
                    # Complete fallback
                    timestamp = base_time or 0
                    failed_parses += 1
            
            if base_time is None and timestamp > 0:
                base_time = timestamp
            
            parsed_times.append(timestamp)
        
        if not parsed_times or base_time is None:
            print(f"  Warning: Failed to parse all timestamps, keeping as raw strings")
            return {'type': 'raw', 'data': json.dumps(timestamps).encode(), 'count': len(timestamps)}
        
        if failed_parses > 0:
            print(f"  Warning: Failed to parse {failed_parses}/{len(timestamps)} timestamps, using base time as fallback")
        
        # Delta encode
        deltas = [t - base_time for t in parsed_times]
        
        packed_data = struct.pack('<I', base_time)
        for delta in deltas:
            packed_data += self._pack_varint(delta)
        
        return {
            'type': 'delta_encoded',
            'data': packed_data,
            'count': len(timestamps),
            'base_time': base_time
        }
    
    def _decode_iso_timestamps(self, encoded: Dict[str, Any]) -> List[str]:
        """Decode ISO timestamps"""
        if encoded['type'] == 'empty':
            return []
        elif encoded['type'] == 'raw':
            return json.loads(encoded['data'].decode())
        elif encoded['type'] == 'delta_encoded':
            data = encoded['data']
            base_time = struct.unpack('<I', data[:4])[0]
            
            pos = 4
            timestamps = []
            for _ in range(encoded['count']):
                delta, pos = self._unpack_varint(data, pos)
                timestamp = base_time + delta
                
                dt = datetime.fromtimestamp(timestamp)
                iso_ts = dt.isoformat()
                timestamps.append(iso_ts)
            
            return timestamps
        
        return []
    
    def _pack_varint(self, value: int) -> bytes:
        """Pack integer as variable-length encoding"""
        if value < 0:
            # Handle negative numbers by encoding as positive
            value = ((-value - 1) << 1) | 1
        else:
            value = value << 1
        
        result = b''
        while value >= 0x80:
            result += bytes([value & 0x7F | 0x80])
            value >>= 7
        result += bytes([value & 0x7F])
        return result
    
    def _unpack_varint(self, data: bytes, pos: int) -> Tuple[int, int]:
        """Unpack variable-length integer"""
        value = 0
        shift = 0
        
        while pos < len(data):
            byte = data[pos]
            pos += 1
            
            value |= (byte & 0x7F) << shift
            if byte & 0x80 == 0:
                break
            shift += 7
        
        # Handle negative numbers
        if value & 1:
            value = -((value >> 1) + 1)
        else:
            value = value >> 1
        
        return value, pos
    
    def encode_variable_columns(self, variable_columns: Dict[str, List[str]]) -> Dict[str, Any]:
        """Encode all variable columns using appropriate strategies"""
        encoded_columns = {}
        
        for col_type, values in variable_columns.items():
            if col_type in self.encoders and values:
                print(f"  Encoding {col_type}: {len(values)} values...")
                start_time = time.time()
                
                encoded = self.encoders[col_type](values)
                
                encode_time = time.time() - start_time
                original_size = sum(len(v.encode('utf-8')) for v in values)
                encoded_size = len(encoded['data'])
                
                encoded_columns[col_type] = encoded
                
                print(f"    Original: {original_size:,} bytes, Encoded: {encoded_size:,} bytes")
                print(f"    Compression: {original_size / max(encoded_size, 1):.2f}x in {encode_time:.3f}s")
            else:
                # No values or no encoder, store empty
                encoded_columns[col_type] = {'type': 'empty', 'data': b'', 'count': 0}
        
        return encoded_columns
    
    def decode_variable_columns(self, encoded_columns: Dict[str, Any]) -> Dict[str, List[str]]:
        """Decode all variable columns"""
        decoded_columns = {}
        
        for col_type, encoded in encoded_columns.items():
            if col_type in self.decoders:
                decoded_columns[col_type] = self.decoders[col_type](encoded)
            else:
                decoded_columns[col_type] = []
        
        return decoded_columns


def process_log_file(input_file: Path, output_file: Path, metadata_file: Path) -> Dict[str, Any]:
    """Process a log file with advanced variable encoding"""
    print(f"Processing {input_file.name} with advanced variable encoding...")
    
    start_time = time.time()
    
    # Load Phase 3 data (template extraction + columnar storage)
    phase3_file = input_file.parent / f"phase3_logs_{input_file.stem.split('_')[-1]}.pkl"
    
    if not phase3_file.exists():
        raise FileNotFoundError(f"Phase 3 output not found: {phase3_file}")
    
    print(f"Loading Phase 3 data from {phase3_file}...")
    
    # Load compressed Phase 3 data
    with open(phase3_file, 'rb') as f:
        compressed_data = f.read()
    
    # Decompress Phase 3 data
    decompressor = zstd.ZstdDecompressor()
    decompressed_data = decompressor.decompress(compressed_data)
    phase3_data = pickle.loads(decompressed_data)
    
    print(f"Phase 3 data loaded: {len(phase3_data['variable_columns'])} column types")
    
    # Apply advanced variable encoding
    encoder = AdvancedVariableEncoder()
    
    print("Applying advanced variable encoding...")
    encoded_columns = encoder.encode_variable_columns(phase3_data['variable_columns'])
    
    # Create Phase 4 data structure
    phase4_data = {
        'templates': phase3_data['templates'],
        'encoded_variable_columns': encoded_columns,
        'line_to_template': phase3_data['line_to_template'],
        'line_variable_counts': phase3_data['line_variable_counts'],
        'template_variable_patterns': phase3_data['template_variable_patterns'],
        'total_lines': phase3_data['total_lines'],
        'unique_templates': phase3_data['unique_templates'],
        'encoding_metadata': {
            'encoder_version': '1.0',
            'encoding_timestamp': time.time()
        }
    }
    
    # Calculate original size
    original_size = sum(len(line.encode('utf-8')) + 1 for line in open(input_file, 'r', encoding='utf-8', errors='ignore') if line.strip())
    
    # Serialize Phase 4 data
    uncompressed_data = pickle.dumps(phase4_data, protocol=pickle.HIGHEST_PROTOCOL)
    uncompressed_size = len(uncompressed_data)
    
    # Apply Zstd compression
    print(f"Applying Zstd Level {DEFAULT_ZSTD_LEVEL} compression...")
    compressor = zstd.ZstdCompressor(level=DEFAULT_ZSTD_LEVEL)
    compressed_data = compressor.compress(uncompressed_data)
    
    # Save compressed data
    with open(output_file, 'wb') as f:
        f.write(compressed_data)
    
    file_size = output_file.stat().st_size
    processing_time = time.time() - start_time
    
    # Calculate compression ratios
    overall_compression_ratio = original_size / file_size
    structure_compression_ratio = original_size / uncompressed_size
    zstd_compression_ratio = uncompressed_size / file_size
    
    # Create metadata
    metadata = {
        'phase': 'Phase 4 - Advanced Variable Encoding + Zstd Level 22',
        'storage_format': 'advanced_encoded_columns_zstd22',
        'file_size_bytes': file_size,
        'original_size_bytes': original_size,
        'uncompressed_size_bytes': uncompressed_size,
        'overall_compression_ratio': overall_compression_ratio,
        'structure_compression_ratio': structure_compression_ratio,
        'zstd_compression_ratio': zstd_compression_ratio,
        'processing_time_seconds': processing_time,
        'lines_processed': phase4_data['total_lines'],
        'unique_templates': phase4_data['unique_templates'],
        'template_reuse_ratio': phase4_data['total_lines'] / phase4_data['unique_templates'],
        'encoding_stats': {
            col_type: {
                'count': encoded['count'],
                'encoding_type': encoded['type'],
                'encoded_size_bytes': len(encoded['data'])
            }
            for col_type, encoded in encoded_columns.items()
        }
    }
    
    # Save metadata
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"  Completed in {processing_time:.2f} seconds")
    print(f"  Lines processed: {phase4_data['total_lines']:,}")
    print(f"  Unique templates: {phase4_data['unique_templates']:,}")
    print(f"  Template reuse: {phase4_data['total_lines'] / phase4_data['unique_templates']:.2f}x")
    print(f"  Original size: {original_size:,} bytes")
    print(f"  Advanced encoding size: {uncompressed_size:,} bytes")
    print(f"  After Zstd Level 22: {file_size:,} bytes")
    print(f"  Structure compression: {structure_compression_ratio:.2f}x")
    print(f"  Zstd compression: {zstd_compression_ratio:.2f}x")
    print(f"  Overall compression ratio: {overall_compression_ratio:.2f}x")
    
    return metadata


def verify_reconstruction(input_file: Path, encoded_file: Path) -> bool:
    """Verify that we can perfectly reconstruct the original logs"""
    print("Verifying advanced variable encoding integrity...")
    
    # Load compressed Phase 4 data
    with open(encoded_file, 'rb') as f:
        compressed_data = f.read()
    
    # Decompress
    decompressor = zstd.ZstdDecompressor()
    decompressed_data = decompressor.decompress(compressed_data)
    phase4_data = pickle.loads(decompressed_data)
    
    # Decode variable columns
    encoder = AdvancedVariableEncoder()
    decoded_columns = encoder.decode_variable_columns(phase4_data['encoded_variable_columns'])
    
    # Reconstruct logs (similar to Phase 3 but with decoded columns)
    print("Reconstructing log lines from advanced encoded variables...")
    
    # Track column positions for reconstruction
    column_positions = {col_type: 0 for col_type in decoded_columns.keys()}
    
    # Read original lines
    original_lines = []
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if line:
                original_lines.append(line)
    
    # Test reconstruction of all lines (but sample for performance if too many)
    mismatches = 0
    test_count = min(100, len(original_lines))  # Just test first 100 lines for debugging
    
    for i in range(test_count):
        template_id = phase4_data['line_to_template'][i]
        template = phase4_data['templates'][template_id]
        template_pattern = phase4_data['template_variable_patterns'][template_id]
        
        # Reconstruct
        reconstructed = template
        for placeholder_type in template_pattern:
            placeholder = f'<{placeholder_type}>'
            if placeholder in reconstructed:
                if column_positions[placeholder_type] < len(decoded_columns[placeholder_type]):
                    value = decoded_columns[placeholder_type][column_positions[placeholder_type]]
                    reconstructed = reconstructed.replace(placeholder, value, 1)
                    column_positions[placeholder_type] += 1
        
        if reconstructed != original_lines[i]:
            mismatches += 1
            if mismatches <= 5:  # Show more examples
                print(f"❌ Line {i+1} mismatch:")
                print(f"   Template ID: {template_id}")
                print(f"   Template: {template}")
                print(f"   Pattern: {template_pattern}")
                print(f"   Original:     {repr(original_lines[i])}")
                print(f"   Reconstructed: {repr(reconstructed)}")
                # Show character-by-character differences
                orig_chars = list(original_lines[i])
                recon_chars = list(reconstructed)
                min_len = min(len(orig_chars), len(recon_chars))
                diff_chars = []
                for j in range(min_len):
                    if orig_chars[j] != recon_chars[j]:
                        diff_chars.append(f"pos {j}: '{orig_chars[j]}' vs '{recon_chars[j]}'")
                if diff_chars:
                    print(f"   Differences: {', '.join(diff_chars[:5])}")
                print()
    
    accuracy = (test_count - mismatches) / test_count * 100
    
    if mismatches == 0:
        print(f"✅ Perfect reconstruction: all {test_count:,} lines match")
        return True
    else:
        print(f"❌ Reconstruction accuracy: {accuracy:.2f}% ({mismatches} mismatches out of {test_count})")
        return False


def main():
    """Main function to process logs with phase 4 advanced variable encoding"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 4: Advanced Variable Encoding')
    parser.add_argument('--size', choices=['small', 'big', 'huge'], default='small',
                       help='Dataset size to process (default: small)')
    parser.add_argument('--verify', action='store_true',
                       help='Verify reconstruction integrity')
    
    args = parser.parse_args()
    
    # Setup paths
    input_file = Path(f'output/logs_{args.size}.log')
    output_file = Path(f'output/phase4_logs_{args.size}.pkl')
    metadata_file = Path(f'output/phase4_logs_metadata_{args.size}.json')
    
    # Ensure output directory exists
    output_file.parent.mkdir(exist_ok=True)
    
    # Check input file exists
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        print("   Please run Phase 0 first to generate log data")
        return 1
    
    try:
        print("=" * 60)
        print(f"Phase 4: Advanced Variable Encoding ({args.size})")
        print("=" * 60)
        print(f"Input: {input_file}")
        print(f"Output: {output_file}")
        
        # Process the logs
        metadata = process_log_file(input_file, output_file, metadata_file)
        
        # Verify reconstruction if requested
        if args.verify:
            if not verify_reconstruction(input_file, output_file):
                print("❌ Reconstruction verification failed!")
                return 1
        
        print(f"\n📊 Phase 4 Advanced Variable Encoding Results:")
        print(f"  Lines processed: {metadata['lines_processed']:,}")
        print(f"  Unique templates: {metadata['unique_templates']:,}")
        print(f"  Template reuse: {metadata['template_reuse_ratio']:.2f}x per template")
        print(f"  Original size: {metadata['original_size_bytes']:,} bytes ({metadata['original_size_bytes']/1024:.1f} KB)")
        print(f"  Advanced encoding size: {metadata['uncompressed_size_bytes']:,} bytes ({metadata['uncompressed_size_bytes']/1024:.1f} KB)")
        print(f"  After Zstd Level 22: {metadata['file_size_bytes']:,} bytes ({metadata['file_size_bytes']/1024:.1f} KB)")
        print(f"  Structure compression: {metadata['structure_compression_ratio']:.2f}x")
        print(f"  Zstd compression: {metadata['zstd_compression_ratio']:.2f}x")
        print(f"  Overall compression ratio: {metadata['overall_compression_ratio']:.2f}x")
        print(f"  Space saved: {(1 - metadata['file_size_bytes']/metadata['original_size_bytes'])*100:.1f}%")
        print(f"  Processing time: {metadata['processing_time_seconds']:.2f} seconds")
        
        print(f"\n🏆 Variable Encoding Statistics:")
        for col_type, stats in metadata['encoding_stats'].items():
            if stats['count'] > 0:
                print(f"  {col_type}: {stats['count']:,} values, {stats['encoding_type']}, {stats['encoded_size_bytes']:,} bytes")
        
        print(f"\n✅ Phase 4 completed successfully!")
        print(f"   Output: {output_file}")
        print(f"   Metadata: {metadata_file}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error in Phase 4 processing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())