"""
Encoders for time-series data compression.

This module provides various encoding techniques for compressing
time-series data efficiently.
"""

import struct
from typing import List, Tuple, Union

def delta_encode_timestamps(timestamps: List[int]) -> Tuple[int, int, List[int]]:
    """
    Double-delta encode timestamps.
    
    Args:
        timestamps: List of timestamps (integers)
        
    Returns:
        Tuple of (initial_timestamp, first_delta, double_deltas)
    """
    if len(timestamps) < 2:
        return timestamps[0] if timestamps else 0, 0, []
    
    if len(timestamps) == 2:
        return timestamps[0], timestamps[1] - timestamps[0], []
    
    initial_timestamp = timestamps[0]
    first_delta = timestamps[1] - timestamps[0]
    
    deltas = []
    for i in range(1, len(timestamps)):
        deltas.append(timestamps[i] - timestamps[i-1])
    
    double_deltas = []
    for i in range(1, len(deltas)):
        double_deltas.append(deltas[i] - deltas[i-1])
    
    return initial_timestamp, first_delta, double_deltas

def delta_decode_timestamps(initial_timestamp: int, first_delta: int, double_deltas: List[int]) -> List[int]:
    """
    Decode double-delta encoded timestamps.
    
    Args:
        initial_timestamp: The first timestamp
        first_delta: The first delta value
        double_deltas: List of double-delta values
        
    Returns:
        List of decoded timestamps
    """
    if not double_deltas:
        if first_delta == 0:
            return [initial_timestamp]
        return [initial_timestamp, initial_timestamp + first_delta]
    
    timestamps = [initial_timestamp, initial_timestamp + first_delta]
    current_delta = first_delta
    
    for double_delta in double_deltas:
        current_delta += double_delta
        timestamps.append(timestamps[-1] + current_delta)
    
    return timestamps

def run_length_encode(data: List[int]) -> List[Tuple[int, int]]:
    """
    Run-length encode a list of integers.
    
    Args:
        data: List of integers to encode
        
    Returns:
        List of (value, count) tuples
    """
    if not data:
        return []
    
    encoded = []
    current_value = data[0]
    current_count = 1
    
    for i in range(1, len(data)):
        if data[i] == current_value:
            current_count += 1
        else:
            encoded.append((current_value, current_count))
            current_value = data[i]
            current_count = 1
    
    encoded.append((current_value, current_count))
    return encoded

def run_length_decode(encoded_data: List[Tuple[int, int]]) -> List[int]:
    """
    Decode run-length encoded data.
    
    Args:
        encoded_data: List of (value, count) tuples
        
    Returns:
        List of decoded integers
    """
    decoded = []
    for value, count in encoded_data:
        decoded.extend([value] * count)
    return decoded

def xor_encode_floats(values: List[float]) -> Tuple[float, List[int]]:
    """
    Simple XOR encoding for float values (simplified Gorilla-like compression).
    
    Args:
        values: List of float values
        
    Returns:
        Tuple of (first_value, xor_encoded_values)
    """
    if not values:
        return 0.0, []
    
    if len(values) == 1:
        return values[0], []
    
    first_value = values[0]
    xor_encoded = []
    
    prev_bits = struct.unpack('>Q', struct.pack('>d', values[0]))[0]
    
    for i in range(1, len(values)):
        current_bits = struct.unpack('>Q', struct.pack('>d', values[i]))[0]
        xor_value = current_bits ^ prev_bits
        xor_encoded.append(xor_value)
        prev_bits = current_bits
    
    return first_value, xor_encoded

def xor_decode_floats(first_value: float, xor_encoded: List[int]) -> List[float]:
    """
    Decode XOR encoded float values.
    
    Args:
        first_value: The first float value
        xor_encoded: List of XOR encoded values
        
    Returns:
        List of decoded float values
    """
    if not xor_encoded:
        return [first_value]
    
    values = [first_value]
    prev_bits = struct.unpack('>Q', struct.pack('>d', first_value))[0]
    
    for xor_value in xor_encoded:
        current_bits = prev_bits ^ xor_value
        current_value = struct.unpack('>d', struct.pack('>Q', current_bits))[0]
        values.append(current_value)
        prev_bits = current_bits
    
    return values

def simple_delta_encode_floats(values: List[float]) -> Tuple[float, List[float]]:
    """
    Simple delta encoding for float values (alternative to XOR).
    
    Args:
        values: List of float values
        
    Returns:
        Tuple of (first_value, deltas)
    """
    if not values:
        return 0.0, []
    
    if len(values) == 1:
        return values[0], []
    
    first_value = values[0]
    deltas = []
    
    for i in range(1, len(values)):
        deltas.append(values[i] - values[i-1])
    
    return first_value, deltas

def simple_delta_decode_floats(first_value: float, deltas: List[float]) -> List[float]:
    """
    Decode simple delta encoded float values.
    
    Args:
        first_value: The first float value
        deltas: List of delta values
        
    Returns:
        List of decoded float values
    """
    if not deltas:
        return [first_value]
    
    values = [first_value]
    current_value = first_value
    
    for delta in deltas:
        current_value += delta
        values.append(current_value)
    
    return values

def compress_integer_list(data: List[int]) -> bytes:
    """
    Compress a list of integers using variable-length encoding.
    
    Args:
        data: List of integers to compress
        
    Returns:
        Compressed bytes
    """
    compressed = bytearray()
    
    for value in data:
        # Simple variable-length integer encoding
        # Positive numbers: encode directly
        # Negative numbers: encode as positive with sign bit
        if value >= 0:
            encoded_value = value << 1  # Shift left, sign bit = 0
        else:
            encoded_value = ((-value) << 1) | 1  # Shift left, sign bit = 1
        
        # Variable-length encoding (similar to LEB128)
        while encoded_value >= 128:
            compressed.append((encoded_value & 0x7F) | 0x80)
            encoded_value >>= 7
        compressed.append(encoded_value & 0x7F)
    
    return bytes(compressed)

def decompress_integer_list(data: bytes) -> List[int]:
    """
    Decompress a variable-length encoded list of integers.
    
    Args:
        data: Compressed bytes
        
    Returns:
        List of decoded integers
    """
    integers = []
    i = 0
    
    while i < len(data):
        value = 0
        shift = 0
        
        while i < len(data):
            byte = data[i]
            i += 1
            
            value |= (byte & 0x7F) << shift
            shift += 7
            
            if (byte & 0x80) == 0:
                break
        
        # Decode sign
        if value & 1:  # Sign bit is set
            integers.append(-(value >> 1))
        else:
            integers.append(value >> 1)
    
    return integers