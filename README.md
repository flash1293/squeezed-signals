# Squeezed Signals: Metrics Storage Engine Evolution

A comprehensive demonstration of how time-series metrics storage formats evolve from simple JSON to highly optimized binary formats with compression. This project shows the journey from **7.8MB** of human-readable JSON down to **0.18MB** of compressed specialized data - a **44.3x compression ratio** - while maintaining full data fidelity.

## 🎯 Overview

This project demonstrates the evolution of metrics storage through 7 distinct phases, showing how general-purpose compression (zstd) integrates with structural optimizations:

1. **NDJSON Baseline** - Human-readable but inefficient
2. **CBOR Encoding** - Better binary serialization  
3. **CBOR + zstd** - First compression layer
4. **Binary Table + zstd** - String deduplication with compression
5. **Columnar Storage + zstd** - Grouping by time series with compression
6. **Compression Tricks + zstd** - Specialized algorithms with compression
7. **Downsampling + zstd** - Multi-resolution storage with compression

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
python main.py --size big      # 5M points
python main.py --size huge     # 100M points (requires significant memory)
```

## 📊 Results Preview

With enhanced dataset (48,000 points):

| Phase | Format | Size | Compression | Key Innovation |
|-------|--------|------|-------------|----------------|
| 1 | NDJSON | 7.8 MB | 1.0x | Human readable baseline |
| 2 | CBOR | 6.2 MB | 1.3x | Binary encoding |
| 3 | CBOR + zstd | 0.39 MB | 19.8x | First compression layer |
| 4 | Binary Table + zstd | 0.32 MB | 24.5x | String deduplication + compression |
| 5 | Columnar + zstd | 0.22 MB | 35.3x | Series grouping + compression |
| 6 | **Compression Tricks + zstd** | **0.18 MB** | **44.3x** | **Specialized algorithms + compression** |

**🎯 Key Achievement: 44.3x compression** with specialized time-series algorithms + zstd compression applied throughout the pipeline

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

## 📖 Technical Documentation

### Complete Phase Analysis
- [Phase 1: NDJSON Characteristics](docs/phase1-ndjson-characteristics.md) - Baseline format analysis
- [Phase 2: CBOR Characteristics](docs/phase2-cbor-characteristics.md) - Binary serialization benefits
- [Phase 3: CBOR + zstd Characteristics](docs/phase3-cbor-zstd-characteristics.md) - General-purpose compression
- [Phase 4: Binary Table + zstd Characteristics](docs/phase4-binary-table-zstd-characteristics.md) - Structural optimization + compression
- [Phase 5: Columnar Storage + zstd Characteristics](docs/phase5-columnar-storage-zstd-characteristics.md) - Data organization optimization
- [Phase 6: Compression Tricks + zstd Characteristics](docs/phase6-compression-tricks-zstd-characteristics.md) - Specialized algorithms + compression
- [Phase 7: Downsampling + zstd Characteristics](docs/phase7-downsampling-zstd-characteristics.md) - Multi-resolution storage

## 🔍 Phase Details

### Phase 1: NDJSON Baseline
```json
{"timestamp": 1760860006, "metric_name": "http_request_duration_seconds", "value": 257.94, "labels": {"host": "server-c", "region": "ap-southeast-1"}}
```
- ✅ Human readable, debuggable
- ❌ Massive key repetition, inefficient numbers

📖 **[Full Analysis: NDJSON Characteristics](docs/phase1-ndjson-characteristics.md)**

### Phase 2: CBOR Encoding
- ✅ Binary format, preserves structure
- ✅ Better type encoding (integers, floats)
- ❌ Still denormalized with repeated metadata

📖 **[Full Analysis: CBOR Characteristics](docs/phase2-cbor-characteristics.md)**

### Phase 3: CBOR + zstd Compression
- ✅ Excellent compression with minimal code changes
- ✅ Industry standard zstd compression  
- ❌ Still preserves underlying redundancy

📖 **[Full Analysis: CBOR + zstd Characteristics](docs/phase3-cbor-zstd-characteristics.md)**

### Phase 4: Binary Table + zstd
- ✅ String deduplication (91,932x+ compression on strings!)
- ✅ Fixed-width binary encoding for fast parsing
- ❌ Still denormalized structure

📖 **[Complete Analysis: Binary Table + zstd](docs/phase4-binary-table-zstd-characteristics.md)**

### Phase 5: Columnar Storage + zstd
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
- ✅ Groups related data for optimal compression
- ❌ Requires decompression for access

📖 **[Complete Analysis: Columnar Storage + zstd](docs/phase5-columnar-storage-zstd-characteristics.md)**

### Phase 6: Compression Tricks + zstd
- ✅ Specialized algorithms for time-series patterns
- ✅ Adaptive XOR/delta compression selection per series
- ✅ Additional zstd compression on optimized data
- ❌ High computational complexity

📖 **[Complete Analysis: Compression Tricks + zstd](docs/phase6-compression-tricks-zstd-characteristics.md)**

### Phase 7: Downsampling + zstd
- ✅ Multi-resolution storage for long-term retention
- ✅ Dramatic data reduction (up to 96.7% fewer points)
- ✅ Fast queries over long time ranges
- ❌ Lossy compression (precision loss)

📖 **[Complete Analysis: Downsampling + zstd](docs/phase7-downsampling-zstd-characteristics.md)**



## 🔧 Configuration Options

```bash
# Small dataset: 50,000 points (good for development/testing)
python main.py --size small

