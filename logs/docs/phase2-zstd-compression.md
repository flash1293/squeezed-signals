# Phase 2: Zstd Compression

Applies Zstandard (Zstd) compression algorithm to plain text logs. Establishes what generic compression achieves without log-specific optimizations.

## Algorithm

Zstd Level 6 (balanced speed vs. compression):
- Dictionary-based compression
- Recognizes repeated patterns
- Entropy coding
- Fast decompression (~800 MB/s)

## Results

**HDFS small dataset:**
- Input: 554.6 KB (plain text)
- Output: 19.1 KB (compressed)
- Compression: **29.1x**
- Bytes per line: 9.8 (down from 283.9)

## How It Works

**Dictionary building:**
- Zstd scans data for repeated sequences
- Log templates appear frequently → excellent dictionary candidates
- Example: `"INFO dfs.DataNode"` appears 347 times → dictionary entry

**Pattern matching:**
- Subsequent occurrences replaced with short references
- Back-references: "Use bytes 450-497 from earlier in file"
- Much shorter than storing full text again

**Entropy coding:**
- Compresses the reference numbers themselves
- Frequent patterns get shorter codes
- Result: 29.1x compression

## What Compresses Well

**Repeated templates:** ~33x compression
- Static log patterns repeat frequently
- Dictionary captures full templates

**Variable values:** ~24x compression
- Repeated IPs, IDs compress well
- Numbers have patterns

**Whitespace/structure:** ~30x compression
- Consistent formatting compresses easily

## Limitations

- No understanding of log structure
- Variables encoded as text (not optimal)
- Templates not explicitly separated
- Chronological order not optimal for compression

## Usage

```bash
python 02_zstd_compression.py --size small
```

## Output

```
output/phase2_logs_small.zst              # Compressed (19.1 KB)
output/phase2_logs_metadata_small.json    # Statistics
```

29.1x is impressive for a generic algorithm, but understanding log structure can do better.
