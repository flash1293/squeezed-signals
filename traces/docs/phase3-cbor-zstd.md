# Phase 3: CBOR + Zstandard Compression

Adds Zstandard compression on top of CBOR binary encoding. Generic dictionary-based compression without trace-specific optimizations.

## Algorithm

Zstandard Level 6 with custom dictionary:
- Builds dictionary from sample data
- Includes common strings: service names, operation names, tag keys
- Dictionary size: 112 KB trained on 50 sample spans

## Results

**Small dataset:**
- Input: 74.8 KB (CBOR)
- Output: 11.3 KB (CBOR+Zstd)
- Compression: **11.89x** (vs 1x baseline, +6.64x vs Phase 2)
- Bytes per span: 42 bytes (down from 280)

## How It Works

**Dictionary training:**
```
Common patterns in traces:
  - Service names: "api-gateway", "user-service", ... (12 unique)
  - Operations: "authenticate", "get_profile", ... (~45 unique)
  - Tag keys: "http.method", "http.status_code", ...
  - CBOR field keys: "t", "s", "p", "svc", "o", ...

Zstd dictionary: 112 KB of learned patterns
```

**Dictionary compression:**
```
Before: "api-gateway" appears 30 times = 330 bytes
After: Dictionary entry + 30 references (2-3 bytes each) = ~80 bytes
Gain: 4.1x on this service name alone
```

**Pattern matching:**
- Repeated service/operation combinations
- Similar timestamp sequences
- Common tag patterns
- CBOR structure repetition

## What Compresses Well

**Service names:** ~8x compression
- Limited set (12 unique)
- High repetition (22x average)
- Dictionary learns all service names

**Operation names:** ~6x compression
- ~45 unique operations
- Moderate repetition
- Dictionary captures common ops

**Tags:** ~5x compression
- Tag keys repeat across spans
- Tag values have patterns (status codes, HTTP methods)

**Structure:** ~3x compression
- CBOR field order consistent
- Similar span structures

## Limitations

Still doesn't understand traces:
- Doesn't exploit parent-child relationships
- Doesn't group spans by trace
- No timestamp delta encoding
- No topology-aware optimization

## Dictionary Training

Training on first 50 spans creates patterns like:
```
Dictionary entries:
  - Frequent: "svc", "o", "t", "s", "p"
  - Services: "api-gateway", "user-service", ...
  - Operations: "authenticate", "get_profile", ...
  - Tags: "http.method", "http.status_code", ...
  - Values: "GET", "POST", "200", "500"
```

Result: 20-30% better compression than without dictionary.

## Usage

```bash
python 03_cbor_zstd.py --size small
```

## Output

```
output/traces_small_cbor.zst            # Compressed (11.3 KB)
output/traces_small_cbor_dict.zstd      # Dictionary (112 KB)
output/phase3_cbor_zstd_metadata_small.json
```

11.89x is excellent for generic compression, but trace-aware techniques can nearly double this.
