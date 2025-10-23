# Phase 2: Zstd Compression

Applies Zstandard (Zstd) compression algorithm to plain text logs. Establishes what generic compression achieves without log-specific optimizations.

## Algorithm

Zstd Level 22 (maximum compression):
- Dictionary-based compression
- Recognizes repeated patterns
- Entropy coding
- Fast decompression (~800 MB/s)

## Results

**Apache dataset (56,482 lines):**
- Input: 5.0 MB (plain text)
- Output: 173 KB (compressed)
- Compression: **29.0x**
- Bytes per line: 3.1 (down from 90.9)

**HDFS dataset (74,859 lines):**
- Input: 10.0 MB (plain text)
- Output: 602 KB (compressed)
- Compression: **17.0x**
- Bytes per line: 8.2 (down from 139.8)

**OpenSSH dataset (655,147 lines):**
- Input: 69.4 MB (plain text)
- Output: 2.9 MB (compressed)
- Compression: **24.5x**
- Bytes per line: 4.5 (down from 111.0)

**Level 22 vs Level 6:**
- Maximum compression provides 1.5-1.7x improvement over balanced compression
- Slower compression speed (~10x) but same decompression speed
- Worth it for archival/storage optimization

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

**Repeated templates:** 
- Apache: 38 templates for 56k lines → excellent compression
- HDFS: 18 templates for 75k lines → best reuse ratio
- OpenSSH: 5,669 templates for 655k lines → moderate entropy

**Variable values:**
- Repeated IPs, IDs compress well
- Numbers have patterns
- Depends on cardinality

**Whitespace/structure:**
- Consistent formatting compresses easily
- Log format matters significantly

## Limitations

- No understanding of log structure
- Variables encoded as text (not optimal)
- Templates not explicitly separated
- Chronological order not optimal for compression

## Usage

```bash
python 02_zstd_compression.py --size small
```
