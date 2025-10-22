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

## Technique Overview

### Phase 2: CBOR Binary Encoding (1.8x)

Replace JSON text with binary encoding:
- Compact field names: `trace_id` → `t`
- Binary integers instead of text
- No whitespace overhead

### Phase 3: CBOR + Zstd (11.9x)

Add dictionary compression:
- Service/operation names compress well (repeated)
- Zstd learns patterns from data
- 6.6x additional compression

### Phase 4: Span Relationships (21x)

**Core breakthrough:** Exploit trace structure.

**Service topology mapping:**
```
Services appear ~20-30 times → Store once, use IDs
Before: "api-gateway" × 30 = 390 bytes
After: "api-gateway" + 30 IDs (1 byte each) = 43 bytes
Gain: 9x
```

**Parent-child delta encoding:**
```
Span IDs within trace: 0, 1, 2, 3, ...
Parent IDs: -1, 0, 1, 2, ... (small integers)
Use 1-2 bytes instead of 36-byte UUIDs
```

**Timestamp deltas:**
```
Absolute: [1698000000000000, 1698000000052000, ...]
Deltas: [0, 52000, 34000, ...] (much smaller numbers)
Varint encoding: 52000 = 3 bytes instead of 8
```

**Result:** 1.77x improvement over Phase 3 (21x total)

### Phase 5: Columnar Storage (25x)

Store columns separately with column-specific compression:

**Duration column:**
- All durations together: [53ms, 86ms, 30ms, ...]
- Delta encoding: base + deltas
- 1342 bytes → 675 bytes (2x)

**Status code column:**
- Mostly 0s (OK), few 1s (ERROR)
- Run-length encoding works well
- 270 bytes → 56 bytes (4.8x)

**Parent relationships:**
- Patterns: [-1, 0, 1, 2, -1, 0, ...]
- Dictionary compression
- 270 bytes → 94 bytes (2.9x)

**Result:** 1.19x improvement (25x total), better for queries

## Trade-offs

**Phase 4 (Relationships):**
- ✅ Best compression (21-22x)
- ✅ Fast reconstruction
- ✅ Preserves trace structure
- ❌ Sequential access

**Phase 5 (Columnar):**
- ✅ Good compression (18-25x)
- ✅ Column queries (e.g., "all durations")
- ✅ Analytics-friendly
- ❌ Slightly larger than Phase 4

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
