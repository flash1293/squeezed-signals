#!/usr/bin/env python3
"""
Phase 0: Generate Realistic Distributed Trace Data

Creates realistic distributed traces with multiple services, operations, and error scenarios.
Simulates microservices topology with realistic latency distributions and error propagation.
"""

import json
import random
import time
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import os
from pathlib import Path

# Import our trace encoders
import sys
sys.path.append(str(Path(__file__).parent))
from lib.encoders import Span, Trace

class MicroserviceTopology:
    """Simulates a realistic microservices architecture"""
    
    def __init__(self):
        # Define realistic microservices
        self.services = {
            'api-gateway': {
                'operations': ['authenticate', 'route_request', 'rate_limit'],
                'error_rate': 0.02,
                'avg_latency_ms': 50,
                'downstream': ['user-service', 'order-service', 'inventory-service']
            },
            'user-service': {
                'operations': ['get_profile', 'update_profile', 'authenticate_user'],
                'error_rate': 0.01,
                'avg_latency_ms': 80,
                'downstream': ['auth-service', 'profile-db']
            },
            'order-service': {
                'operations': ['create_order', 'get_order', 'update_order', 'cancel_order'],
                'error_rate': 0.03,
                'avg_latency_ms': 120,
                'downstream': ['payment-service', 'inventory-service', 'order-db']
            },
            'payment-service': {
                'operations': ['process_payment', 'validate_card', 'charge_card'],
                'error_rate': 0.05,
                'avg_latency_ms': 200,
                'downstream': ['bank-api', 'fraud-detection']
            },
            'inventory-service': {
                'operations': ['check_availability', 'reserve_items', 'update_stock'],
                'error_rate': 0.02,
                'avg_latency_ms': 90,
                'downstream': ['inventory-db', 'warehouse-api']
            },
            'auth-service': {
                'operations': ['verify_token', 'refresh_token', 'revoke_token'],
                'error_rate': 0.01,
                'avg_latency_ms': 30,
                'downstream': ['redis-cache', 'auth-db']
            },
            'profile-db': {
                'operations': ['select', 'insert', 'update', 'delete'],
                'error_rate': 0.005,
                'avg_latency_ms': 20,
                'downstream': []
            },
            'order-db': {
                'operations': ['select', 'insert', 'update', 'delete'],
                'error_rate': 0.005,
                'avg_latency_ms': 25,
                'downstream': []
            },
            'inventory-db': {
                'operations': ['select', 'insert', 'update', 'delete'],
                'error_rate': 0.01,
                'avg_latency_ms': 30,
                'downstream': []
            },
            'auth-db': {
                'operations': ['select', 'insert', 'update'],
                'error_rate': 0.005,
                'avg_latency_ms': 15,
                'downstream': []
            },
            'redis-cache': {
                'operations': ['get', 'set', 'delete', 'expire'],
                'error_rate': 0.002,
                'avg_latency_ms': 5,
                'downstream': []
            },
            'bank-api': {
                'operations': ['charge', 'verify', 'refund'],
                'error_rate': 0.08,
                'avg_latency_ms': 800,
                'downstream': []
            },
            'fraud-detection': {
                'operations': ['analyze_transaction', 'check_patterns'],
                'error_rate': 0.03,
                'avg_latency_ms': 150,
                'downstream': ['ml-model-service']
            },
            'ml-model-service': {
                'operations': ['predict', 'validate_input'],
                'error_rate': 0.02,
                'avg_latency_ms': 300,
                'downstream': []
            },
            'warehouse-api': {
                'operations': ['check_stock', 'reserve', 'ship'],
                'error_rate': 0.04,
                'avg_latency_ms': 250,
                'downstream': []
            }
        }
        
        # Common request patterns
        self.request_patterns = [
            'user_authentication',
            'order_creation', 
            'order_lookup',
            'profile_update',
            'inventory_check',
            'payment_processing'
        ]

