"""
Trace-specific encoding and compression utilities for distributed tracing data.
"""

import sys
import struct
import zstandard as zstd
import msgpack
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import time

# Add project root to path for config import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import DEFAULT_ZSTD_LEVEL

@dataclass
class Span:
    """OpenTelemetry-compatible span representation"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    service_name: str
    start_time: int  # nanoseconds
    end_time: int    # nanoseconds
    tags: Dict[str, Any]
    logs: List[Dict[str, Any]]
    status_code: int  # 0=OK, 1=ERROR, 2=TIMEOUT
    
    @property
    def duration(self) -> int:
        return self.end_time - self.start_time

@dataclass
class Trace:
    """Complete trace with all spans"""
    trace_id: str
    spans: List[Span]
    root_span: Optional[Span] = None
    
    def __post_init__(self):
        # Find root span (no parent)
        for span in self.spans:
            if span.parent_span_id is None:
                self.root_span = span
                break

class ServiceTopologyEncoder:
    """Compresses service-to-service call patterns"""
    
    def __init__(self):
        self.service_map: Dict[str, int] = {}
        self.operation_map: Dict[str, int] = {}
        self.call_patterns: Dict[Tuple[int, int], int] = {}  # (service_a, service_b) -> count
    
    def add_service(self, service_name: str) -> int:
        """Add service and return its ID"""
        if service_name not in self.service_map:
            self.service_map[service_name] = len(self.service_map)
        return self.service_map[service_name]
    
    def add_operation(self, operation_name: str) -> int:
        """Add operation and return its ID"""
        if operation_name not in self.operation_map:
            self.operation_map[operation_name] = len(self.operation_map)
        return self.operation_map[operation_name]
    
    def record_call_pattern(self, parent_service: str, child_service: str):
        """Record a service-to-service call"""
        parent_id = self.add_service(parent_service)
        child_id = self.add_service(child_service)
        pattern = (parent_id, child_id)
        self.call_patterns[pattern] = self.call_patterns.get(pattern, 0) + 1

class SpanRelationshipEncoder:
    """Compresses span parent-child relationships"""
    
    def __init__(self):
        self.span_id_map: Dict[str, int] = {}
        self.parent_deltas: List[int] = []
    
    def encode_span_relationships(self, trace: Trace) -> bytes:
        """Encode span relationships with delta compression"""
        # Sort spans by start time for better delta compression
        sorted_spans = sorted(trace.spans, key=lambda s: s.start_time)
        
        # Build span ID mapping
        for i, span in enumerate(sorted_spans):
            self.span_id_map[span.span_id] = i
        
        # Encode parent relationships as deltas
        relationships = []
        for span in sorted_spans:
            if span.parent_span_id is None:
                relationships.append(-1)  # Root span marker
            else:
                parent_idx = self.span_id_map.get(span.parent_span_id, -1)
                current_idx = self.span_id_map[span.span_id]
                delta = current_idx - parent_idx
                relationships.append(delta)
        
        return msgpack.packb(relationships)

class TracePatternDetector:
    """Detects common distributed system patterns"""
    
    def __init__(self):
        self.service_call_templates: Dict[str, int] = {}
        self.error_patterns: Dict[str, int] = {}
        self.latency_patterns: Dict[str, List[int]] = defaultdict(list)
    
    def analyze_trace(self, trace: Trace) -> Dict[str, Any]:
        """Analyze trace for compression patterns"""
        patterns = {
            'service_chain': self._detect_service_chain(trace),
            'fan_out_pattern': self._detect_fan_out(trace),
            'error_propagation': self._detect_error_propagation(trace),
            'critical_path': self._find_critical_path(trace),
            'repeated_operations': self._find_repeated_operations(trace)
        }
        return patterns
    
    def _detect_service_chain(self, trace: Trace) -> List[str]:
        """Detect linear service call chains (A→B→C→D)"""
        if not trace.root_span:
            return []
        
        chain = [trace.root_span.service_name]
        current_span = trace.root_span
        
        while True:
            # Find child spans
            children = [s for s in trace.spans if s.parent_span_id == current_span.span_id]
            if len(children) == 1:  # Linear chain continues
                child = children[0]
                if child.service_name != current_span.service_name:
                    chain.append(child.service_name)
                current_span = child
            else:
                break  # Chain ends (fan-out or leaf)
        
        return chain
    
    def _detect_fan_out(self, trace: Trace) -> Dict[str, int]:
        """Detect fan-out patterns (one service calls many)"""
        fan_out = defaultdict(int)
        
        for span in trace.spans:
            children = [s for s in trace.spans if s.parent_span_id == span.span_id]
            if len(children) > 1:
                # Count unique services called
                unique_services = set(child.service_name for child in children)
                if len(unique_services) > 1:
                    fan_out[span.service_name] = len(unique_services)
        
        return dict(fan_out)
    
    def _detect_error_propagation(self, trace: Trace) -> List[str]:
        """Detect error propagation through services"""
        error_chain = []
        error_spans = [s for s in trace.spans if s.status_code != 0]
        
        if error_spans:
            # Sort by start time to see propagation order
            error_spans.sort(key=lambda s: s.start_time)
            error_chain = [s.service_name for s in error_spans]
        
        return error_chain
    
    def _find_critical_path(self, trace: Trace) -> List[str]:
        """Find the critical path through the trace"""
        if not trace.root_span:
            return []
        
        # Build dependency graph
        span_dict = {s.span_id: s for s in trace.spans}
        
        def get_max_path(span: Span) -> Tuple[int, List[str]]:
            children = [s for s in trace.spans if s.parent_span_id == span.span_id]
            if not children:
                return span.duration, [span.service_name]
            
            max_child_duration = 0
            max_child_path = []
            
            for child in children:
                child_duration, child_path = get_max_path(child)
                if child_duration > max_child_duration:
                    max_child_duration = child_duration
                    max_child_path = child_path
            
            return span.duration + max_child_duration, [span.service_name] + max_child_path
        
        _, critical_path = get_max_path(trace.root_span)
        return critical_path
    
    def _find_repeated_operations(self, trace: Trace) -> Dict[str, int]:
        """Find repeated operation patterns"""
        operations = defaultdict(int)
        
        for span in trace.spans:
            key = f"{span.service_name}:{span.operation_name}"
            operations[key] += 1
        
        # Return only operations that appear multiple times
        return {k: v for k, v in operations.items() if v > 1}

class ColumnarTraceEncoder:
    """Column-oriented trace storage"""
    
    def __init__(self):
        self.compressor = zstd.ZstdCompressor(level=DEFAULT_ZSTD_LEVEL)
    
    def encode_columnar(self, traces: List[Trace]) -> Dict[str, bytes]:
        """Encode traces in columnar format"""
        columns = {
            'trace_ids': [],
            'span_ids': [],
            'parent_span_ids': [],
            'service_names': [],
            'operation_names': [],
            'start_times': [],
            'end_times': [],
            'durations': [],
            'status_codes': [],
            'tags': [],
        }
        
        # Extract all spans into columns
        for trace in traces:
            for span in trace.spans:
                columns['trace_ids'].append(span.trace_id)
                columns['span_ids'].append(span.span_id)
                columns['parent_span_ids'].append(span.parent_span_id or '')
                columns['service_names'].append(span.service_name)
                columns['operation_names'].append(span.operation_name)
                columns['start_times'].append(span.start_time)
                columns['end_times'].append(span.end_time)
                columns['durations'].append(span.duration)
                columns['status_codes'].append(span.status_code)
                columns['tags'].append(span.tags)
        
        # Compress each column separately
        compressed_columns = {}
        for col_name, col_data in columns.items():
            if col_name in ['start_times', 'end_times', 'durations']:
                # Delta encode timestamps and durations
                if col_data:
                    deltas = [col_data[0]]  # First value as-is
                    for i in range(1, len(col_data)):
                        deltas.append(col_data[i] - col_data[i-1])
                    packed_data = msgpack.packb(deltas)
                else:
                    packed_data = msgpack.packb([])
            else:
                packed_data = msgpack.packb(col_data)
            
            compressed_columns[col_name] = self.compressor.compress(packed_data)
        
        return compressed_columns

def calculate_compression_ratio(original_size: int, compressed_size: int) -> float:
    """Calculate compression ratio"""
    if compressed_size == 0:
        return float('inf')
    return original_size / compressed_size

def format_size(size_bytes: int) -> str:
    """Format size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"