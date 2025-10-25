#!/usr/bin/env python3
"""
Phase 6: Enhanced Compression Tricks + zstd - Maximum Compression

This script applies extremely aggressive compression techniques with additional
optimizations for maximum space efficiency.
"""

import os
import sys
import pickle
import msgpack
import struct
import zstandard as zstd
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import Counter, defaultdict

# Add project root to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DEFAULT_ZSTD_LEVEL

from lib.encoders import (
    delta_encode_timestamps, delta_decode_timestamps,
    run_length_encode, run_length_decode,
    xor_encode_floats, xor_decode_floats,
    simple_delta_encode_floats, simple_delta_decode_floats,
    compress_integer_list, decompress_integer_list
)

def detect_advanced_patterns(values: List[float]) -> str:
    """Advanced pattern detection with more sophisticated algorithms."""
    if not values or len(values) < 3:
        return "sparse"
    
    # Check for constant values (all identical)
    if all(v == values[0] for v in values):
        return "constant"
    
    # Check for near-constant (within small tolerance)
    if len(values) > 1:
        value_range = max(values) - min(values)
        if value_range < 1e-6:
            return "near_constant"
    
    # Check for mostly zeros or very sparse data
    zero_count = sum(1 for v in values if abs(v) < 1e-10)
    if zero_count / len(values) > 0.3:  # More than 30% zeros
        return "sparse"
    
    # Check for power-of-2 values (common in computing metrics)
    powers_of_2 = 0
    for v in values:
        if v > 0 and v == 2 ** int(math.log2(v)):
            powers_of_2 += 1
    if powers_of_2 / len(values) > 0.7:
        return "power_of_2"
    
    # Check for integer values (can be compressed better)
    integer_count = sum(1 for v in values if v == int(v))
    if integer_count / len(values) > 0.8:
        return "mostly_integers"
    
    # Check for exponential pattern (common in growth metrics)
    if len(values) >= 5:
        try:
            ratios = [values[i+1] / values[i] for i in range(len(values)-1) if values[i] != 0]
            if len(ratios) >= 3:
                avg_ratio = sum(ratios) / len(ratios)
                ratio_variance = sum((r - avg_ratio)**2 for r in ratios) / len(ratios)
                if ratio_variance < 0.01 and 0.9 < avg_ratio < 1.1:  # Stable growth/decay
                    return "exponential"
        except:
            pass
    
    # Check for periodic/seasonal pattern
    if len(values) >= 20:
        # Try different periods
        for period in [6, 12, 24, 60, 300]:  # common monitoring periods
            if period < len(values) // 3:
                correlation_sum = 0
                comparisons = 0
                for i in range(period, len(values)):
                    correlation_sum += abs(values[i] - values[i - period])
                    comparisons += 1
                
                if comparisons > 0:
                    avg_diff = correlation_sum / comparisons
                    value_range = max(values) - min(values)
                    if value_range > 0 and avg_diff / value_range < 0.1:  # Very similar pattern
                        return f"periodic_{period}"
    
    # Check for quantized values with enhanced detection
    unique_values = list(set(values))
    if len(unique_values) <= min(50, len(values) // 5):  # Up to 50 unique values
        # Check if values follow a pattern (e.g., multiples of 5, 10, etc.)
        sorted_unique = sorted(unique_values)
        if len(sorted_unique) >= 3:
            diffs = [sorted_unique[i+1] - sorted_unique[i] for i in range(len(sorted_unique)-1)]
            # Check if differences are consistent
            if len(set(diffs)) <= 3:  # Very few different step sizes
                return "quantized_stepped"
        return "quantized"
    
    # Check for smooth/similar values (good for XOR compression)
    value_variance = sum((v - values[0])**2 for v in values) / len(values)
    if value_variance < 100:
        return "smooth"
    
    return "random"

def compress_with_dictionary(data: List[float]) -> Tuple[bytes, Dict]:
    """Compress using dictionary encoding for repeated values."""
    # Count value frequencies
    value_counts = Counter(data)
    
    # Build dictionary of most common values
    common_values = [value for value, count in value_counts.most_common(256)]
    value_to_index = {value: i for i, value in enumerate(common_values)}
    
    # Encode data
    compressed = bytearray()
    compressed.extend(struct.pack('>H', len(common_values)))  # Dictionary size
    
    # Store dictionary
    for value in common_values:
        compressed.extend(struct.pack('>d', value))
    
    # Store encoded data
    for value in data:
        if value in value_to_index:
            compressed.append(value_to_index[value])
        else:
            compressed.append(255)  # Escape code
            compressed.extend(struct.pack('>d', value))
    
    dictionary = {"values": common_values}
    return bytes(compressed), dictionary

def compress_timestamps_advanced(timestamps: List[int]) -> Dict:
    """Enhanced timestamp compression with multiple techniques."""
    if not timestamps:
        return {"method": "empty"}
    
    if len(timestamps) == 1:
        return {"method": "single", "value": timestamps[0]}
    
    # Analyze timestamp patterns
    deltas = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
    
    # Check for multiple regular intervals (switching between two intervals)
    if len(deltas) >= 4:
        delta_counts = Counter(deltas)
        if len(delta_counts) <= 2:  # At most 2 different intervals
            common_deltas = list(delta_counts.keys())
            if len(common_deltas) == 1:
                # Single interval
                return {
                    "method": "regular",
                    "start": timestamps[0],
                    "interval": common_deltas[0],
                    "count": len(timestamps)
                }
            elif len(common_deltas) == 2:
                # Alternating intervals - encode as pattern
                pattern = []
                for delta in deltas:
                    pattern.append(0 if delta == common_deltas[0] else 1)
                
                # Run-length encode the pattern
                rle_pattern = run_length_encode(pattern)
                
                return {
                    "method": "dual_interval",
                    "start": timestamps[0],
                    "intervals": common_deltas,
                    "pattern": rle_pattern
                }
    
    # Use regular delta compression with enhanced RLE
    return {
        "method": "delta_rle",
        "start": timestamps[0],
        "deltas": run_length_encode(deltas)
    }

def compress_values_advanced(values: List[float], series_id: str, report_details: bool = False) -> Dict:
    """Enhanced value compression with pattern-specific algorithms."""
    if not values:
        return {"method": "empty"}
    
    if len(values) == 1:
        return {"method": "single", "value": values[0]}
    
    pattern = detect_advanced_patterns(values)
    
    if report_details:
        print(f"\n  📊 Series Analysis:")
        print(f"     Pattern detected: {pattern}")
        if len(values) > 5:
            sample_str = f"[{values[0]:.2f}, {values[1]:.2f}, {values[2]:.2f}, {values[3]:.2f}, {values[4]:.2f}, ..., {values[-1]:.2f}]"
        else:
            sample_str = f"{[round(v, 2) for v in values]}"
        print(f"     Sample values: {sample_str}")
        print(f"     Value range: {min(values):.2f} to {max(values):.2f}")
        print(f"     Total points: {len(values)}")
    
    if pattern == "constant":
        result = {
            "method": "constant",
            "value": values[0],
            "count": len(values)
        }
        if report_details:
            # Estimate size: just storing one value + count
            estimated_size = 16  # double + int
            original_size = len(values) * 8
            print(f"     → Constant compression: {estimated_size} bytes (vs {original_size} bytes, {original_size/estimated_size:.1f}x)")
        return result
    
    elif pattern == "near_constant":
        # Store base value + small deviations
        base_value = values[0]
        deviations = [v - base_value for v in values]
        
        # Use minimal precision for deviations
        precision = max(1e-6, max(abs(d) for d in deviations) / 1000)
        quantized_deviations = [round(d / precision) for d in deviations]
        
        compressed_deviations = compress_integer_list(quantized_deviations)
        result = {
            "method": "near_constant",
            "base": base_value,
            "precision": precision,
            "deviations": compressed_deviations
        }
        if report_details:
            estimated_size = 24 + len(compressed_deviations)
            original_size = len(values) * 8
            print(f"     → Near-constant compression: {estimated_size} bytes (vs {original_size} bytes, {original_size/estimated_size:.1f}x)")
            print(f"        Base: {base_value:.6f}, Max deviation: {max(abs(d) for d in deviations):.6f}")
        return result
    
    elif pattern == "power_of_2":
        # Store as exponents
        exponents = []
        for v in values:
            if v > 0:
                exp = int(math.log2(v))
                exponents.append(exp)
            else:
                exponents.append(-1)  # Special marker for zero/negative
        
        compressed_exponents = compress_integer_list(exponents)
        fallback = [v for v in values if v <= 0 or v != 2 ** int(math.log2(v))]
        result = {
            "method": "power_of_2",
            "exponents": compressed_exponents,
            "fallback_values": fallback
        }
        if report_details:
            estimated_size = len(compressed_exponents) + len(fallback) * 8
            original_size = len(values) * 8
            print(f"     → Power-of-2 compression: {estimated_size} bytes (vs {original_size} bytes, {original_size/estimated_size:.1f}x)")
            print(f"        Fallback values: {len(fallback)}")
        return result
    
    elif pattern == "mostly_integers":
        # Split into integer and fractional parts
        integer_parts = [int(v) for v in values]
        fractional_parts = [v - int(v) for v in values]
        
        # Check if fractional parts are mostly zero
        non_zero_fractions = [(i, f) for i, f in enumerate(fractional_parts) if abs(f) > 1e-10]
        
        compressed_integers = compress_integer_list(integer_parts)
        result = {
            "method": "mostly_integers",
            "integers": compressed_integers,
            "fractional_indices": [i for i, f in non_zero_fractions],
            "fractional_values": [f for i, f in non_zero_fractions]
        }
        if report_details:
            estimated_size = len(compressed_integers) + len(non_zero_fractions) * 12
            original_size = len(values) * 8
            print(f"     → Mostly-integers compression: {estimated_size} bytes (vs {original_size} bytes, {original_size/estimated_size:.1f}x)")
            print(f"        Non-zero fractions: {len(non_zero_fractions)}/{len(values)}")
        return result
    
    elif pattern == "exponential":
        # Store first value + ratios
        base_value = values[0]
        ratios = [values[i+1] / values[i] for i in range(len(values)-1) if values[i] != 0]
        avg_ratio = sum(ratios) / len(ratios)
        
        # Store deviations from average ratio
        ratio_deviations = [r - avg_ratio for r in ratios]
        
        result = {
            "method": "exponential",
            "base": base_value,
            "avg_ratio": avg_ratio,
            "ratio_deviations": ratio_deviations
        }
        if report_details:
            estimated_size = 24 + len(ratio_deviations) * 8
            original_size = len(values) * 8
            print(f"     → Exponential compression: {estimated_size} bytes (vs {original_size} bytes, {original_size/estimated_size:.1f}x)")
            print(f"        Avg ratio: {avg_ratio:.6f}")
        return result
    
    elif pattern.startswith("periodic_"):
        period = int(pattern.split("_")[1])
        # Store one period + deviations
        base_pattern = values[:period]
        deviations = []
        
        for i in range(period, len(values)):
            pattern_index = i % period
            deviation = values[i] - base_pattern[pattern_index]
            deviations.append(deviation)
        
        result = {
            "method": "periodic",
            "period": period,
            "base_pattern": base_pattern,
            "deviations": deviations
        }
        if report_details:
            estimated_size = period * 8 + len(deviations) * 8
            original_size = len(values) * 8
            print(f"     → Periodic compression (period={period}): {estimated_size} bytes (vs {original_size} bytes, {original_size/estimated_size:.1f}x)")
        return result
    
    elif pattern == "quantized" or pattern == "quantized_stepped":
        # Dictionary encoding for quantized values
        compressed_data, dictionary = compress_with_dictionary(values)
        result = {
            "method": "dictionary",
            "data": compressed_data,
            "dictionary": dictionary
        }
        if report_details:
            original_size = len(values) * 8
            compressed_size = len(compressed_data)
            print(f"     → Dictionary compression: {compressed_size} bytes (vs {original_size} bytes, {original_size/compressed_size:.1f}x)")
            print(f"        Dictionary size: {len(dictionary['values'])} unique values")
        return result
    
    elif pattern == "sparse":
        # Enhanced sparse encoding with delta-compressed indices
        non_zero_data = [(i, v) for i, v in enumerate(values) if abs(v) > 1e-10]
        
        if len(non_zero_data) < len(values) * 0.3:
            if len(non_zero_data) > 1:
                indices = [item[0] for item in non_zero_data]
                index_deltas = [indices[i] - indices[i-1] for i in range(1, len(indices))]
                compressed_deltas = compress_integer_list(index_deltas)
                
                result = {
                    "method": "sparse_optimized",
                    "length": len(values),
                    "first_index": indices[0],
                    "index_deltas": compressed_deltas,
                    "values": [item[1] for item in non_zero_data]
                }
                if report_details:
                    estimated_size = 16 + len(compressed_deltas) + len(non_zero_data) * 8
                    original_size = len(values) * 8
                    print(f"     → Sparse compression: {estimated_size} bytes (vs {original_size} bytes, {original_size/estimated_size:.1f}x)")
                    print(f"        Non-zero values: {len(non_zero_data)}/{len(values)} ({len(non_zero_data)/len(values)*100:.1f}%)")
                return result
            else:
                result = {
                    "method": "sparse",
                    "length": len(values),
                    "non_zero": non_zero_data
                }
                if report_details:
                    estimated_size = 24
                    original_size = len(values) * 8
                    print(f"     → Sparse compression (single value): {estimated_size} bytes (vs {original_size} bytes, {original_size/estimated_size:.1f}x)")
                return result
        else:
            # Fall back to other methods
            pass
    
    # Try enhanced XOR compression vs delta compression
    xor_result = None
    delta_result = None
    
    try:
        first_value, xor_data = xor_encode_floats(values)
        xor_result = {
            "method": "xor",
            "first": first_value,
            "data": xor_data,
            "count": len(values),
            "size": len(xor_data)
        }
    except:
        pass
    
    # Enhanced delta compression
    delta_result = _compress_values_delta_enhanced(values)
    
    # Choose the better compression
    original_size = len(values) * 8
    
    if xor_result and delta_result:
        xor_size = xor_result["size"]
        delta_size = len(delta_result.get("data", b""))
        
        if xor_size < delta_size:
            if report_details:
                print(f"     → XOR compression: {xor_size} bytes (vs {original_size} bytes, {original_size/xor_size:.1f}x)")
                print(f"        Chosen over delta ({delta_size} bytes)")
            else:
                print(f"    Series {series_id}: XOR compression - {xor_size} bytes ({pattern})")
            return xor_result
        else:
            if report_details:
                print(f"     → Delta compression: {delta_size} bytes (vs {original_size} bytes, {original_size/delta_size:.1f}x)")
                print(f"        Chosen over XOR ({xor_size} bytes)")
            else:
                print(f"    Series {series_id}: Enhanced delta compression - {delta_size} bytes ({pattern})")
            return delta_result
    elif xor_result:
        xor_size = xor_result["size"]
        if report_details:
            print(f"     → XOR compression: {xor_size} bytes (vs {original_size} bytes, {original_size/xor_size:.1f}x)")
        else:
            print(f"    Series {series_id}: XOR compression - {xor_size} bytes ({pattern})")
        return xor_result
    else:
        if report_details:
            delta_size = len(delta_result.get("data", b"")) if delta_result else original_size
            print(f"     → Enhanced delta compression: {delta_size} bytes (vs {original_size} bytes, {original_size/max(delta_size, 1):.1f}x)")
        else:
            print(f"    Series {series_id}: Enhanced delta compression ({pattern})")
        return delta_result or {"method": "uncompressed", "values": values}

def _compress_values_delta_enhanced(values: List[float]) -> Dict:
    """Enhanced delta compression with better handling of small values."""
    if not values:
        return {"method": "empty"}
    
    if len(values) == 1:
        return {"method": "single", "value": values[0]}
    
    # Calculate deltas
    deltas = [values[i] - values[i-1] for i in range(1, len(values))]
    
    # Analyze delta patterns
    zero_deltas = sum(1 for d in deltas if abs(d) < 1e-10)
    
    if zero_deltas > len(deltas) * 0.7:
        # Many zero deltas - use RLE
        rle_deltas = run_length_encode([0 if abs(d) < 1e-10 else 1 for d in deltas])
        non_zero_deltas = [d for d in deltas if abs(d) >= 1e-10]
        
        return {
            "method": "delta_rle",
            "first": values[0],
            "rle_pattern": rle_deltas,
            "non_zero_deltas": non_zero_deltas
        }
    else:
        # Regular delta compression
        delta_bytes = b''.join(struct.pack('>d', d) for d in deltas)
        return {
            "method": "delta",
            "first": values[0],
            "data": delta_bytes
        }

def compress_metadata_aggressively(series_metadata: Dict) -> Dict:
    """Aggressively compress series metadata."""
    # Extract all label keys and values
    all_label_keys = set()
    all_label_values = set()
    all_metric_names = set()
    
    for series_id, metadata in series_metadata.items():
        # Handle both "metric_name" and "name" for compatibility
        metric_name = metadata.get("metric_name") or metadata.get("name")
        if metric_name:
            all_metric_names.add(metric_name)
        
        for key, value in metadata["labels"].items():
            all_label_keys.add(key)
            all_label_values.add(value)
    
    # Create dictionaries for compression
    metric_name_dict = list(all_metric_names)
    label_key_dict = list(all_label_keys)
    label_value_dict = list(all_label_values)
    
    # Create reverse mappings
    metric_name_to_id = {name: i for i, name in enumerate(metric_name_dict)}
    label_key_to_id = {key: i for i, key in enumerate(label_key_dict)}
    label_value_to_id = {value: i for i, value in enumerate(label_value_dict)}
    
    # Compress series metadata
    compressed_series = {}
    for series_id, metadata in series_metadata.items():
        metric_name = metadata.get("metric_name") or metadata.get("name")
        metric_id = metric_name_to_id[metric_name] if metric_name else 0
        
        label_pairs = []
        for key, value in metadata["labels"].items():
            key_id = label_key_to_id[key]
            value_id = label_value_to_id[value]
            label_pairs.append((key_id, value_id))
        
        compressed_series[series_id] = {
            "metric_id": metric_id,
            "label_pairs": label_pairs
        }
    
    return {
        "dictionaries": {
            "metric_names": metric_name_dict,
            "label_keys": label_key_dict,
            "label_values": label_value_dict
        },
        "compressed_series": compressed_series
    }

def compress_columnar_data_enhanced(columnar_data: Dict[str, Any]) -> Dict[str, Any]:
    """Apply maximum compression with all enhanced techniques."""
    print("Applying maximum compression with enhanced techniques...")
    
    series_metadata = columnar_data["series_metadata"]
    series_data = columnar_data["series_data"]
    
    # Compress metadata aggressively
    compressed_metadata = compress_metadata_aggressively(series_metadata)
    
    compressed_series_data = {}
    
    total_original_bytes = 0
    total_compressed_bytes = 0
    
    # Track compression method statistics
    method_stats = defaultdict(lambda: {"count": 0, "original_bytes": 0, "compressed_bytes": 0})
    timestamp_method_stats = defaultdict(int)
    
    # Track per-series statistics
    series_stats = []
    
    print(f"\n{'='*120}")
    print(f"Compressing {len(series_data)} time series...")
    print(f"{'='*120}")
    
    # Print table header
    print(f"\n{'#':<4} {'Metric':<30} {'Pts':<5} {'Mean':<10} {'Range':<12} {'Uniq':<5} {'Var':<10} {'Pattern':<15} {'Method':<15} {'Ratio':<7} {'Samples'}")
    print(f"{'-'*4} {'-'*30} {'-'*5} {'-'*10} {'-'*12} {'-'*5} {'-'*10} {'-'*15} {'-'*15} {'-'*7} {'-'*40}")
    
    for idx, (series_id, data) in enumerate(series_data.items()):
        timestamps = data["timestamps"]
        values = data["values"]
        
        # Calculate original size
        original_bytes = len(timestamps) * 8 + len(values) * 8
        total_original_bytes += original_bytes
        
        # Get series metadata for better reporting
        metadata = series_metadata.get(series_id, {})
        metric_name = metadata.get("name", "unknown")
        labels_str = ", ".join(f"{k}={v}" for k, v in metadata.get("labels", {}).items())
        
        # Compress timestamps
        compressed_timestamps = compress_timestamps_advanced(timestamps)
        timestamp_method = compressed_timestamps.get("method", "unknown")
        timestamp_method_stats[timestamp_method] += 1
        
        # Compress values (without detailed reporting during compression)
        compressed_values = compress_values_advanced(values, series_id, report_details=False)
        
        compressed_series_data[series_id] = {
            "timestamps": compressed_timestamps,
            "values": compressed_values,
            "original_length": len(timestamps)
        }
        
        # Track method statistics
        value_method = compressed_values.get("method", "unknown")
        pattern = detect_advanced_patterns(values)
        
        # Estimate compressed size for this series
        ts_size = 16  # Base estimate for timestamps
        if timestamp_method == "regular":
            ts_size = 16
        elif timestamp_method == "dual_interval":
            pattern_size = len(compressed_timestamps.get("pattern", []))
            ts_size = 32 + pattern_size
        elif timestamp_method == "delta_rle":
            ts_size = 16 + len(compressed_timestamps.get("deltas", []))
        
        val_size = 0
        if value_method == "xor":
            val_size = compressed_values.get("size", 0)
        elif value_method in ["delta", "delta_rle"]:
            val_size = len(compressed_values.get("data", b""))
        elif value_method == "dictionary":
            val_size = len(compressed_values.get("data", b""))
        elif value_method == "constant":
            val_size = 16
        elif value_method == "sparse_optimized":
            val_size = 16 + len(compressed_values.get("index_deltas", b"")) + len(compressed_values.get("values", [])) * 8
        else:
            # Rough estimate for other methods
            val_size = original_bytes // 4
        
        estimated_compressed = ts_size + val_size
        compression_ratio = original_bytes / max(estimated_compressed, 1)
        
        method_stats[value_method]["count"] += 1
        method_stats[value_method]["original_bytes"] += original_bytes
        method_stats[value_method]["compressed_bytes"] += estimated_compressed
        
        series_stats.append({
            "series_id": series_id,
            "metric_name": metric_name + labels_str and f" ({labels_str})" or "",
            "labels_str": labels_str,
            "points": len(timestamps),
            "original_bytes": original_bytes,
            "compressed_bytes": estimated_compressed,
            "compression_ratio": compression_ratio,
            "timestamp_method": timestamp_method,
            "value_method": value_method
        })
        
        # Calculate statistics
        mean_val = sum(values) / len(values)
        min_val = min(values)
        max_val = max(values)
        value_range = max_val - min_val
        unique_count = len(set(values))
        
        # Calculate variance
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)
        
        # Show sample values in table format
        if len(values) > 3:
            sample_str = f"[{values[0]:.1f}, {values[1]:.1f}, ..., {values[-1]:.1f}]"
        else:
            sample_str = f"{[round(v, 1) for v in values]}"
        
        # Format statistics for display
        if abs(mean_val) < 1000 and abs(mean_val) > 0.01:
            mean_str = f"{mean_val:.2f}"
        elif abs(mean_val) < 0.01:
            mean_str = f"{mean_val:.2e}"
        else:
            mean_str = f"{mean_val:.2e}"
        
        if value_range < 1000 and value_range > 0.01:
            range_str = f"{min_val:.1f}-{max_val:.1f}"
        elif value_range == 0:
            range_str = f"const"
        else:
            range_str = f"{value_range:.2e}"
        
        if variance < 1000 and variance > 0.01:
            var_str = f"{variance:.2f}"
        elif variance < 0.01:
            var_str = f"{variance:.2e}"
        else:
            var_str = f"{variance:.2e}"
        
        # Print table row with statistics
        print(f"{idx+1:<4} {metric_name[:30]:30s} {len(values):<5} {mean_str:<10s} {range_str:<12s} {unique_count:<5} {var_str:<10s} {pattern[:15]:15s} {value_method[:15]:15s} {compression_ratio:<7.2f} {sample_str[:40]}")
    
    # Estimate compressed size
    compressed_msgpack = msgpack.packb({
        "metadata": compressed_metadata,
        "series_data": compressed_series_data
    }, use_bin_type=True)
    
    total_compressed_bytes = len(compressed_msgpack)
    compression_ratio = total_original_bytes / max(total_compressed_bytes, 1)
    
    # Print comprehensive statistics
    print(f"\n{'='*80}")
    print(f"📊 COMPRESSION SUMMARY")
    print(f"{'='*80}")
    
    print(f"\n📈 Overall Statistics:")
    print(f"  Total series: {len(series_data)}")
    print(f"  Total data points: {sum(s['points'] for s in series_stats):,}")
    print(f"  Original size: {total_original_bytes:,} bytes ({total_original_bytes/1024/1024:.2f} MB)")
    print(f"  Compressed size: {total_compressed_bytes:,} bytes ({total_compressed_bytes/1024/1024:.2f} MB)")
    print(f"  Overall compression ratio: {compression_ratio:.2f}x")
    print(f"  Avg bytes per series: {total_compressed_bytes/len(series_data):.1f}")
    print(f"  Avg bytes per data point: {total_compressed_bytes/sum(s['points'] for s in series_stats):.2f}")
    
    print(f"\n🔧 Compression Methods Used (Values):")
    sorted_methods = sorted(method_stats.items(), key=lambda x: x[1]["count"], reverse=True)
    for method, stats in sorted_methods:
        count = stats["count"]
        orig = stats["original_bytes"]
        comp = stats["compressed_bytes"]
        ratio = orig / max(comp, 1)
        pct = (count / len(series_data)) * 100
        print(f"  {method:20s}: {count:4d} series ({pct:5.1f}%) | {ratio:6.2f}x compression | {comp:,} bytes")
    
    print(f"\n⏱️  Timestamp Compression Methods:")
    sorted_ts_methods = sorted(timestamp_method_stats.items(), key=lambda x: x[1], reverse=True)
    for method, count in sorted_ts_methods:
        pct = (count / len(series_data)) * 100
        print(f"  {method:20s}: {count:4d} series ({pct:5.1f}%)")
    
    print(f"\n🏆 Best Compressed Series (by ratio):")
    best_series = sorted(series_stats, key=lambda x: x["compression_ratio"], reverse=True)[:5]
    for i, s in enumerate(best_series, 1):
        print(f"  {i}. {s['metric_name']:30s} | {s['compression_ratio']:6.1f}x | {s['value_method']}")
    
    print(f"\n📉 Worst Compressed Series (by ratio):")
    worst_series = sorted(series_stats, key=lambda x: x["compression_ratio"])[:5]
    for i, s in enumerate(worst_series, 1):
        print(f"  {i}. {s['metric_name']:30s} | {s['compression_ratio']:6.1f}x | {s['value_method']}")
    
    print(f"\n💾 Space Efficiency by Series Size:")
    # Group by size buckets
    size_buckets = {
        "small (<100 pts)": [s for s in series_stats if s["points"] < 100],
        "medium (100-1000 pts)": [s for s in series_stats if 100 <= s["points"] < 1000],
        "large (1000+ pts)": [s for s in series_stats if s["points"] >= 1000]
    }
    for bucket_name, bucket_series in size_buckets.items():
        if bucket_series:
            avg_ratio = sum(s["compression_ratio"] for s in bucket_series) / len(bucket_series)
            avg_bytes_per_pt = sum(s["compressed_bytes"] for s in bucket_series) / sum(s["points"] for s in bucket_series)
            print(f"  {bucket_name:25s}: {len(bucket_series):4d} series | {avg_ratio:.2f}x avg | {avg_bytes_per_pt:.2f} bytes/pt")
    
    return {
        "metadata": compressed_metadata,
        "series_data": compressed_series_data,
        "compression_info": {
            "algorithm": "enhanced_pattern_aware_maximum",
            "original_bytes": total_original_bytes,
            "compressed_bytes": total_compressed_bytes,
            "ratio": compression_ratio,
            "method_stats": dict(method_stats),
            "series_stats": series_stats
        }
    }