class TraceGenerator:
    """Generates realistic distributed traces"""
    
    def __init__(self):
        self.topology = MicroserviceTopology()
        self.trace_counter = 0
        
    def generate_trace_id(self) -> str:
        """Generate a unique trace ID"""
        self.trace_counter += 1
        return f"trace-{self.trace_counter:08d}-{uuid.uuid4().hex[:8]}"
    
    def generate_span_id(self) -> str:
        """Generate a unique span ID"""
        return uuid.uuid4().hex[:16]
    
    def generate_realistic_latency(self, service_name: str) -> int:
        """Generate realistic latency with some variance"""
        base_latency = self.topology.services[service_name]['avg_latency_ms']
        # Add variance (±50% with exponential distribution for outliers)
        variance = random.expovariate(2.0) * base_latency * 0.5
        if random.random() < 0.05:  # 5% chance of high latency outlier
            variance += base_latency * random.uniform(2, 10)
        return int(base_latency + variance)
    
    def should_have_error(self, service_name: str) -> bool:
        """Determine if this span should have an error"""
        error_rate = self.topology.services[service_name]['error_rate']
        return random.random() < error_rate
    
    def generate_tags(self, service_name: str, operation: str, has_error: bool) -> Dict[str, Any]:
        """Generate realistic span tags"""
        tags = {
            'service.name': service_name,
            'operation': operation,
            'component': 'http' if 'api' in service_name else 'database' if 'db' in service_name else 'service',
            'http.method': random.choice(['GET', 'POST', 'PUT', 'DELETE']) if 'api' in service_name or 'service' in service_name else None,
            'http.status_code': random.choice([500, 502, 503, 504]) if has_error else random.choice([200, 201, 202]),
            'user.id': f"user-{random.randint(1000, 9999)}",
            'request.id': f"req-{uuid.uuid4().hex[:8]}",
        }
        
        # Remove None values
        return {k: v for k, v in tags.items() if v is not None}
    
    def generate_span(self, trace_id: str, service_name: str, operation: str, 
                     parent_span_id: Optional[str], start_time: int) -> Span:
        """Generate a single span"""
        span_id = self.generate_span_id()
        latency_ms = self.generate_realistic_latency(service_name)
        end_time = start_time + (latency_ms * 1_000_000)  # Convert to nanoseconds
        
        has_error = self.should_have_error(service_name)
        status_code = 1 if has_error else 0  # 0=OK, 1=ERROR
        
        tags = self.generate_tags(service_name, operation, has_error)
        
        # Generate some log events
        logs = []
        if has_error:
            logs.append({
                'timestamp': start_time + (latency_ms * 500_000),  # Mid-span
                'level': 'ERROR',
                'message': f'Error in {operation}: timeout' if 'timeout' in operation else f'Error in {operation}: validation failed',
                'error.kind': 'timeout' if random.random() < 0.3 else 'validation'
            })
        
        return Span(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            operation_name=operation,
            service_name=service_name,
            start_time=start_time,
            end_time=end_time,
            tags=tags,
            logs=logs,
            status_code=status_code
        )
    
    def generate_request_pattern_trace(self, pattern: str) -> Trace:
        """Generate a trace following a specific request pattern"""
        trace_id = self.generate_trace_id()
        base_time = int(time.time() * 1_000_000_000)  # Current time in nanoseconds
        spans = []
        
        if pattern == 'user_authentication':
            # API Gateway -> User Service -> Auth Service -> Auth DB
            current_time = base_time
            
            # API Gateway span
            gateway_span = self.generate_span(trace_id, 'api-gateway', 'authenticate', None, current_time)
            spans.append(gateway_span)
            current_time += 10_000_000  # 10ms offset
            
            # User Service span
            user_span = self.generate_span(trace_id, 'user-service', 'authenticate_user', gateway_span.span_id, current_time)
            spans.append(user_span)
            current_time += 20_000_000  # 20ms offset
            
            # Auth Service span
            auth_span = self.generate_span(trace_id, 'auth-service', 'verify_token', user_span.span_id, current_time)
            spans.append(auth_span)
            current_time += 5_000_000   # 5ms offset
            
            # Auth DB span
            db_span = self.generate_span(trace_id, 'auth-db', 'select', auth_span.span_id, current_time)
            spans.append(db_span)
            
        elif pattern == 'order_creation':
            # Complex order creation with fan-out pattern
            current_time = base_time
            
            # API Gateway
            gateway_span = self.generate_span(trace_id, 'api-gateway', 'route_request', None, current_time)
            spans.append(gateway_span)
            current_time += 15_000_000
            
            # Order Service
            order_span = self.generate_span(trace_id, 'order-service', 'create_order', gateway_span.span_id, current_time)
            spans.append(order_span)
            
            # Fan-out: Parallel calls to payment and inventory
            fan_out_time = current_time + 30_000_000
            
            # Payment processing
            payment_span = self.generate_span(trace_id, 'payment-service', 'process_payment', order_span.span_id, fan_out_time)
            spans.append(payment_span)
            
            # Bank API call from payment service
            bank_span = self.generate_span(trace_id, 'bank-api', 'charge', payment_span.span_id, fan_out_time + 50_000_000)
            spans.append(bank_span)
            
            # Fraud detection (parallel to bank)
            fraud_span = self.generate_span(trace_id, 'fraud-detection', 'analyze_transaction', payment_span.span_id, fan_out_time + 20_000_000)
            spans.append(fraud_span)
            
            # ML model for fraud detection
            ml_span = self.generate_span(trace_id, 'ml-model-service', 'predict', fraud_span.span_id, fan_out_time + 80_000_000)
            spans.append(ml_span)
            
            # Inventory check (parallel to payment)
            inventory_span = self.generate_span(trace_id, 'inventory-service', 'check_availability', order_span.span_id, fan_out_time)
            spans.append(inventory_span)
            
            # Inventory DB
            inv_db_span = self.generate_span(trace_id, 'inventory-db', 'select', inventory_span.span_id, fan_out_time + 30_000_000)
            spans.append(inv_db_span)
            
            # Order DB (after everything completes)
            order_db_span = self.generate_span(trace_id, 'order-db', 'insert', order_span.span_id, fan_out_time + 200_000_000)
            spans.append(order_db_span)
            
        # Add similar patterns for other request types...
        else:
            # Simple fallback pattern
            gateway_span = self.generate_span(trace_id, 'api-gateway', 'route_request', None, base_time)
            spans.append(gateway_span)
        
        return Trace(trace_id=trace_id, spans=spans)
    
    def generate_dataset(self, num_traces: int) -> List[Trace]:
        """Generate a complete dataset of traces"""
        traces = []
        
        print(f"Generating {num_traces} realistic distributed traces...")
        
        for i in range(num_traces):
            if i % 100 == 0:
                print(f"Generated {i}/{num_traces} traces...")
            
            # Choose a random pattern
            pattern = random.choice(self.topology.request_patterns)
            trace = self.generate_request_pattern_trace(pattern)
            traces.append(trace)
        
        print(f"Generated {len(traces)} traces with {sum(len(t.spans) for t in traces)} total spans")
        return traces

