# Squeezed Signals: Metrics Storage Engine Evolution

A comprehensive demonstration of how time-series metrics storage formats evolve from simple JSON to highly optimized binary formats. This project shows the journey from **81MB** of human-readable JSON down to **1.8MB** of hybrid compressed data - a **45x compression ratio** - while maintaining full data fidelity.

## 🎯 Overview

This project demonstrates the evolution of metrics storage through 8 distinct phases, each building upon the previous to show different optimization techniques:

1. **NDJSON Baseline** - Human-readable but inefficient
2. **CBOR Encoding** - Better binary serialization  
3. **Binary Table** - String deduplication with fixed-width encoding
4. **Columnar Storage** - Grouping by time series 
5. **Compression Tricks** - Specialized time-series algorithms
6. **Downsampling** - Long-term storage with aggregation
7. **General-Purpose Compression** - zstd as comparison baseline
8. **Hybrid Compression** - Ultimate compression combining tricks + zstd

## 🚀 Quick Start

```bash
# Set up the environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run the complete demonstration with synthetic data (default)
python main.py --size small

# Use real monitoring data instead
DATA_GENERATOR=real python main.py --size small

# Generate larger datasets
DATASET_SIZE=big python main.py --size big
```

## 📊 Results Preview

With enhanced dataset (48,000 points):

| Phase | Format | Size | Compression | Key Innovation |
|-------|--------|------|-------------|----------------|
| 1 | NDJSON | 81.0 MB | 1.0x | Human readable baseline |
| 2 | CBOR | 64.0 MB | 1.27x | Binary encoding |
| 3 | Binary Table | 16.7 MB | 4.85x | String deduplication (9,507x) |
| 4 | Columnar | 6.7 MB | 12.1x | Series grouping |
| 5 | **Compression Tricks** | **4.8 MB** | **16.9x** | **Temporal algorithms** |
| 6 | Downsampling | 0.30 MB | 270x | Multi-resolution storage |
| 7 | NDJSON (zstd) | 4.3 MB | 18.8x | General-purpose compression |
| 8 | **🏆 Hybrid (Tricks+zstd)** | **1.8 MB** | **45.0x** | **Ultimate compression** |

**🎯 Key Achievement: 45x compression** with Phase 8 Hybrid Compression (ultimate ratio combining specialized algorithms with zstd)

## 🔬 Data Generation Options

### Synthetic Data Generator (Default)
Creates realistic time-series patterns that improve compression without sacrificing realism:

- **Infrastructure Correlation**: Services on same platforms show shared load patterns
- **Value Quantization**: Realistic precision levels (percentages to 1-2 decimals, latencies rounded appropriately)  
- **Timestamp Regularity**: 94.6% perfect intervals reflecting modern monitoring systems

### Real Data Generator
Uses actual performance monitoring data from the [Westermo test-system-performance-dataset](https://github.com/westermo/test-system-performance-dataset):

- **Authentic Patterns**: Real system metrics from production environments
- **Diverse Metrics**: CPU, memory, disk, network, and system load data
- **Natural Irregularities**: Actual timestamp patterns and value distributions
- **Smart Caching**: Generated datasets are cached to speed up subsequent runs

```bash
# Use real monitoring data
DATA_GENERATOR=real python main.py --size small

# Control dataset size (both generators)
DATASET_SIZE=small   # ~50,000 points
DATASET_SIZE=big     # ~500,000 points

# Cache management (automatic, per generator+size combination)
rm output/raw_dataset.pkl  # Force regeneration
```
- **Platform Stability**: Well-managed services show reduced random variation

**Compression Breakdown in Phase 5:**
- **Timestamp compression**: 43.75x (delta-delta encoding + 94.6% zero deltas)
- **Value compression**: 1.71x (adaptive XOR/delta with bit-level encoding)
- **Zero delta optimization**: 94.6% perfect timestamp regularity
- **Overall improvement**: 2.2x better than columnar storage

## 🛤️ The Evolution Journey

## 📖 Technical Deep Dives

- [Data Generation Deep Dive](docs/data-generation-deep-dive.md) - How realistic patterns enhance compression
- [Phase 3: Binary Table Deep Dive](docs/phase3-binary-table-deep-dive.md) - String deduplication and fixed-width encoding
- [Phase 5: Compression Tricks Deep Dive](docs/phase5-compression-deep-dive.md) - Temporal algorithms and bit-level optimization  
- [Phase 6: Downsampling Deep Dive](docs/phase6-downsampling-deep-dive.md) - Multi-resolution storage strategies

## 🔍 Phase Details

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

### Phase 8: Hybrid Compression (Tricks + zstd)
- ✅ Ultimate compression ratio (45x over baseline)
- ✅ Leverages both specialized and general-purpose algorithms
- ✅ 2.7x improvement over already-compressed Phase 5 data
- ✅ Production-ready zstd format for final storage
- ❌ Double compression overhead (Phase 5 + zstd)
- ❌ Complex two-stage decompression required
- ❌ Higher computational cost for read/write operations

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
├── 08_hybrid_compression.py      # Phase 8: Ultimate hybrid compression
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
1. **Structural optimization** (row → columnar): **12.1x** compression
2. **String deduplication** (binary table): **4.9x** compression with fast access
3. **Specialized algorithms** (XOR/delta): **16.9x** with temporal patterns
4. **General-purpose** (zstd): **18.8x** with zero code changes
5. **🏆 Hybrid approach** (specialized + zstd): **45.0x** ultimate compression

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
- **zstd (18.8x)**: Excellent results with zero algorithm complexity
- **Specialized (16.9x)**: Good compression with custom temporal algorithms
- **Hybrid (45.0x)**: Ultimate compression combining specialized + general-purpose
- **Downsampling (270x)**: Essential for long-term retention, but lossy

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

The complete demonstration shows how thoughtful storage format evolution can achieve **45x compression** while maintaining full data fidelity - essential for cost-effective metrics storage at scale. Phase 8 hybrid compression represents the ultimate combination of specialized time-series algorithms with general-purpose compression, achieving maximum space efficiency.

The enhanced data generation demonstrates that understanding and leveraging natural patterns in monitoring data can provide substantial compression improvements without sacrificing realism.