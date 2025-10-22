# Phase 2: CBOR Binary Encoding

Replaces JSON text encoding with CBOR (Concise Binary Object Representation) binary format. Compact field names and binary integers instead of text.

## Changes from Phase 1

**Field name optimization:**
```
trace_id → t (1 byte instead of 8)
span_id → s
parent_span_id → p
operation_name → o
service_name → svc
start_time → st
end_time → et
duration_ns → d
status_code → sc
```

**Binary encoding:**
- Integers as binary (not decimal text)
- Timestamp: 8 bytes binary vs 16 bytes text
- Boolean values: 1 byte vs 4-5 bytes text
- Reduced overhead: No quotes, minimal whitespace

## Results

**Small dataset:**
- Input: 134.3 KB (NDJSON)
- Output: 74.8 KB (CBOR)
- Compression: **1.79x**
- Bytes per span: 280 bytes (down from 503)

## How It Works

**Example transformation:**
```json
// Before (JSON): 150 bytes
{"trace_id": "550e8400-e29b-41d4-a716-446655440000", "span_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8", "service_name": "api-gateway", "start_time": 1698000000000000}

// After (CBOR pseudo-representation): ~85 bytes
{t: "550e...", s: "6ba...", svc: "api-gateway", st: 0x1698000000000000}
```

**Savings breakdown:**
- Field names: 50 bytes → 10 bytes (5x)
- Timestamps: 16 bytes → 8 bytes (2x)
- Overall structure: ~40% reduction

## Why This Works

**Field name compression:**
- JSON repeats full field names on every span
- CBOR uses short keys: 267 spans × 7 bytes saved per field = 1,869 bytes per field
- 10 fields = 18,690 bytes saved just from shorter keys

**Binary integers:**
- Timestamp `1698000000000000` as text: 16 bytes
- As binary int64: 8 bytes
- 267 spans × 2 timestamps × 8 bytes saved = 4,272 bytes

**No encoding overhead:**
- JSON: Quotes, colons, commas, whitespace
- CBOR: Type bytes only
- ~10% overhead reduction

## Limitations

Still has inefficiencies:
- Full UUIDs stored (could use integers)
- Service/operation names repeated (no dictionary)
- No compression algorithm
- No understanding of relationships

## Usage

```bash
python 02_cbor_storage.py --size small
```

## Output

```
output/traces_small_cbor.cbor           # CBOR binary (74.8 KB)
output/phase2_cbor_metadata_small.json  # Statistics
```

1.79x is good for just changing encoding, but understanding structure can do much better.