# Add decompression functions for verification
def decompress_timestamps_advanced(ts_data: Dict) -> List[int]:
    """Decompress advanced timestamp formats."""
    method = ts_data.get("method", "empty")
    
    if method == "empty":
        return []
    elif method == "single":
        return [ts_data["value"]]
    elif method == "regular":
        start = ts_data["start"]
        interval = ts_data["interval"]
        count = ts_data["count"]
        return [start + i * interval for i in range(count)]
    elif method == "dual_interval":
        start = ts_data["start"]
        intervals = ts_data["intervals"]
        pattern = run_length_decode(ts_data["pattern"])
        
        timestamps = [start]
        current_ts = start
        for bit in pattern:
            current_ts += intervals[bit]
            timestamps.append(current_ts)
        return timestamps
    elif method == "delta_rle":
        start = ts_data["start"]
        deltas = run_length_decode(ts_data["deltas"])
        
        timestamps = [start]
        for delta in deltas:
            timestamps.append(timestamps[-1] + delta)
        return timestamps
    else:
        raise ValueError(f"Unknown timestamp method: {method}")

def decompress_values_advanced(val_data: Dict) -> List[float]:
    """Decompress advanced value formats."""
    method = val_data.get("method", "empty")
    
    if method == "empty":
        return []
    elif method == "single":
        return [val_data["value"]]
    elif method == "constant":
        return [val_data["value"]] * val_data["count"]
    elif method == "near_constant":
        base = val_data["base"]
        precision = val_data["precision"]
        deviations = decompress_integer_list(val_data["deviations"])
        return [base + d * precision for d in deviations]
    elif method == "power_of_2":
        exponents = decompress_integer_list(val_data["exponents"])
        fallback_values = val_data["fallback_values"]
        fallback_iter = iter(fallback_values)
        
        result = []
        for exp in exponents:
            if exp == -1:
                result.append(next(fallback_iter))
            else:
                result.append(2 ** exp)
        return result
    elif method == "mostly_integers":
        integers = decompress_integer_list(val_data["integers"])
        fractional_indices = val_data["fractional_indices"]
        fractional_values = val_data["fractional_values"]
        
        result = [float(i) for i in integers]
        for idx, frac in zip(fractional_indices, fractional_values):
            result[idx] += frac
        return result
    elif method == "sparse_optimized":
        length = val_data["length"]
        first_index = val_data["first_index"]
        index_deltas = decompress_integer_list(val_data["index_deltas"])
        values = val_data["values"]
        
        # Reconstruct indices
        indices = [first_index]
        for delta in index_deltas:
            indices.append(indices[-1] + delta)
        
        # Build result array
        result = [0.0] * length
        for idx, value in zip(indices, values):
            result[idx] = value
        return result
    elif method == "xor":
        expected_count = val_data.get("count", None)
        return xor_decode_floats(val_data["first"], val_data["data"], expected_count)
    elif method == "delta":
        deltas_bytes = val_data["data"]
        num_deltas = len(deltas_bytes) // 8
        deltas = [struct.unpack('>d', deltas_bytes[i*8:(i+1)*8])[0] for i in range(num_deltas)]
        
        values = [val_data["first"]]
        for delta in deltas:
            values.append(values[-1] + delta)
        return values
    elif method == "delta_rle":
        first = val_data["first"]
        rle_pattern = val_data["rle_pattern"]
        non_zero_deltas = val_data["non_zero_deltas"]
        
        # Decode RLE pattern
        pattern = run_length_decode(rle_pattern)
        
        # Reconstruct deltas
        deltas = []
        non_zero_iter = iter(non_zero_deltas)
        for bit in pattern:
            if bit == 0:
                deltas.append(0.0)
            else:
                deltas.append(next(non_zero_iter))
        
        # Reconstruct values
        values = [first]
        for delta in deltas:
            values.append(values[-1] + delta)
        return values
    elif method == "dictionary":
        # Decompress dictionary-encoded data
        data = val_data["data"]
        dictionary = val_data["dictionary"]
        common_values = dictionary["values"]
        
        # Parse compressed data
        if len(data) < 2:
            return []
        
        dict_size = struct.unpack('>H', data[:2])[0]
        dict_end = 2 + dict_size * 8
        
        if len(data) < dict_end:
            return []
        
        # Read dictionary values
        dict_values = []
        for i in range(dict_size):
            offset = 2 + i * 8
            value = struct.unpack('>d', data[offset:offset+8])[0]
            dict_values.append(value)
        
        # Decode data
        result = []
        i = dict_end
        while i < len(data):
            index = data[i]
            i += 1
            
            if index == 255:  # Escape code
                if i + 8 <= len(data):
                    value = struct.unpack('>d', data[i:i+8])[0]
                    result.append(value)
                    i += 8
                else:
                    break
            else:
                if index < len(dict_values):
                    result.append(dict_values[index])
        
        return result
    elif method == "periodic":
        period = val_data["period"]
        base_pattern = val_data["base_pattern"]
        deviations = val_data["deviations"]
        
        # Reconstruct values
        result = base_pattern.copy()
        
        deviation_iter = iter(deviations)
        for i in range(period, period + len(deviations)):
            pattern_index = i % period
            deviation = next(deviation_iter)
            value = base_pattern[pattern_index] + deviation
            result.append(value)
        
        return result
    elif method == "exponential":
        base = val_data["base"]
        avg_ratio = val_data["avg_ratio"]
        ratio_deviations = val_data["ratio_deviations"]
        
        # Reconstruct values
        result = [base]
        current = base
        
        for deviation in ratio_deviations:
            ratio = avg_ratio + deviation
            current *= ratio
            result.append(current)
        
        return result

