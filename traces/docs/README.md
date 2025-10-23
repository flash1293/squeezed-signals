# Distributed Trace Compression

Progressive compression techniques for distributed tracing data. Achieves **21-25x compression** by understanding trace structure, service topology, and span relationships.

## Documentation

- **[Phase 0: Data Generation](phase0-data-generation.md)** - Realistic microservices traces
- **[Phase 1: NDJSON Baseline](phase1-ndjson-baseline.md)** - Human-readable baseline (1x)
- **[Phase 2: CBOR Encoding](phase2-cbor-encoding.md)** - Binary serialization (1.8x)
- **[Phase 3: CBOR + Zstd](phase3-cbor-zstd.md)** - Generic compression (11.9x)
- **[Phase 4: Span Relationships](phase4-span-relationships.md)** - Topology compression (21x)
- **[Phase 5: Columnar Storage](phase5-columnar-storage.md)** - Column-oriented analytics (25x)

## Running the Pipeline

```bash
cd traces

# Run all phases
python main.py --size small

# Run specific phase
python main.py --phase 04 --size medium

# Available sizes
python main.py --size small   # 100 traces
python main.py --size medium  # 1,000 traces  
python main.py --size big     # 10,000 traces
```

## Compression Results

**Small dataset (100 traces, 267 spans):**

| Phase | Format | Size | Ratio | Δ |
|-------|---------|------|-------|---|
| 0 | Raw JSON | 134.5 KB | 1.00x | - |
| 1 | NDJSON | 134.3 KB | 1.00x | - |
| 2 | CBOR | 74.8 KB | 1.79x | +1.79x |
| 3 | CBOR+Zstd | 11.3 KB | 11.89x | +6.64x |
| 4 | Relationships | 6.4 KB | 21.03x | +1.77x |
| 5 | Columnar | 5.4 KB | 24.98x | +1.19x |

**Medium dataset (1,000 traces, 2,811 spans):**
- Phase 4: **22.21x** compression
- Phase 5: **17.82x** compression (better for analytics)

## Trace Data Model

Microservices architecture simulation:

```
api-gateway → user-service → auth-service → auth-db
            → order-service → payment-service → bank-api
                           → fraud-detection
                           → inventory-service → inventory-db
                           → order-db
```

Each span:
```
{
  trace_id: UUID (groups related spans)
  span_id: UUID (unique span identifier)
  parent_span_id: UUID (parent in call tree)
  service_name: string (e.g., "api-gateway")
  operation_name: string (e.g., "authenticate")
  start_time: nanoseconds
  end_time: nanoseconds
  tags: key-value metadata
  logs: structured log events
  status_code: 0 (OK) or 1 (ERROR)
}
```

## Key Insights

**Why this works:**

1. **Service name reuse:** 12 services across 267 spans = 22x reuse
2. **Parent-child locality:** Sequential IDs within traces
3. **Timestamp clustering:** Related spans close in time
4. **Tag repetition:** Same tags across many spans

**Compression evolution:**
- JSON (1x) → CBOR (1.8x): Binary encoding
- CBOR (1.8x) → +Zstd (11.9x): Dictionary compression
- Zstd (11.9x) → +Topology (21x): Structure awareness
- Topology (21x) → +Columnar (25x): Column-specific algorithms

Each phase builds on previous techniques while adding domain-specific optimizations.

## References

- **OpenTelemetry**: https://opentelemetry.io/ (trace data standard)
- **CBOR**: https://cbor.io/ (binary JSON)
- **Zstandard**: https://facebook.github.io/zstd/
- **Jaeger/Zipkin**: Distributed tracing systems

Understanding trace structure (parent-child, topology, timing) enables 12-18x additional compression beyond generic algorithms.
