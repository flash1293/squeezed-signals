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
