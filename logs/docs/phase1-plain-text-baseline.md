# Phase 1: Plain Text Baseline

Stores logs as plain text with line indexing. Establishes the uncompressed baseline (1x) for comparison.

## Format

Each log line stored as-is, with metadata tracking line positions:

```
081109 203615 143 INFO dfs.DataNode: Receiving block blk_-160899...
081109 203615 145 INFO dfs.DataNode: PacketResponder 0 for block...
```

Metadata:
```json
{
  "line_index": [0, 156, 312, ...],
  "total_lines": 2000,
  "total_bytes": 567890
}
```

## Results

**HDFS small dataset:**
- Total lines: 2,000
- File size: 567,890 bytes (554.6 KB)
- Bytes per line: 283.9
- Compression: **1.00x** (baseline)

## Characteristics

**Advantages:**
- Human-readable
- Standard tools work (grep, less, tail)
- No parsing overhead
- Simple implementation

**Disadvantages:**
- No compression (100% size)
- Repeated templates stored verbatim
- Text encoding overhead (IP addresses: 15 bytes vs 4 bytes binary)
- No deduplication

## Redundancy Example

Template `"INFO dfs.DataNode: Receiving block"` (47 bytes):
- Appears 347 times
- Total: 16,309 bytes
- Could be: Template ID (2 bytes) × 347 = 694 bytes
- Waste: 15,615 bytes from one template alone

## Usage

```bash
python 01_plain_text_baseline.py --size small
```

## Output

```
output/phase1_logs_small.log             # Plain text (554.6 KB)
output/phase1_logs_metadata_small.json   # Metadata
```

This establishes the 1x baseline that subsequent phases improve upon.



- Trivial to implement in any language

**Universal Compatibility**
- Works with all text processing tools
- Compatible across all operating systems
- No versioning or format compatibility issues
- Easy integration with existing log pipelines

**Debugging Friendly**
- Logs are immediately readable
- No decompression step needed for investigation
- Easy to grep, tail, head, or sed
- Perfect for development and troubleshooting

**Sequential Append**
- Can write new lines without rewriting file
- No index updates required during write
- Log rotation is trivial (just rename/move file)
- Works perfectly with streaming log collectors

**No Corruption Risk**
- Partial writes still readable
- No header/footer dependencies
- File truncation only loses recent entries
- Easy recovery from incomplete writes

### ❌ Disadvantages (Cons)

**Massive Storage Waste**
- Every character stored as 1+ bytes
- Zero deduplication of repeated content
