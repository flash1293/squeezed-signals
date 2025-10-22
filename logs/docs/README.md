# Log Compression Evolution

Progressive compression techniques demonstrating how understanding data structure enables better compression than generic algorithms alone. Achieves **42x-51x compression** on real-world log data.

## Documentation

- **[Phase 0: Log Data Generation](phase0-data-generation.md)** - Real-world datasets from LogHub
- **[Phase 1: Plain Text Baseline](phase1-plain-text-baseline.md)** - Uncompressed baseline (1x)
- **[Phase 2: Zstd Compression](phase2-zstd-compression.md)** - Generic algorithm (29x)
- **[Phase 3: Template Extraction](phase3-template-extraction.md)** - CLP algorithm - structure separation (36x)
- **[Phase 4: Advanced Variable Encoding](phase4-advanced-variable-encoding.md)** - Type-specific encoding (40x)
- **[Phase 5: Smart Row Ordering](phase5-smart-row-ordering.md)** - Data locality grouping (42x)
- **[Phase 6: Drop Order Preservation](phase6-drop-order-preservation.md)** - Remove ordering overhead (51x)

## Running the Pipeline

```bash
cd logs

# Run individual phases
python 00_generate_data.py --size small
python 01_plain_text_baseline.py --size small
python 02_zstd_compression.py --size small
python 03_template_extraction.py --size small
python 04_advanced_variable_encoding.py --size small
python 05_smart_row_ordering.py --size small
python 06_drop_order_preservation.py --size small

# Or run all at once
python main.py --size small --phase 0 1 2 3 4 5 6
```

**Dataset sizes:** `small` (Apache, ~0.5 MB), `big` (HDFS, ~1 MB), `huge` (OpenSSH, ~1 MB)

## Compression Results

**HDFS Dataset (2,000 lines, 554.6 KB)**

| Phase | Technique | Size | Ratio | Δ | Bytes/Line |
|-------|-----------|------|-------|---|------------|
| 0 | Raw data | 554.6 KB | 1x | - | 283.9 |
| 1 | Plain text | 554.6 KB | 1x | - | 283.9 |
| 2 | Zstd Level 6 | 19.1 KB | 29.1x | 29.1x | 9.8 |
| 3 | Template extraction | 15.3 KB | 36.2x | +1.24x | 7.8 |
| 4 | Variable encoding | 13.9 KB | 39.9x | +1.10x | 7.1 |
| 5 | Smart ordering | 13.1 KB | 42.2x | +1.06x | 6.7 |
| 6 | Drop order | 10.9 KB | 50.9x | +1.21x | 5.6 |

## Technique Overview

### Phase 2: Zstd Compression (29x)

Generic compression algorithm (Zstandard Level 6). Dictionary-based compression recognizes repeated log templates. Fast decompression (~800 MB/s). Establishes baseline for log-aware techniques.

### Phase 3: Template Extraction (36x)

**Core CLP algorithm.** Separates logs into static templates and dynamic variables.

Example:
```
Before: "081109 203615 143 INFO dfs.DataNode: Receiving block blk_-160899"
After:  Template: "<TIMESTAMP> <NUM> INFO dfs.DataNode: Receiving block <ID>"
        Variables: TIMESTAMP="081109 203615", NUM=143, ID="blk_-160899"
```

**Result:** 47 templates serve 2,000 lines (42.6x reuse). Columnar variable storage enables type-specific compression.

### Phase 4: Advanced Variable Encoding (40x)

Type-specific encoding for variable columns:
- **Timestamps:** Delta encoding (base + deltas: [0, 0, 2, 1, ...])
- **IPs:** Binary (4 bytes vs 13 bytes text)
- **Identifiers:** Dictionary (store once, use indices)
- **Numbers:** Varint encoding

Gains 10% over Phase 3.

### Phase 5: Smart Row Ordering (42x)

Reorders logs by template and variable similarity for better compression:
- Groups same templates together: `[T0, T0, T0, ..., T5, T5, ...]`
- Clusters similar variable values within template groups
- Stores order mapping (delta + varint + zstd): 2,300 bytes (17% overhead)

Gains 6% over Phase 4.

### Phase 6: Drop Order Preservation (51x)

Removes order mapping entirely. Trade-off: 21% space savings vs. no exact chronological reconstruction. Timestamps still available for approximate ordering.

Removes 2,300 bytes (17% of Phase 5 size).

