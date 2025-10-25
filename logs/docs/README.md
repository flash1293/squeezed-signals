# Log Compression Evolution

Progressive compression techniques demonstrating how understanding data structure enables better compression than generic algorithms alone. Achieves **24-51x compression** on real-world log data depending on dataset characteristics.

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
# Set up the environment (from project root)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Navigate to logs directory
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
python main.py --size small
python main.py --size big    # HDFS logs
python main.py --size huge   # OpenSSH logs
```

**Dataset sizes:** 
- `small` (Apache, ~5 MB, 56k lines)
- `big` (HDFS, ~10 MB, 75k lines)
- `huge` (OpenSSH, ~70 MB, 655k lines)

## Compression Results

**Apache Dataset (56,482 lines, 4.9 MB)**

| Phase | Technique | Size | Ratio | Δ | Bytes/Line |
|-------|-----------|------|-------|---|------------|
| 0 | Raw data | 5,135 KB | 1x | - | 93.1 |
| 1 | Plain text | 5,015 KB | 1x | - | 90.9 |
| 2 | Zstd Level 22 | 173 KB | 28.99x | 29.0x | 3.1 |
| 3 | Template extraction | 138 KB | 36.36x | +1.25x | 2.5 |
| 4 | Variable encoding | 117 KB | 43.31x | +1.19x | 2.1 |
| 5 | Smart ordering | 114 KB | 44.38x | +1.02x | 2.1 |
| 6 | Drop order | 99 KB | 50.75x | +1.14x | 1.8 |

**HDFS Dataset (74,859 lines, 10.0 MB)**

| Phase | Technique | Size | Ratio | Δ | Bytes/Line |
|-------|-----------|------|-------|---|------------|
| 0 | Raw data | 10,486 KB | 1x | - | 143.3 |
| 1 | Plain text | 10,240 KB | 1x | - | 139.8 |
| 2 | Zstd Level 22 | 602 KB | 17.00x | 17.0x | 8.2 |
| 3 | Template extraction | 449 KB | 22.80x | +1.34x | 6.1 |
| 4 | Variable encoding | 454 KB | 22.74x | +1.00x | 6.2 |
| 5 | Smart ordering | 447 KB | 23.06x | +1.01x | 6.1 |
| 6 | Drop order | 423 KB | 24.21x | +1.05x | 5.8 |

**OpenSSH Dataset (655,147 lines, 69.4 MB)**

| Phase | Technique | Size | Ratio | Δ | Bytes/Line |
|-------|-----------|------|-------|---|------------|
| 0 | Raw data | 72,747 KB | 1x | - | 113.8 |
| 1 | Plain text | 71,042 KB | 1x | - | 111.0 |
| 2 | Zstd Level 22 | 2,899 KB | 24.50x | 24.5x | 4.5 |
| 3 | Template extraction | 1,958 KB | 36.28x | +1.48x | 3.1 |
| 4 | Variable encoding | 1,851 KB | 38.73x | +1.07x | 2.9 |
| 5 | Smart ordering | 1,853 KB | 38.69x | +1.00x | 2.9 |
| 6 | Drop order | 1,725 KB | 41.18x | +1.06x | 2.7 |

## Key Insights

**Why this works:**
1. **Log repetition:** 
   - Apache: 38 templates serve 56k lines (1,486x reuse)
   - HDFS: 18 templates serve 75k lines (4,159x reuse)
   - OpenSSH: 5,669 templates serve 655k lines (116x reuse)
2. **Columnar storage:** Enables type-specific compression (timestamps: 6-15x, IPs: 3-12x, IDs: 6-11x)
3. **Data locality:** Grouping similar values improves compression 1-6%
4. **Maximum compression:** Zstd Level 22 provides optimal compression vs Level 6 (1.5-1.7x improvement)
5. **Dataset characteristics matter:**
   - Structured logs (Apache): Best compression (50.8x)
   - Variable structure (HDFS): Moderate compression (24.2x)
   - High entropy (OpenSSH): Good compression (41.2x)

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

Understanding data structure enables significant additional compression beyond generic algorithms:
- **Apache:** 29x from Zstd alone → **50.8x** with log-aware techniques (+75%)
- **HDFS:** 17x from Zstd alone → **24.2x** with log-aware techniques (+42%)
- **OpenSSH:** 24.5x from Zstd alone → **41.2x** with log-aware techniques (+68%)

Each phase targets a different aspect of log structure, with compounding returns. Maximum compression (Zstd Level 22) provides substantial improvements over balanced compression (Level 6).
