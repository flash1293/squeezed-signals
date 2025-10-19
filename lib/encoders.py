"""
Encoders for time-series data compression.

This module provides various encoding techniques for compressing
time-series data efficiently.
"""

import struct
from typing import List, Tuple, Union

# Bit manipulation helpers for compressed encoding

def _write_bits(data: bytearray, value: int, num_bits: int) -> None:
    """Write bits to a bytearray, maintaining bit-level precision."""
    if not hasattr(_write_bits, 'bit_buffer'):
        _write_bits.bit_buffer = 0
        _write_bits.bits_in_buffer = 0
    
    # Add value to bit buffer
    _write_bits.bit_buffer = (_write_bits.bit_buffer << num_bits) | value
    _write_bits.bits_in_buffer += num_bits
    
    # Write complete bytes to data
    while _write_bits.bits_in_buffer >= 8:
        _write_bits.bits_in_buffer -= 8
        byte_value = (_write_bits.bit_buffer >> _write_bits.bits_in_buffer) & 0xFF
        data.append(byte_value)
        _write_bits.bit_buffer &= (1 << _write_bits.bits_in_buffer) - 1

def _flush_bits(data: bytearray) -> None:
    """Flush remaining bits in buffer to data."""
    if hasattr(_write_bits, 'bits_in_buffer') and _write_bits.bits_in_buffer > 0:
        # Pad with zeros and write final byte
        remaining_bits = 8 - _write_bits.bits_in_buffer
        _write_bits.bit_buffer <<= remaining_bits
        data.append(_write_bits.bit_buffer & 0xFF)
        _write_bits.bit_buffer = 0
        _write_bits.bits_in_buffer = 0

def _count_leading_zeros(value: int) -> int:
    """Count leading zeros in a 64-bit integer."""
    if value == 0:
        return 64
    count = 0
    mask = 1 << 63
    while count < 64 and (value & mask) == 0:
        count += 1
        mask >>= 1
    return count

def _count_trailing_zeros(value: int) -> int:
    """Count trailing zeros in a 64-bit integer."""
    if value == 0:
        return 64
    count = 0
    while count < 64 and (value & 1) == 0:
        count += 1
        value >>= 1
    return count

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

def xor_encode_floats(values: List[float]) -> Tuple[float, bytes]:
    """
    Real XOR encoding with bit-level compression (Gorilla-like compression).
    
    Args:
        values: List of float values
        
    Returns:
        Tuple of (first_value, compressed_xor_data)
    """
    if not values:
        return 0.0, b''
    
    if len(values) == 1:
        return values[0], b''
    
    # Reset bit buffer for new encoding
    _write_bits.bit_buffer = 0
    _write_bits.bits_in_buffer = 0
    
    first_value = values[0]
    compressed_data = bytearray()
    
    prev_bits = struct.unpack('>Q', struct.pack('>d', values[0]))[0]
    
    for i in range(1, len(values)):
        current_bits = struct.unpack('>Q', struct.pack('>d', values[i]))[0]
        xor_value = current_bits ^ prev_bits
        
        if xor_value == 0:
            # Perfect match - store single bit '0'
            _write_bits(compressed_data, 0, 1)
        else:
            # Non-zero XOR - store '1' + leading zeros + significant bits
            _write_bits(compressed_data, 1, 1)
            
            # Count leading and trailing zeros
            leading_zeros = _count_leading_zeros(xor_value)
            trailing_zeros = _count_trailing_zeros(xor_value)
            
            # Significant bits (remove leading and trailing zeros)
            significant_bits = 64 - leading_zeros - trailing_zeros
            significant_value = xor_value >> trailing_zeros
            
            # Store: leading_zeros (6 bits) + significant_bits_count (6 bits) + significant_bits
            _write_bits(compressed_data, leading_zeros, 6)
            _write_bits(compressed_data, significant_bits, 6)
            _write_bits(compressed_data, significant_value, significant_bits)
        
        prev_bits = current_bits
    
    # Flush any remaining bits
    _flush_bits(compressed_data)
    
    return first_value, bytes(compressed_data)

def xor_decode_floats(first_value: float, compressed_data: bytes) -> List[float]:
    """
    Decode XOR encoded float values from compressed bit data.
    
    Args:
        first_value: The first float value
        compressed_data: Compressed XOR data as bytes
        
    Returns:
        List of decoded float values
    """
    if not compressed_data:
        return [first_value]
    
    values = [first_value]
    prev_bits = struct.unpack('>Q', struct.pack('>d', first_value))[0]
    
    # Initialize bit reader
    bit_reader = _BitReader(compressed_data)
    
    try:
        while bit_reader.has_bits():
            # Read control bit
            control_bit = bit_reader.read_bits(1)
            
            if control_bit == 0:
                # Perfect match - XOR value is 0
                xor_value = 0
            else:
                # Read leading zeros (6 bits) and significant bits count (6 bits)
                leading_zeros = bit_reader.read_bits(6)
                significant_bits = bit_reader.read_bits(6)
                
                if significant_bits == 0:
                    xor_value = 0
                else:
                    # Read significant value
                    significant_value = bit_reader.read_bits(significant_bits)
                    
                    # Reconstruct XOR value
                    trailing_zeros = 64 - leading_zeros - significant_bits
                    xor_value = significant_value << trailing_zeros
            
            # Decode value
            current_bits = prev_bits ^ xor_value
            current_value = struct.unpack('>d', struct.pack('>Q', current_bits))[0]
            values.append(current_value)
            prev_bits = current_bits
    
    except Exception:
        # If we run out of bits or encounter an error, we're done
        pass
    
    return values