def verify_enhanced_compression(original_data: Dict[str, Any], compressed_data: Dict[str, Any]) -> None:
    """Verify enhanced compression integrity."""
    print("\nVerifying enhanced compression integrity...")
    
    # Decompress metadata
    compressed_metadata = compressed_data["metadata"]
    dictionaries = compressed_metadata["dictionaries"]
    compressed_series = compressed_metadata["compressed_series"]
    
    # Reconstruct original metadata format
    reconstructed_metadata = {}
    for series_id, comp_series in compressed_series.items():
        metric_name = dictionaries["metric_names"][comp_series["metric_id"]]
        labels = {}
        for key_id, value_id in comp_series["label_pairs"]:
            key = dictionaries["label_keys"][key_id]
            value = dictionaries["label_values"][value_id]
            labels[key] = value
        
        reconstructed_metadata[series_id] = {
            "name": metric_name,  # Use "name" to match columnar format
            "labels": labels
        }
    
    # Verify series data
    compressed_series_data = compressed_data["series_data"]
    original_series_data = original_data["series_data"]
    
    verification_errors = 0
    
    for series_id in reconstructed_metadata.keys():
        if series_id not in compressed_series_data or series_id not in original_series_data:
            print(f"  ⚠️  Series {series_id} missing in compressed or original data")
            verification_errors += 1
            continue
        
        original = original_series_data[series_id]
        compressed = compressed_series_data[series_id]
        
        # Verify timestamps
        try:
            decoded_timestamps = decompress_timestamps_advanced(compressed["timestamps"])
            
            if decoded_timestamps != original["timestamps"]:
                print(f"  ❌ Timestamp mismatch in series {series_id}")
                verification_errors += 1
        except Exception as e:
            print(f"  ❌ Timestamp decompression error in series {series_id}: {e}")
            verification_errors += 1
        
        # Verify values
        try:
            decoded_values = decompress_values_advanced(compressed["values"])
            
            if len(decoded_values) != len(original["values"]):
                print(f"  ❌ Value count mismatch in series {series_id}: {len(decoded_values)} vs {len(original['values'])}")
                verification_errors += 1
            else:
                for i, (decoded, original_val) in enumerate(zip(decoded_values, original["values"])):
                    if abs(decoded - original_val) > 1e-9:
                        print(f"  ❌ Value mismatch in series {series_id} at index {i}: {decoded} vs {original_val}")
                        verification_errors += 1
                        break
        except Exception as e:
            print(f"  ❌ Value decompression error in series {series_id}: {e}")
            verification_errors += 1
    
    if verification_errors == 0:
        print(f"  ✅ All {len(reconstructed_metadata)} series verified successfully")
    else:
        print(f"  ⚠️  {verification_errors} verification errors found")

