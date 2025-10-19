"""
Encoders for time-series data compression.

This module provides various encoding techniques for compressing
time-series data efficiently.
"""

import struct
from typing import List, Tuple, Union

# Bit manipulation helpers for compressed encoding

class _BitWriter:
    """Helper class for writing bits to compressed data."""
    
    def __init__(self):
        self.data = bytearray()
        self.bit_buffer = 0
        self.bits_in_buffer = 0
    
    def write_bits(self, value: int, num_bits: int) -> None:
        """Write bits to the output."""
        if num_bits == 0:
            return
        
        # Mask value to ensure it fits in num_bits
        value &= (1 << num_bits) - 1
        
        # Add value to bit buffer
        self.bit_buffer = (self.bit_buffer << num_bits) | value
        self.bits_in_buffer += num_bits
        
        # Write complete bytes to data
        while self.bits_in_buffer >= 8:
            self.bits_in_buffer -= 8
            byte_value = (self.bit_buffer >> self.bits_in_buffer) & 0xFF
            self.data.append(byte_value)
            # Clear the written bits
            self.bit_buffer &= (1 << self.bits_in_buffer) - 1
    
    def flush(self) -> bytes:
        """Flush remaining bits and return the compressed data."""
        if self.bits_in_buffer > 0:
            # Pad with zeros and write final byte
            remaining_bits = 8 - self.bits_in_buffer
            self.bit_buffer <<= remaining_bits
            self.data.append(self.bit_buffer & 0xFF)
        
        result = bytes(self.data)
        # Reset for next use
        self.data = bytearray()
        self.bit_buffer = 0
        self.bits_in_buffer = 0
        return result

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
    
    first_value = values[0]
    writer = _BitWriter()
    
    prev_bits = struct.unpack('>Q', struct.pack('>d', values[0]))[0]
    
    for i in range(1, len(values)):
        current_bits = struct.unpack('>Q', struct.pack('>d', values[i]))[0]
        xor_value = current_bits ^ prev_bits
        
        if xor_value == 0:
            # Perfect match - store single bit '0'
            writer.write_bits(0, 1)
        else:
            # Non-zero XOR - store '1' + leading zeros + significant bits
            writer.write_bits(1, 1)
            
            # Count leading and trailing zeros
            leading_zeros = _count_leading_zeros(xor_value)
            trailing_zeros = _count_trailing_zeros(xor_value)
            
            # Significant bits (remove leading and trailing zeros)
            significant_bits = 64 - leading_zeros - trailing_zeros
            if significant_bits <= 0:
                significant_bits = 1
                leading_zeros = 63
                trailing_zeros = 0
            
            significant_value = xor_value >> trailing_zeros
            
            # Store: leading_zeros (6 bits) + significant_bits_count (6 bits) + significant_bits
            writer.write_bits(leading_zeros, 6)
            writer.write_bits(significant_bits, 6)
            writer.write_bits(significant_value, significant_bits)
        
        prev_bits = current_bits
    
    return first_value, writer.flush()

