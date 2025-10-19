# Squeezed Signals: Metrics Storage Engine Evolution

A comprehensive demonstration of how time-series metrics storage formats evolve from simple JSON to highly optimized binary formats. This project shows the journey from 8MB of human-readable JSON down to 0.6MB of compressed columnar data - a **13x compression ratio** - while maintaining full data fidelity.

## 🎯 Overview

This project demonstrates the evolution of metrics storage through 7 distinct phases, each building upon the previous to show different optimization techniques:

1. **NDJSON Baseline** - Human-readable but inefficient
2. **CBOR Encoding** - Better binary serialization  
3. **Binary Table** - String deduplication with fixed-width encoding
4. **Columnar Storage** - Grouping by time series 
5. **Compression Tricks** - Specialized time-series algorithms
6. **Downsampling** - Long-term storage with aggregation
7. **General-Purpose Compression** - zstd as comparison baseline

## 🚀 Quick Start

```bash
# Set up the environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run the complete demonstration
python main.py --size small
```

## 📊 Results Preview

With the small dataset (50,000 points):

| Phase | Format | Size | Compression | Description |
|-------|--------|------|-------------|-------------|
| 1 | NDJSON | 8.05 MB | 1.0x | Human-readable baseline |
| 2 | CBOR | ~6.5 MB | ~1.2x | Better binary serialization |
| 3 | Binary Table | 1.60 MB | 5.0x | String deduplication |
| 4 | Columnar | 0.60 MB | 13.4x | Series grouping |
| 5 | Compression Tricks | 0.66 MB | 12.3x | Temporal algorithms |
| 6 | Downsampling | 2.73 MB | 3.0x | Multi-resolution storage |
| 7 | NDJSON (zstd) | 0.98 MB | 8.2x | General-purpose compression |

## 🛤️ The Evolution Journey

### Phase 1: NDJSON Baseline
```json
{"timestamp": 1760860006, "metric_name": "http_request_duration_seconds", "value": 257.94, "labels": {"host": "server-c", "region": "ap-southeast-1"}}
```
- ✅ Human readable, debuggable
- ❌ Massive key repetition, inefficient numbers

### Phase 2: CBOR Encoding
- ✅ Binary format, preserves structure
- ✅ Better type encoding (integers, floats)
- ❌ Still denormalized with repeated metadata

### Phase 3: Binary Table Format
- ✅ String deduplication (9,000x+ compression on strings!)
- ✅ Fixed-width binary encoding
- ❌ Still row-based structure

### Phase 4: Columnar Storage
```python
{
  "cpu_usage": {
    "metadata": {"labels": {"host": "server-a"}},
    "timestamps": [1760860006, 1760860021, 1760860036],
    "values": [45.2, 47.1, 43.8]
  }
}
```
- ✅ Eliminates metadata repetition completely
- ✅ Enables column-specific optimizations
- ❌ Requires custom parsing

### Phase 5: Compression Tricks
- ✅ Delta-delta encoding for regular timestamps
- ✅ XOR compression for similar values
- ✅ Run-length encoding for repeated data
- ❌ Computational complexity

### Phase 6: Downsampling
- ✅ Essential for long-term retention
- ✅ Multiple aggregation levels (1m, 5m, 15m, 1h)
- ✅ Huge space savings for historical data
- ❌ Lossy compression

### Phase 7: General-Purpose Compression (zstd)
- ✅ Excellent compression with no code changes
- ✅ Industry standard, battle-tested
- ✅ Can compete with specialized techniques
- ❌ Requires decompression for any access

## 🔧 Configuration Options

```bash
# Small dataset: 50,000 points (good for development/testing)
python main.py --size small

# Big dataset: 5,000,000 points (realistic production scale)
python main.py --size big
```

## 📁 Project Structure

```
squeezed-signals/
├── 00_generate_data.py           # Realistic time-series data generation
├── 01_ndjson_storage.py          # Phase 1: NDJSON baseline
├── 02_cbor_storage.py            # Phase 2: CBOR encoding
├── 03_binary_table.py            # Phase 3: Binary table format
├── 04_columnar_storage.py        # Phase 4: Columnar grouping
├── 05_compression_tricks.py      # Phase 5: Specialized algorithms
├── 06_downsampling_storage.py    # Phase 6: Multi-resolution storage
├── 07_general_compression.py     # Phase 7: zstd comparison
├── main.py                       # Orchestration script
├── lib/
│   ├── data_generator.py         # Realistic data patterns
│   └── encoders.py              # Compression algorithms
└── output/                       # Generated files
```

## 🎛️ Data Generation Features

The data generator creates realistic time-series patterns:

- **Random Walk**: Values follow realistic trends with volatility
- **Temporal Correlation**: Values are related to previous values  
- **Seasonal Patterns**: Daily/weekly cycles in the data
- **Integer Metrics**: Connection counts, queue sizes as proper integers
- **Realistic Labels**: Production-like host/region/environment combinations

## 💡 Key Insights

### String Deduplication is Powerful
Binary table format achieves 9,000x+ compression on repeated strings by creating a lookup table.

### Columnar Restructuring > Compression Algorithms
Moving from row-based to columnar format (13.4x) provides bigger gains than specialized compression (12.3x).

### General-Purpose Compression is Competitive  
zstd compression (8.2x) performs surprisingly well compared to specialized techniques with much less complexity.

### Downsampling is Essential at Scale
For long-term retention, downsampling provides the only sustainable approach to storage costs.

## 🌍 Real-World Applications

This evolution mirrors production time-series databases:

- **Prometheus**: Uses columnar storage with compression
- **InfluxDB**: Implements similar timestamp/value compression
- **TimescaleDB**: Combines relational and time-series optimizations
- **Grafana**: Multi-resolution storage for different retention periods

## 🏗️ Production Recommendations

1. **Recent Data (hours-days)**: Use columnar compression for fast queries
2. **Medium-term (days-weeks)**: Implement automatic downsampling
3. **Long-term (months-years)**: Keep only essential aggregates
4. **Monitor compression ratios**: They indicate data pattern health
5. **Tiered storage**: SSD for recent data, HDD for historical

## 🧪 Extending the Project

- Add different compression algorithms (Snappy, LZ4)
- Implement query performance benchmarks
- Add encryption overhead analysis  
- Compare with real database formats
- Add memory usage profiling

## 📚 Learn More

Each phase includes detailed comments explaining:
- Why the technique works
- Trade-offs and limitations
- Real-world applicability
- Performance characteristics

Run individual phases to dive deep into specific techniques:

```bash
python 01_ndjson_storage.py
python 02_cbor_storage.py
# ... etc
```

## 🎉 Results

The complete demonstration shows how thoughtful storage format evolution can achieve **13x compression** while maintaining full data fidelity - essential for cost-effective metrics storage at scale.