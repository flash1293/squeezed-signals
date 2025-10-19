# Squeezed Signals: Metrics Storage Engine Evolution

A comprehensive demonstration of how time-series metrics storage formats evolve from simple JSON to highly optimized binary formats. This project shows the journey from 8MB of human-readable JSON down to **0.13MB** of compressed columnar data - a **53x compression ratio** - while maintaining full data fidelity.

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

# Run with enhanced data generation for better compression
USE_ENHANCED_GENERATOR=true REGULARITY_LEVEL=high python main.py --size small
```

## 📊 Results Preview

### Standard Dataset (47,000 points)
| Phase | Format | Size | Compression | Key Innovation |
|-------|--------|------|-------------|----------------|
| 1 | NDJSON | 7.32 MB | 1.0x | Human readable baseline |
| 4 | Columnar | 0.57 MB | 12.85x | Series grouping |
| 5 | Compression Tricks | 0.51 MB | 14.42x | Temporal algorithms |
| 7 | NDJSON (zstd) | 0.89 MB | 8.19x | General-purpose compression |

### Enhanced Dataset (High Regularity, 47,000 points)  
| Phase | Format | Size | Compression | Key Innovation |
|-------|--------|------|-------------|----------------|
| 1 | NDJSON | 6.96 MB | 1.0x | Human readable baseline |
| 4 | Columnar | 0.50 MB | 13.89x | Series grouping |
| 5 | **Compression Tricks** | **0.13 MB** | **53.27x** | **Optimized temporal algorithms** |
| 7 | NDJSON (zstd) | 0.39 MB | 17.99x | General-purpose compression |

**🎯 Key Achievement: 524x compression** for long-term storage (3600s downsampling)

## 🔬 Enhanced Data Generation

The project includes an enhanced data generator that injects realistic regularity patterns to improve compression:

- **Timestamp Regularity**: 100% perfect intervals vs 4.8% in standard data
- **Value Quantization**: Smart rounding to realistic precision levels  
- **Infrastructure Correlation**: Shared patterns across related services
- **Compression Gains**: 3.69x better compression (53.27x vs 14.42x)

See [Enhanced Compression Analysis](docs/enhanced-compression-analysis.md) for detailed technical analysis.

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
- ✅ String deduplication (8,658x+ compression on strings!)
- ✅ Fixed-width binary encoding for fast parsing
- ❌ Still row-based structure

📖 **[Technical Deep Dive: Binary Table Format](docs/phase3-binary-table-deep-dive.md)**

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
- ✅ Delta-delta encoding for regular timestamps (4.08x compression)
- ✅ Adaptive XOR/delta compression for values (1.21x compression)
- ✅ Bit-level optimization with leading zero compression
- ❌ Computational complexity

📖 **[Technical Deep Dive: Compression Tricks](docs/phase5-compression-tricks-deep-dive.md)**

### Phase 6: Downsampling
- ✅ Essential for long-term retention
- ✅ Multiple aggregation levels (1m, 5m, 15m, 1h)
- ✅ Huge space savings for historical data
- ❌ Lossy compression

📖 **[Technical Deep Dive: Downsampling Storage](docs/phase6-downsampling-deep-dive.md)**

### Phase 7: General-Purpose Compression (zstd)
- ✅ Excellent compression with no code changes
- ✅ Industry standard, battle-tested
- ✅ Can compete with specialized techniques
- ❌ Requires decompression for any access

## 🔧 Configuration Options

```bash
# Small dataset: 46,000 points (good for development/testing)
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
├── docs/                         # Technical deep dives
│   ├── phase3-binary-table-deep-dive.md
│   ├── phase5-compression-tricks-deep-dive.md
│   └── phase6-downsampling-deep-dive.md
└── output/                       # Generated files
```

## 📚 Technical Documentation

For detailed technical explanations of the compression algorithms:

- **[Phase 3: Binary Table Deep Dive](docs/phase3-binary-table-deep-dive.md)** - String deduplication and fixed-width encoding
- **[Phase 5: Compression Tricks Deep Dive](docs/phase5-compression-tricks-deep-dive.md)** - XOR compression, delta encoding, and bit-level optimization
- **[Phase 6: Downsampling Deep Dive](docs/phase6-downsampling-deep-dive.md)** - Multi-resolution storage and hierarchical retention

## 🎛️ Data Generation Features

The data generator creates realistic time-series patterns:

- **Random Walk**: Values follow realistic trends with volatility
- **Temporal Correlation**: Values are related to previous values  
- **Seasonal Patterns**: Daily/weekly cycles in the data
- **Integer Metrics**: Connection counts, queue sizes as proper integers
- **Realistic Labels**: Production-like host/region/environment combinations

## 💡 Key Insights

### Compression Technique Hierarchy
1. **Structural optimization** (row → columnar): **12.8x** compression
2. **String deduplication** (binary table): **5.0x** compression with fast access
3. **Specialized algorithms** (XOR/delta): **+11%** additional compression  
4. **General-purpose** (zstd): **7.9x** with zero code changes

### Data Pattern Exploitation
- **Low label cardinality**: 40 unique strings → 8,658x string compression
- **Temporal regularity**: 4.7% perfect intervals → 4x timestamp compression
- **Value correlation**: Similar consecutive values → XOR finds leading zeros
- **Adaptive selection**: Choose optimal algorithm per series (85% prefer XOR)

### Production Database Convergent Evolution
Time-series databases independently converged on similar techniques:
- **Facebook Gorilla**: XOR compression with bit packing
- **InfluxDB**: Timestamp + value compression  
- **TimescaleDB**: Columnar storage + specialized encoding
- **Apache Parquet**: Dictionary encoding + columnar layout

### The Simplicity vs. Sophistication Trade-off
- **zstd (7.9x)**: Excellent results with zero algorithm complexity
- **Specialized (14.3x)**: Better compression but requires custom implementation
- **Downsampling (19.3x)**: Essential for long-term retention, but lossy

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