# Phase 5: Columnar Storage

Column-oriented storage with column-specific compression algorithms. Optimized for analytical queries rather than trace reconstruction.

## Approach

Separate span attributes into columns and apply targeted compression per column type.

## Column-Specific Strategies

### Duration Column

**Pattern:** Wide range but predictable distribution
```
Durations: [53ms, 86ms, 30ms, 16ms, 52ms, 120ms, ...]
Unique values: 147 out of 267 spans
```

**Strategy:** Delta encoding from median
```
Median: 80ms
Deltas: [-27ms, +6ms, -50ms, -64ms, -28ms, +40ms, ...]
Smaller numbers → better varint compression

Result: 1,342 bytes → 675 bytes (2x)
```

### Status Code Column

**Pattern:** Mostly 0 (OK), few 1 (ERROR)
```
Status codes: [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, ...]
Unique values: 2 (binary)
```

**Strategy:** Run-length encoding
```
Runs: 8×0, 1×1, 10×0, ...
Or bitmap: 00000001 00000000 ...

Result: 270 bytes → 56 bytes (4.8x)
```

### Parent Relationship Column

**Pattern:** Sequential with many roots
```
Parent indices: [-1, 0, 1, 2, -1, 0, 1, 2, -1, 0, ...]
Unique values: 6 patterns
```

**Strategy:** Dictionary encoding
```
Dictionary: [-1, 0, 1, 2, 3, 4]
Indices: [0, 1, 2, 3, 0, 1, ...] (6 values = 3 bits each)

Result: 270 bytes → 94 bytes (2.9x)
```

### Service Name Column

**Pattern:** 12 unique services with high reuse
```
Services: ["api-gateway" (30×), "user-service" (25×), ...]
```

**Strategy:** Dictionary + RLE
```
Dictionary: 12 services
ID sequence: [0, 0, 0, ..., 1, 1, ..., 2, 2, 2, ...]
Runs: 30×0, 25×1, 20×2, ...

Result: ~74x compression (best column)
```

## Results

**Small dataset:**
- Input: 6.4 KB (Phase 4 relationships)
- Output: 5.4 KB (Columnar)
- Compression: **24.98x** (vs 1x baseline, +1.19x vs Phase 4)
- Bytes per span: 20 bytes (down from 24)

**Medium dataset:**
- Compression: **17.82x** (Phase 4 is 22x)
- Trade-off: Worse compression but better query performance

## Storage Structure

```
{
  topology: {...} (same as Phase 4)
  
  columns: {
    durations: <compressed_675_bytes>
    status_codes: <compressed_56_bytes>
    parent_relationships: <compressed_94_bytes>
    service_ids: <compressed>
    operation_ids: <compressed>
    start_deltas: <compressed>
  }
  
  span_positions: [4, 4, 4, 1, 1, ...] (spans per trace)
  
  mappings: {
    tag_keys: {...}
    tag_values: {...}
  }
}
```

## Query Performance

**Column queries (fast):**
```
// Get all durations
decompress(columns.durations)  # Only read one column

// Count errors
decompress(columns.status_codes).count(1)

// Average latency
mean(decompress(columns.durations))
```

**Trace reconstruction (slower):**
```
// Need to read multiple columns
services = decompress(columns.service_ids)
durations = decompress(columns.durations)
...
reconstruct_spans(services, durations, ...)
```

## Trade-offs vs Phase 4

**Phase 4 (Relationships):**
- ✅ Better compression (21-22x)
- ✅ Faster trace reconstruction
- ✅ Maintains trace structure
- ❌ Must read full traces for queries

**Phase 5 (Columnar):**
- ✅ Fast column queries
- ✅ Good compression (18-25x)
- ✅ Analytics-friendly
- ❌ Slower trace reconstruction
- ❌ More complex implementation

## Use Cases

**Choose Phase 4 for:**
- Trace storage/archival
- Trace reconstruction/visualization
- Request debugging
- Sequential access patterns

**Choose Phase 5 for:**
- Performance analytics
- Error rate analysis
- Latency percentiles
- Service health monitoring
- Business intelligence queries

## Column Compression Summary

```
Column              Original  Compressed  Ratio   Strategy
─────────────────────────────────────────────────────────
Durations           1,342 B   675 B       2.0x    Delta
Status codes        270 B     56 B        4.8x    RLE
Parent indices      270 B     94 B        2.9x    Dictionary
Service IDs         ~3,000 B  ~41 B       73x     Dict+RLE
Operation IDs       ~2,000 B  ~90 B       22x     Dict+RLE
Start deltas        ~2,100 B  ~800 B      2.6x    Varint
─────────────────────────────────────────────────────────
```

## Usage

```bash
python 05_columnar_storage.py --size small
```

## Output

```
output/traces_small_columnar.msgpack.zst  # 5.4 KB
output/phase5_columnar_metadata_small.json
```

Columnar storage achieves 25x compression while enabling fast analytical queries over individual span attributes.
