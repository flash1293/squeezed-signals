# Phase 3: Template Extraction

The core CLP (Compressed Log Processor) algorithm. Separates log lines into static templates and dynamic variables, storing templates once and variables in columnar format.

## The CLP Algorithm

**Key idea:** Most log lines share common structure with variable parts.

Example:
```
Before: "081109 203615 143 INFO dfs.DataNode: Receiving block blk_-160899"
After:
  Template: "<TIMESTAMP> <NUM> INFO dfs.DataNode: Receiving block <ID>"
  Variables: TIMESTAMP="081109 203615", NUM=143, ID="blk_-160899"
```

## Results

**HDFS small dataset:**
- Input: 19.1 KB (Zstd compressed text)
- Output: 15.3 KB (template + variables)
- Compression: **36.2x** (vs 1x baseline, +1.24x vs Phase 2)
- Bytes per line: 7.8 (down from 9.8)

## How It Works

**1. Template extraction:**
- Scan logs to identify static vs variable parts
- Variable types: timestamps, IPs, numbers, identifiers, paths
- Result: 47 unique templates for 2,000 lines (42.6x reuse)

**2. Columnar storage:**
```
line_to_template: [0, 0, 1, 0, 2, 0, 0, 3, ...]  # Template ID per line
variable_columns: {
  'TIMESTAMP': ['081109 203615', '081109 203615', ...],
  'NUM': [143, 145, 147, ...],
  'IP': ['10.251.43.191', '10.251.43.191', ...],
  'IDENTIFIER': ['blk_-160899...', 'blk_-160900...', ...]
}
```

**3. Compression:**
- Template IDs: 2,000 indices → compressed to ~950 bytes
- Variable columns: Grouped by type → better Zstd compression
- Overall: 36.2x from baseline

## Why This Works

**Template reuse:**
```
Template: "INFO dfs.DataNode: Receiving block"
Occurrences: 347 times
Storage:
  - Plain text: 347 × 47 bytes = 16,309 bytes
  - Phase 3: 47 bytes (template) + 347 × 2 bytes (IDs) = 741 bytes
  Savings: 22x just from this template
```

**Columnar compression:**
```
Timestamps column (all similar):
  ['081109 203615', '081109 203615', '081109 203617', ...]
  Zstd compresses repeated values much better when grouped
  
IPs column (locality):
  ['10.251.43.191', '10.251.43.191', ..., '172.16.5.10', ...]
  Similar values adjacent → better compression
```

## Data Structure

```json
{
  "templates": [
    "<TIMESTAMP> <NUM> INFO dfs.DataNode: Receiving block <ID>",
    "<TIMESTAMP> <NUM> INFO dfs.DataNode: PacketResponder <NUM> for block <ID>",
    ...
  ],
  "line_to_template": [0, 0, 1, 0, 2, ...],
  "variable_columns": {
    "TIMESTAMP": ["081109 203615", ...],
    "NUM": [143, 145, ...],
    "IP": ["10.251.43.191", ...],
    "IDENTIFIER": ["blk_-160899...", ...]
  },
  "line_variable_counts": [3, 3, 4, ...],
  "template_variable_patterns": {
    "0": ["TIMESTAMP", "NUM", "IDENTIFIER"],
    "1": ["TIMESTAMP", "NUM", "NUM", "IDENTIFIER"]
  }
}
```

(All pickled + Zstd compressed)

## Usage

```bash
python 03_template_extraction.py --size small
```

## Output

```
output/phase3_logs_small.pkl             # Template data (15.3 KB)
output/phase3_logs_metadata_small.json   # Statistics
```

This is the breakthrough technique - understanding log structure enables much better compression than generic algorithms.
