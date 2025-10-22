# Phase 4: Span Relationship Compression

The breakthrough phase. Exploits trace structure, parent-child relationships, and service topology for maximum compression.

## Core Techniques

### 1. Service Topology Mapping

**Problem:** Service names repeated across spans
```
"api-gateway" appears 30 times = 330 bytes
"user-service" appears 25 times = 300 bytes
...
```

**Solution:** Store each service name once, use IDs
```
Service dictionary:
  0: "api-gateway"
  1: "user-service"
  2: "order-service"
  ...

Spans reference ID: svc=0, svc=1, svc=0, ... (1 byte each)

Savings:
  Before: 330 bytes (30 × 11)
  After: 11 bytes (name) + 30 bytes (IDs) = 41 bytes
  Gain: 8x for one service
```

Same for operation names (~45 unique operations).

### 2. Parent-Child Delta Encoding

**Problem:** Full UUIDs for span relationships
```
span_id: "6ba7b810-9dad-11d1-80b4-00c04fd430c8" (36 bytes)
parent_span_id: "550e8400-e29b-41d4-a716-446655440000" (36 bytes)
```

**Solution:** Use sequential integers within each trace
```
Trace A spans: 0, 1, 2, 3, 4
Parent IDs: -1, 0, 1, 2, 1 (root has -1, others reference parent)

span 0: parent=-1 (root)
span 1: parent=0
span 2: parent=1
span 3: parent=2
span 4: parent=1 (sibling of span 2)

Savings:
  Before: 36 bytes per span × 267 spans = 9,612 bytes
  After: 1-2 bytes per span × 267 spans = ~534 bytes
  Gain: 18x
```

### 3. Timestamp Delta Encoding

**Problem:** Absolute nanosecond timestamps are large
```
start_time: 1698000000000000 (16 decimal digits)
```

**Solution:** Store delta from root span
```
Root span: start=1698000000000000 (reference time)
Child span: start=1698000000052000
  → Delta: 52000 (5 digits, much smaller)

Varint encoding: 52000 = 3 bytes instead of 8

Typical deltas: 10,000-500,000 (10μs-500ms)
  → 2-4 bytes with varint instead of 8 bytes
  → 2-4x compression
```

### 4. Trace Grouping

**Problem:** Spans scattered across file
```
trace1-span1, trace2-span1, trace1-span2, trace3-span1, trace1-span3
```

**Solution:** Group all spans by trace_id
```
trace1: [span1, span2, span3]
trace2: [span1, span2]
trace3: [span1, span2, span3, span4]

Benefits:
  - Parent IDs are local (0, 1, 2 instead of UUIDs)
  - Timestamps are close (good deltas)
  - Service patterns more predictable
  - Better Zstd compression
```

## Results

**Small dataset:**
- Input: 11.3 KB (CBOR+Zstd)
- Output: 6.4 KB (Relationships)
- Compression: **21.03x** (vs 1x baseline, +1.77x vs Phase 3)
- Bytes per span: 24 bytes (down from 42)

**Medium dataset:**
- Compression: **22.21x** (better with more data)

## Data Structure

```
{
  topology: {
    services: {"api-gateway": 0, "user-service": 1, ...}
    operations: {"authenticate": 0, "get_profile": 1, ...}
  }
  traces: [
    {
      tid: "trace-uuid" (only once per trace)
      root_start: 1698000000000000 (reference timestamp)
      spans: [
        {
          si: 0 (span index, not UUID)
          pi: -1 (parent index: -1 = root)
          svc: 0 (service ID)
          op: 0 (operation ID)
          std: 0 (start delta from root)
          dur: 52000000 (duration in ns)
          sc: 0 (status code)
          tags: {...}
          logs: [...]
        },
        {
          si: 1
          pi: 0 (parent is span 0)
          svc: 1
          op: 5
          std: 52000 (52μs after root)
          dur: 30000000
          sc: 0
          tags: {...}
        }
      ]
    }
  ]
}
```

(Serialized with MessagePack + Zstd Level 22)

## Why This Works

**Service IDs:**
- 12 services across 267 spans
- Text: 12 × avg(11 bytes) + 267 × avg(11 bytes) = 3,069 bytes
- IDs: 12 × avg(11 bytes) + 267 × 1 byte = 399 bytes
- **Gain: 7.7x**

**Parent indices:**
- UUIDs: 267 × 36 bytes = 9,612 bytes
- Indices: 267 × 1 byte = 267 bytes (varint)
- **Gain: 36x**

**Timestamp deltas:**
- Absolute: 267 × 8 bytes = 2,136 bytes
- Deltas: 267 × 3 bytes avg = 801 bytes (varint)
- **Gain: 2.7x**

**Combined with Zstd:**
- Topology creates patterns
- Sequential IDs compress well
- Delta values predictable
- Additional 2-3x from Zstd

## Limitations

- Must reconstruct full trace to read single span
- Sequential access only
- More complex than columnar for analytics

## Usage

```bash
python 04_span_relationships.py --size small
```

## Output

```
output/traces_small_relationships.msgpack.zst  # 6.4 KB
output/phase4_relationships_metadata_small.json
```

21x compression achieved by understanding trace structure. This is the optimal format for storage and reconstruction.