class _BitReader:
    """Helper class for reading bits from compressed data."""
    
    def __init__(self, data: bytes):
        self.data = data
        self.byte_pos = 0
        self.bit_pos = 0
    
    def has_bits(self) -> bool:
        """Check if there are more bits to read."""
        return self.byte_pos < len(self.data)
    
    def read_bits(self, num_bits: int) -> int:
        """Read specified number of bits."""
        if num_bits == 0:
            return 0
        
        result = 0
        bits_read = 0
        
        while bits_read < num_bits and self.has_bits():
            # Get current byte
            current_byte = self.data[self.byte_pos]
            
            # Calculate how many bits we can read from current byte
            bits_available = 8 - self.bit_pos
            bits_to_read = min(num_bits - bits_read, bits_available)
            
            # Extract bits
            mask = ((1 << bits_to_read) - 1) << (bits_available - bits_to_read)
            bits = (current_byte & mask) >> (bits_available - bits_to_read)
            
            # Add to result
            result = (result << bits_to_read) | bits
            bits_read += bits_to_read
            
            # Update position
            self.bit_pos += bits_to_read
            if self.bit_pos >= 8:
                self.bit_pos = 0
                self.byte_pos += 1
        
        return result

def simple_delta_encode_floats(values: List[float]) -> Tuple[float, bytes]:
    """
    Delta encoding with variable-length compression for float values.
    
    Args:
        values: List of float values
        
    Returns:
        Tuple of (first_value, compressed_delta_data)
    """
    if not values:
        return 0.0, b''
    
    if len(values) == 1:
        return values[0], b''
    
    first_value = values[0]
    deltas = []
    
    for i in range(1, len(values)):
        delta = values[i] - values[i-1]
        deltas.append(delta)
    
    # Compress deltas using variable-length encoding
    compressed_data = _compress_float_deltas(deltas)
    
    return first_value, compressed_data

def _compress_float_deltas(deltas: List[float]) -> bytes:
    """Compress a list of float deltas using variable-length encoding."""
    if not deltas:
        return b''
    
    # Reset bit buffer for new encoding
    _write_bits.bit_buffer = 0
    _write_bits.bits_in_buffer = 0
    
    compressed_data = bytearray()
    
    for delta in deltas:
        if delta == 0.0:
            # Zero delta - store single bit '0'
            _write_bits(compressed_data, 0, 1)
        else:
            # Non-zero delta - store '1' + compressed float
            _write_bits(compressed_data, 1, 1)
            
            # Convert to bytes and compress
            delta_bytes = struct.pack('>d', delta)
            
            # Count leading zero bytes
            leading_zero_bytes = 0
            for byte in delta_bytes:
                if byte == 0:
                    leading_zero_bytes += 1
                else:
                    break
            
            # Count trailing zero bytes
            trailing_zero_bytes = 0
            for byte in reversed(delta_bytes):
                if byte == 0:
                    trailing_zero_bytes += 1
                else:
                    break
            
            # Store significant bytes
            significant_bytes = 8 - leading_zero_bytes - trailing_zero_bytes
            if significant_bytes <= 0:
                significant_bytes = 1  # At least one byte
                leading_zero_bytes = 7
                trailing_zero_bytes = 0
            
            # Store: leading_zero_bytes (3 bits) + significant_bytes_count (3 bits) + significant_data
            _write_bits(compressed_data, leading_zero_bytes, 3)
            _write_bits(compressed_data, significant_bytes, 3)
            
            # Store significant bytes
            for i in range(leading_zero_bytes, 8 - trailing_zero_bytes):
                _write_bits(compressed_data, delta_bytes[i], 8)
    
    # Flush remaining bits
    _flush_bits(compressed_data)
    
    return bytes(compressed_data)

def simple_delta_decode_floats(first_value: float, compressed_data: bytes) -> List[float]:
    """
    Decode delta encoded float values from compressed data.
    
    Args:
        first_value: The first float value
        compressed_data: Compressed delta data as bytes
        
    Returns:
        List of decoded float values
    """
    if not compressed_data:
        return [first_value]
    
    values = [first_value]
    current_value = first_value
    
    # Initialize bit reader
    bit_reader = _BitReader(compressed_data)
    
    try:
        while bit_reader.has_bits():
            # Read control bit
            control_bit = bit_reader.read_bits(1)
            
            if control_bit == 0:
                # Zero delta
                delta = 0.0
            else:
                # Read leading zero bytes (3 bits) and significant bytes count (3 bits)
                leading_zero_bytes = bit_reader.read_bits(3)
                significant_bytes = bit_reader.read_bits(3)
                
                # Reconstruct delta bytes
                delta_bytes = bytearray(8)
                
                # Read significant bytes
                for i in range(leading_zero_bytes, leading_zero_bytes + significant_bytes):
                    if i < 8:
                        delta_bytes[i] = bit_reader.read_bits(8)
                
                # Convert back to float
                delta = struct.unpack('>d', bytes(delta_bytes))[0]
            
            # Add delta to get next value
            current_value += delta
            values.append(current_value)
    
    except Exception:
        # If we run out of bits or encounter an error, we're done
        pass
    
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