def main():
    """Main function to execute enhanced Phase 6."""
    print("=" * 60)
    print("Phase 6: Enhanced Compression Tricks + zstd")
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
    
    # Apply enhanced compression tricks
    compressed_data = compress_columnar_data_enhanced(columnar_data)
    
    # Verify compression
    verify_enhanced_compression(columnar_data, compressed_data)
    
    # Serialize compressed data and apply zstd
    print(f"\nApplying zstd compression to enhanced compressed data...")
    msgpack_data = msgpack.packb(compressed_data, use_bin_type=True)
    
    # Apply zstd compression
    compressor = zstd.ZstdCompressor(level=DEFAULT_ZSTD_LEVEL)
    final_compressed_data = compressor.compress(msgpack_data)
    
    # Store final compressed data
    output_file = "output/metrics.enhanced_compressed.zst"
    with open(output_file, "wb") as f:
        f.write(final_compressed_data)
    
    file_size = len(final_compressed_data)
    msgpack_size = len(msgpack_data)
    zstd_compression_ratio = msgpack_size / file_size
    
    # Compare with previous formats
    ndjson_file = "output/metrics.ndjson"
    columnar_file = "output/metrics.columnar.zst"
    original_compressed_file = "output/metrics.compressed.zst"
    
    ndjson_size = os.path.getsize(ndjson_file) if os.path.exists(ndjson_file) else None
    columnar_size = os.path.getsize(columnar_file) if os.path.exists(columnar_file) else None
    original_compressed_size = os.path.getsize(original_compressed_file) if os.path.exists(original_compressed_file) else None
    
    print(f"\n📊 Enhanced Compression Results:")
    print(f"  Output file: {output_file}")
    print(f"  Enhanced compression size: {msgpack_size:,} bytes")
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
    
    if original_compressed_size:
        original_compression = original_compressed_size / file_size
        improvement = (original_compressed_size - file_size) / original_compressed_size * 100
        print(f"  vs Original Compression Tricks: {original_compression:.2f}x compression ({original_compressed_size:,} → {file_size:,} bytes)")
        print(f"  Additional improvement: {improvement:.1f}% smaller")
    
    print(f"\n✅ Enhanced Phase 6 completed successfully!")
    
    return {
        "format": "Enhanced Compressed Columnar",
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
        print(f"\n✅ Enhanced Phase 6 completed in {end_time - start_time:.2f} seconds")
    else:
        print(f"\n❌ Enhanced Phase 6 failed after {end_time - start_time:.2f} seconds")