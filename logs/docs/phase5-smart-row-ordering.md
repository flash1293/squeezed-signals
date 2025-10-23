# Phase 5: Smart Row Ordering

Reorders logs by template and variable similarity for better compression. Groups similar data together to improve Zstd's dictionary effectiveness.

## The Reordering Strategy

**1. Group by template:**
```
Before: [T0, T5, T0, T12, T0, T5, ...]
After:  [T0, T0, T0, ..., T5, T5, ..., T12, T12, ...]
```

**2. Sub-cluster by variables:**
Within each template group, sort by variable similarity:
```
Template T0 logs, sorted by IP then timestamp:
  [IP=10.251.43.191, TS=081109 203615]
  [IP=10.251.43.191, TS=081109 203617]
  [IP=10.251.43.191, TS=081109 203620]
  [IP=172.16.5.10, TS=081109 203615]
  [IP=172.16.5.10, TS=081109 203618]
```

**3. Store order mapping:**
```
order_mapping: [0, 347, 1, 512, 2, 348, ...]  # New index → original index
Encoding: Delta + varint + Zstd
Size: 2,300 bytes (17% of total)
```

## Results

**HDFS small dataset:**
- Input: 13.9 KB (Phase 4)
- Output: 13.1 KB (reordered + mapping)
- Compression: **42.2x** (vs 1x baseline, +1.06x vs Phase 4)
- Bytes per line: 6.7 (down from 7.1)

## Compression Gains

**Template IDs:**
```
Before: [0, 5, 0, 12, 0, 5, ...]  → 950 bytes compressed
After:  [0, 0, 0, ..., 5, 5, ..., 12, 12, ...]  → 450 bytes compressed
Gain: 2.1x
```

**Variable columns:**
```
IPs before: [10.251.43.191, 172.16.5.10, 10.251.43.191, ...]
IPs after:  [10.251.43.191, 10.251.43.191, ..., 172.16.5.10, ...]
Zstd compression: 1.19x better on IP column
```

Similar 5-15% gains across all variable columns.

## Order Mapping Overhead

The mapping allows reconstructing original chronological order:
```
order_mapping: [original indices for each new position]
Size: 2,300 bytes (17.1% of Phase 5 total)

Encoding:
  Raw: 2,000 × 4 bytes = 8,000 bytes
  Delta-encoded: ~2,800 bytes (mixed large/small deltas)
  After Zstd: ~2,300 bytes
```

## Why This Works

**Data locality:** Similar values adjacent compress better
- Zstd's dictionary finds longer repeating patterns
- Back-references are shorter
- Entropy coding benefits from predictable sequences

**Template runs:** Long sequences of same template ID
- Highly compressible
- RLE-like behavior in Zstd

## Trade-offs

**Advantages:**
- 6% additional compression
- Can reconstruct original order
- All data preserved

**Costs:**
- Order mapping overhead (17%)
- More complex implementation
- Slower reconstruction

## Usage

```bash
python 05_smart_row_ordering.py --size small
```
