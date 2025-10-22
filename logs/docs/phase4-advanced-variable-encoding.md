# Phase 4: Advanced Variable Encoding

Type-specific binary encoding for variable columns. Each variable type uses its optimal encoding scheme.

## Encoding Strategies

**Timestamps:** Delta encoding
```
Values: [1231538175, 1231538175, 1231538177, 1231538178]
Encoded: base=1231538175, deltas=[0, 0, 2, 1]
Gain: 4.3x on timestamp column
```

**IP Addresses:** Binary (4 bytes instead of text)
```
Text: "10.251.43.191" (13 bytes)
Binary: 0x0AFB2BBF (4 bytes)
Gain: 3.25x
```

**Identifiers:** Dictionary encoding
```
Values: ["blk_-160899...", "blk_-160899...", "blk_-160900...", ...]
Encoded: dictionary + indices
  Dict: ["blk_-160899...", "blk_-160900...", ...]
  Indices: [0, 0, 1, ...]
Gain: 2.2x on identifier column
```

**Numbers:** Varint encoding
```
Small numbers use fewer bytes:
  0-127: 1 byte
  128-16383: 2 bytes
  etc.
```

## Results

**HDFS small dataset:**
- Input: 15.3 KB (Phase 3)
- Output: 13.9 KB (encoded)
- Compression: **39.9x** (vs 1x baseline, +1.10x vs Phase 3)
- Bytes per line: 7.1 (down from 7.8)

## Gains by Column

```
Column       Before    After     Improvement
───────────────────────────────────────────
TIMESTAMP    1,840 B   430 B     4.3x
IDENTIFIER   4,100 B   1,850 B   2.2x
IP           670 B     595 B     1.13x
NUM          800 B     720 B     1.11x
───────────────────────────────────────────
Overall: 10% additional compression
```

## Why This Works

Type-specific encoding exploits patterns in each data type:
- Timestamps are usually sequential (deltas are small)
- IPs have structure (subnets cluster together)
- Identifiers repeat frequently (dictionary works well)
- Numbers are often small (varint saves space)

## Data Structure

Same as Phase 3, but `variable_columns` becomes `encoded_variable_columns`:

```json
{
  "templates": [...],
  "line_to_template": [...],
  "encoded_variable_columns": {
    "TIMESTAMP": {
      "encoding": "delta_varint",
      "base_timestamp": 1231538175,
      "deltas": <binary_data>
    },
    "IP": {
      "encoding": "binary_ipv4",
      "values": <4_byte_ints>
    },
    "IDENTIFIER": {
      "encoding": "dictionary",
      "dictionary": ["blk_-160899...", ...],
      "indices": <binary_indices>
    }
  }
}
```

## Usage

```bash
python 04_advanced_variable_encoding.py --size small
```

## Output

```
output/phase4_logs_small.pkl             # Encoded data (13.9 KB)
output/phase4_logs_metadata_small.json   # Statistics
```

10% improvement may seem small, but compounds with previous gains for 40x total compression.
