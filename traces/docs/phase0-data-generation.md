# Phase 0: Trace Data Generation

Generates realistic distributed traces simulating a microservices architecture. Creates traces with parent-child relationships, service topology, realistic latencies, and error scenarios.

## Microservices Topology

**12 services** with dependencies:

```
api-gateway (50ms avg)
  → user-service (80ms)
      → auth-service (30ms) → auth-db (15ms)
      → profile-db (20ms)
  → order-service (120ms)
      → payment-service (200ms)
          → bank-api (800ms, 8% error rate)
          → fraud-detection (150ms)
      → inventory-service (90ms) → inventory-db (30ms)
      → order-db (25ms)
  → inventory-service
      → warehouse-api (100ms)
```

## Realistic Characteristics

**Latency distributions:**
- Database queries: 10-50ms
- Internal services: 50-200ms
- External APIs: 500-1500ms
- Normal distribution with outliers

**Error patterns:**
- bank-api: 8% error rate (external dependency)
- payment-service: 5% error rate
- Most services: 1-3% error rate
- Error propagation up the call chain

**Span relationships:**
- Each request creates 1-8 spans
- Parent-child relationships form tree structure
- Root span (no parent) starts at api-gateway
- Leaf spans at databases/external APIs

## Data Model

Each span contains:
```
{
  trace_id: "550e8400-e29b-41d4-a716-446655440000"
  span_id: "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
  parent_span_id: "6ba7b810-9dad-11d1-80b4-00c04fd430c9" (or null)
  service_name: "api-gateway"
  operation_name: "authenticate"
  start_time: 1698000000000000 (nanoseconds)
  end_time: 1698000000052000
  tags: {
    "http.method": "GET",
    "http.status_code": 200,
    "component": "http"
  }
  logs: [
    {
      "timestamp": 1698000000023000,
      "event": "cache_hit",
      "key": "user:12345"
    }
  ]
  status_code: 0 (OK) or 1 (ERROR)
}
```

## Generated Characteristics

**Small dataset (100 traces):**
- Total spans: ~250-300
- Services: 12 unique
- Operations: ~40-50 unique
- Trace depth: 2-6 levels
- Average spans/trace: 2.5-3

**Medium dataset (1,000 traces):**
- Total spans: ~2,500-3,000
- Higher service/operation reuse
- More realistic patterns emerge

## Compression Potential

**Service names:**
- 12 unique services across ~267 spans
- Reuse: 22x (each service appears ~22 times)
- Potential: Dictionary encoding

**Operation names:**
- ~45 unique operations
- Reuse: 6x
- Potential: Dictionary encoding

**Trace IDs:**
- 100 unique across 267 spans
- 2.67 spans per trace average
- Potential: Group by trace

**Parent-child patterns:**
- Sequential within trace: 0, 1, 2, 3...
- Many -1 (root spans)
- Potential: Delta encoding

**Timestamps:**
- Clustered within traces (100-500ms windows)
- Sequential ordering within traces
- Potential: Delta encoding from root span

## Usage

```bash
python 00_generate_data.py --size small    # 100 traces
python 00_generate_data.py --size medium   # 1,000 traces
python 00_generate_data.py --size big      # 10,000 traces
```

## Output

```
output/traces_small.jsonl              # Raw trace data (134.5 KB)
output/phase0_metadata_small.json      # Statistics
```

This establishes the baseline (134.5 KB) for compression comparisons.