# Big dataset: 5,000,000 points (realistic production scale)
python main.py --size big

# Huge dataset: 100,000,000 points (compression benchmarking - requires 8-16GB RAM)
python main.py --size huge
```

## 📁 Project Structure

```
squeezed-signals/
├── 00_generate_data.py           # Realistic time-series data generation
├── 01_ndjson_storage.py          # Phase 1: NDJSON baseline
├── 02_cbor_storage.py            # Phase 2: CBOR encoding
├── 03_cbor_zstd.py               # Phase 3: CBOR + zstd compression
├── 04_binary_table.py            # Phase 4: Binary table + zstd
├── 05_columnar_storage.py        # Phase 5: Columnar grouping + zstd
├── 06_compression_tricks.py      # Phase 6: Specialized algorithms + zstd
├── 07_downsampling_storage.py    # Phase 7: Multi-resolution storage + zstd
├── main.py                       # Orchestration script
├── lib/
│   ├── data_generator.py         # Realistic data patterns
│   └── encoders.py              # Compression algorithms
├── docs/                         # Technical documentation
│   ├── data-generation-deep-dive.md
│   ├── phase1-ndjson-characteristics.md
│   ├── phase2-cbor-characteristics.md  
│   ├── phase3-cbor-zstd-characteristics.md
│   ├── phase4-binary-table-zstd-characteristics.md
│   ├── phase5-columnar-storage-zstd-characteristics.md
│   ├── phase6-compression-tricks-zstd-characteristics.md
│   └── phase7-downsampling-zstd-characteristics.md
└── output/                       # Generated files
```

## 📚 Complete Documentation

The project includes comprehensive documentation for each phase:

Each phase includes comprehensive documentation combining technical implementation details with performance analysis, pros/cons, and real-world applications:

- **[Data Generation Deep Dive](docs/data-generation-deep-dive.md)** - How realistic patterns enhance compression
- **[Complete Phase Documentation](docs/)** - All phase characteristics with algorithm implementation details

## 🎛️ Data Generation Features

The data generator creates realistic time-series patterns:

- **Random Walk**: Values follow realistic trends with volatility
- **Temporal Correlation**: Values are related to previous values  
- **Seasonal Patterns**: Daily/weekly cycles in the data
- **Integer Metrics**: Connection counts, queue sizes as proper integers
- **Realistic Labels**: Production-like host/region/environment combinations

## 💡 Key Insights

### Compression Technique Hierarchy
1. **Binary encoding** (JSON → CBOR): **1.3x** compression
2. **General-purpose compression** (CBOR + zstd): **19.8x** with minimal changes
3. **String deduplication + zstd** (binary table): **24.5x** compression with structural optimization
4. **Columnar organization + zstd** (series grouping): **35.3x** by eliminating redundancy
5. **🏆 Specialized algorithms + zstd** (temporal patterns): **44.3x** ultimate compression

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
- **CBOR + zstd (19.8x)**: Excellent results with minimal code changes
- **Structural + zstd (24.5x)**: Good balance of optimization and compression
- **Columnar + zstd (35.3x)**: Better structure with compression benefits
- **Specialized + zstd (44.3x)**: Ultimate compression combining domain knowledge with general-purpose algorithms

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

The complete demonstration shows how thoughtful storage format evolution can achieve **44.3x compression** while maintaining full data fidelity - essential for cost-effective metrics storage at scale. The key insight is that general-purpose compression (zstd) works best when combined with structural optimizations and specialized algorithms, rather than as a final step.

The enhanced data generation demonstrates that understanding and leveraging natural patterns in monitoring data can provide substantial compression improvements without sacrificing realism.