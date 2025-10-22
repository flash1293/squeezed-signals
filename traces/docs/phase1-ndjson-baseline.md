# Phase 1: NDJSON Baseline

Stores traces in NDJSON (newline-delimited JSON) format with one span per line. Human-readable baseline with full field names and text encoding.

## Format

Each line is a complete span in JSON:

```json
{"trace_id": "550e8400-...", "span_id": "6ba7b810-...", "parent_span_id": "...", "operation_name": "authenticate", "service_name": "api-gateway", "start_time": 1698000000000000, "end_time": 1698000000052000, "duration_ns": 52000000, "tags": {"http.method": "GET"}, "logs": [], "status_code": 0, "status": "OK"}
{"trace_id": "550e8400-...", "span_id": "7ca8c920-...", "parent_span_id": "6ba7b810-...", ...}
```

## Results

**Small dataset (100 traces, 267 spans):**
- File size: 134,276 bytes (134.3 KB)
- Bytes per span: 503 bytes
- Compression: **1.00x** (baseline)

## Characteristics

**Advantages:**
- Human-readable (can use `cat`, `grep`, `jq`)
- Standard format (NDJSON widely supported)
- One span per line (easy streaming)
- No parsing complexity

**Inefficiencies:**
- Full UUIDs: 36 bytes each (trace_id, span_id, parent_span_id)
- Text encoding: Numbers as decimal strings
- Field names repeated on every line
- Whitespace and quotes overhead
- Duplicate status information (`status_code` and `status`)

## Redundancy Example

Service name "api-gateway" (11 bytes):
- Appears 30 times in dataset
- Total: 330 bytes as text
- Could be: 11 bytes (value) + 30 × 1 byte (ID) = 41 bytes
- Waste: 289 bytes from one service name

## Usage

```bash
python 01_ndjson_storage.py --size small
```

## Output

```
output/traces_small_ndjson.jsonl         # NDJSON (134.3 KB)
output/phase1_ndjson_metadata_small.json # Statistics
```

This establishes the 1x baseline for measuring compression improvements.