def save_traces_as_json(traces: List[Trace], output_file: str):
    """Save traces in OpenTelemetry JSON format"""
    print(f"Saving traces to {output_file}...")
    
    with open(output_file, 'w') as f:
        for trace in traces:
            trace_data = {
                'trace_id': trace.trace_id,
                'spans': []
            }
            
            for span in trace.spans:
                span_data = {
                    'trace_id': span.trace_id,
                    'span_id': span.span_id,
                    'parent_span_id': span.parent_span_id,
                    'operation_name': span.operation_name,
                    'service_name': span.service_name,
                    'start_time': span.start_time,
                    'end_time': span.end_time,
                    'duration': span.duration,
                    'tags': span.tags,
                    'logs': span.logs,
                    'status_code': span.status_code
                }
                trace_data['spans'].append(span_data)
            
            f.write(json.dumps(trace_data) + '\n')
    
    file_size = os.path.getsize(output_file)
    print(f"Saved {len(traces)} traces ({file_size:,} bytes) to {output_file}")

def main():
    """Generate realistic trace dataset"""
    # Create output directory
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Generate dataset based on size argument
    import sys
    size = sys.argv[1] if len(sys.argv) > 1 else 'small'
    
    trace_counts = {
        'small': 100,
        'medium': 1000, 
        'big': 10000
    }
    
    num_traces = trace_counts.get(size, 100)
    
    # Generate traces
    generator = TraceGenerator()
    traces = generator.generate_dataset(num_traces)
    
    # Save in multiple formats for testing
    save_traces_as_json(traces, f'output/traces_{size}.json')
    
    # Calculate and display statistics
    total_spans = sum(len(trace.spans) for trace in traces)
    avg_spans_per_trace = total_spans / len(traces) if traces else 0
    
    print(f"\nDataset Statistics:")
    print(f"Total traces: {len(traces):,}")
    print(f"Total spans: {total_spans:,}")
    print(f"Average spans per trace: {avg_spans_per_trace:.1f}")
    
    # Service distribution
    service_counts = {}
    for trace in traces:
        for span in trace.spans:
            service_counts[span.service_name] = service_counts.get(span.service_name, 0) + 1
    
    print(f"\nTop services by span count:")
    for service, count in sorted(service_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {service}: {count:,} spans")

if __name__ == '__main__':
    main()