def xor_decode_floats(first_value: float, compressed_data: bytes, target_count: int = None) -> List[float]:
    """
    Decode XOR encoded float values from compressed bit data.
    
    Args:
        first_value: The first float value
        compressed_data: Compressed XOR data as bytes
        target_count: Expected number of values to decode (optional)
        
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
        # Keep reading until we run out of bits or reach target count
        while bit_reader.has_bits(1) and (target_count is None or len(values) < target_count):
            # Read control bit
            control_bit = bit_reader.read_bits(1)
            
            if control_bit == 0:
                # Perfect match - XOR value is 0
                xor_value = 0
            else:
                # Need at least 12 more bits (6 + 6) for metadata
                if not bit_reader.has_bits(12):
                    break
                
                # Read leading zeros (6 bits) and significant bits count (6 bits)
                leading_zeros = bit_reader.read_bits(6)
                significant_bits = bit_reader.read_bits(6)
                
                if significant_bits == 0:
                    xor_value = 0
                elif significant_bits > 64:
                    # Invalid data, stop reading
                    break
                else:
                    # Check if we have enough bits for the significant value
                    if not bit_reader.has_bits(significant_bits):
                        break
                    
                    # Read significant value
                    significant_value = bit_reader.read_bits(significant_bits)
                    
                    # Reconstruct XOR value
                    trailing_zeros = 64 - leading_zeros - significant_bits
                    if trailing_zeros < 0:
                        # Invalid data, stop reading
                        break
                    
                    xor_value = significant_value << trailing_zeros
            
            # Decode value
            current_bits = prev_bits ^ xor_value
            current_value = struct.unpack('>d', struct.pack('>Q', current_bits))[0]
            values.append(current_value)
            prev_bits = current_bits
    
    except (ValueError, struct.error):
        # If we encounter an error, stop reading
        pass
    
    return values

class _BitReader:
    """Helper class for reading bits from compressed data."""
    
    def __init__(self, data: bytes):
        self.data = data
        self.byte_pos = 0
        self.bit_pos = 0
    
    def has_bits(self, num_bits: int = 1) -> bool:
        """Check if there are enough bits available to read."""
        total_bits_available = (len(self.data) - self.byte_pos) * 8 - self.bit_pos
        return total_bits_available >= num_bits
    
    def read_bits(self, num_bits: int) -> int:
        """Read specified number of bits."""
        if num_bits == 0:
            return 0
        
        if not self.has_bits(num_bits):
            raise ValueError(f"Not enough bits available: need {num_bits}, have {(len(self.data) - self.byte_pos) * 8 - self.bit_pos}")
        
        result = 0
        bits_read = 0
        
        while bits_read < num_bits:
            # Get current byte
            current_byte = self.data[self.byte_pos]
            
            # Calculate how many bits we can read from current byte
            bits_available_in_byte = 8 - self.bit_pos
            bits_to_read = min(num_bits - bits_read, bits_available_in_byte)
            
            # Extract bits from the left side of the byte (MSB first)
            shift = bits_available_in_byte - bits_to_read
            mask = ((1 << bits_to_read) - 1) << shift
            bits = (current_byte & mask) >> shift
            
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
    Simple delta encoding for float values using direct serialization.
    
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
    
    # Calculate deltas
    deltas = []
    for i in range(1, len(values)):
        delta = values[i] - values[i-1]
        deltas.append(delta)
    
    # Simple approach: serialize deltas directly with compression for zeros
    compressed_data = _simple_compress_float_deltas(deltas)
    
    return first_value, compressed_data

def _simple_compress_float_deltas(deltas: List[float]) -> bytes:
    """Simple compression of float deltas - focus on zero compression."""
    if not deltas:
        return b''
    
    compressed = bytearray()
    
    # Write number of deltas first
    compressed.extend(struct.pack('>I', len(deltas)))
    
    i = 0
    while i < len(deltas):
        delta = deltas[i]
        
        if delta == 0.0:
            # Count consecutive zeros
            zero_count = 0
            j = i
            while j < len(deltas) and deltas[j] == 0.0:
                zero_count += 1
                j += 1
            
            # Store as: 0x00 (zero marker) + count (4 bytes)
            compressed.append(0x00)
            compressed.extend(struct.pack('>I', zero_count))
            i = j
        else:
            # Store as: 0x01 (non-zero marker) + double (8 bytes)
            compressed.append(0x01)
            compressed.extend(struct.pack('>d', delta))
            i += 1
    
    return bytes(compressed)

def simple_delta_decode_floats(first_value: float, compressed_data: bytes, target_count: int = None) -> List[float]:
    """
    Decode simple delta encoded float values from compressed data.
    
    Args:
        first_value: The first float value
        compressed_data: Compressed delta data as bytes
        target_count: Expected number of values to decode (optional)
        
    Returns:
        List of decoded float values
    """
    if not compressed_data:
        return [first_value]
    
    values = [first_value]
    current_value = first_value
    
    try:
        # Read number of deltas
        if len(compressed_data) < 4:
            return values
        
        num_deltas = struct.unpack('>I', compressed_data[:4])[0]
        
        # Validate target count if provided
        if target_count is not None and num_deltas != target_count - 1:
            # Mismatch in expected delta count, but continue decoding
            pass
        
        offset = 4
        deltas_read = 0
        
        while offset < len(compressed_data) and deltas_read < num_deltas:
            if offset >= len(compressed_data):
                break
            
            marker = compressed_data[offset]
            offset += 1
            
            if marker == 0x00:  # Zero marker
                if offset + 4 > len(compressed_data):
                    break
                
                zero_count = struct.unpack('>I', compressed_data[offset:offset+4])[0]
                offset += 4
                
                # Add zeros
                for _ in range(zero_count):
                    values.append(current_value)
                    deltas_read += 1
                    if deltas_read >= num_deltas:
                        break
            
            elif marker == 0x01:  # Non-zero marker
                if offset + 8 > len(compressed_data):
                    break
                
                delta = struct.unpack('>d', compressed_data[offset:offset+8])[0]
                offset += 8
                
                current_value += delta
                values.append(current_value)
                deltas_read += 1
            
            else:
                # Invalid marker, stop reading
                break
    
    except (ValueError, struct.error):
        # If we encounter an error, return what we have
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