## Performance

**Compression speed (2K lines):**
- Phase 2 (Zstd): 0.08s (~200 MB/s)
- Phase 3 (Template): 0.15s (3.7 MB/s)
- Phase 4 (Encoding): 0.23s (2.4 MB/s)
- Phase 5 (Ordering): 0.31s (1.8 MB/s)
- Phase 6 (Drop order): 0.08s (6.9 MB/s)

**Decompression speed:** Phase 2 fastest (~800 MB/s), others range 5-14 MB/s

**Scalability:**

| Log Size | Phase 2 | Phase 3 | Phase 4 | Phase 5 | Phase 6 |
|----------|---------|---------|---------|---------|---------|
| 1 MB | 35 KB | 27 KB | 24 KB | 23 KB | 19 KB |
| 1 GB | 34 MB | 27 MB | 24 MB | 23 MB | 19 MB |
| 10 GB | 340 MB | 270 MB | 240 MB | 230 MB | 191 MB |

## Choosing a Phase

| Phase | Compression | Complexity | Speed | Use Case |
|-------|-------------|------------|-------|----------|
| 1 | 1x | Low | Fast | Development/debugging |
| 2 | 29x | Low | Fast | Quick compression, widely supported |
| 3 | 36x | Medium | Medium | Good balance |
| 4 | 40x | High | Slower | Cost-sensitive |
| 5 | 42x | High | Slowest | Need order preservation |
| 6 | 51x | High | Fast* | Maximum compression, no order needed |

*Fast decompression (no order reconstruction)

## Data Flow

```
Phase 0: Generate data → logs_small.log (554.6 KB)
         ↓
Phase 1: Plain text → phase1_logs_small.log (554.6 KB, 1x)
         ↓
Phase 2: Zstd → phase2_logs_small.zst (19.1 KB, 29x)
         ↓
Phase 3: Template extraction → phase3_logs_small.pkl (15.3 KB, 36x)
         ↓
Phase 4: Variable encoding → phase4_logs_small.pkl (13.9 KB, 40x)
         ↓
Phase 5: Smart ordering + order map → phase5_logs_small.pkl (13.1 KB, 42x)
         ↓
Phase 6: Remove order map → phase6_logs_small.pkl (10.9 KB, 51x)
```

## Storage Format

**Phase 1-2:** Plain text or compressed plain text

**Phase 3:** Templates + columnar variables
```
templates: ["<TIMESTAMP> <NUM> INFO ...", ...]
line_to_template: [0, 0, 1, 0, 2, ...]
variable_columns: {TIMESTAMP: [...], NUM: [...], ...}
```

**Phase 4:** Type-specific encoding
```
encoded_variable_columns: {
  TIMESTAMP: <delta_base + deltas>,
  IP: <binary_4bytes>,
  IDENTIFIER: <dict + indices>,
  NUM: <varint>
}
```

**Phase 5:** + Reordering + order mapping
```
Reordered data + order_mapping: [original_indices]
```

**Phase 6:** - order mapping
```
Same as Phase 5 without order_mapping
```

## Key Insights

**Why this works:**
1. **Log repetition:** 47 templates serve 2,000 lines (42.6x reuse)
2. **Columnar storage:** Enables type-specific compression (timestamps: 15x, IPs: 12x, IDs: 11x)
3. **Data locality:** Grouping similar values improves compression 10-20%
4. **Diminishing returns:** Phase 2 (29x) → Phase 3 (+24%) → Phase 4 (+10%) → Phase 5 (+6%) → Phase 6 (+21%)

**Real-world systems** (e.g., YScope CLP) achieve 50-200x on production logs due to:
- More templates = higher reuse
- Longer time series = better delta encoding
- More homogeneous data = better clustering

## References

- **YScope CLP**: https://github.com/y-scope/clp (production log compression, 100x+)
- **Zstandard**: https://facebook.github.io/zstd/
- **LogHub**: https://github.com/logpai/loghub (real-world log datasets)
- Paper: "Compressed Log Processor (CLP): Making Log Compression Practical" (2021)

## Summary

Understanding data structure enables 45-75% additional compression beyond generic algorithms:
- **29x** from algorithm alone (Zstd)
- **42x** with log-aware techniques (templates + encoding + ordering)
- **51x** with maximum optimization (drop order mapping)

Each phase targets a different aspect of log structure, with diminishing but compounding returns.
