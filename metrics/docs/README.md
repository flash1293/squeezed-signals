# Metrics: Time-Series Storage Engine Evolution

A comprehensive demonstration of how time-series metrics storage formats evolve from simple JSON to highly optimized binary formats with compression. This project shows the journey from **84MB** of human-readable JSON down to **1MB** of compressed specialized data - a **79.7x compression ratio** - while maintaining full data fidelity.

## 🎯 Overview

This project demonstrates the evolution of metrics storage through 7 distinct phases, showing how general-purpose compression (zstd) integrates with structural optimizations:

1. **NDJSON Baseline** - Human-readable but inefficient
2. **CBOR Encoding** - Better binary serialization  
3. **CBOR + zstd** - First compression layer
4. **Binary Table + zstd** - String deduplication with compression
5. **Columnar Storage + zstd** - Grouping by time series with compression
6. **Enhanced Compression Tricks + zstd** - Advanced pattern-aware algorithms with compression
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
python main.py --size big      # 500K points
python main.py --size huge     # 100M points (requires significant memory)
```

## 📊 Results Preview

With real dataset (500,000 points):

| Phase | Format | Size | Compression | Key Innovation |
|-------|--------|------|-------------|----------------|
| 1 | NDJSON | 80.8 MB | 1.0x | Human readable baseline |
| 2 | CBOR | 63.9 MB | 1.3x | Binary encoding |
| 3 | CBOR + zstd | 3.8 MB | 21.1x | First compression layer |
| 4 | Binary Table + zstd | 2.7 MB | 29.4x | String deduplication + compression |
| 5 | Columnar + zstd | 2.0 MB | 40.2x | Series grouping + compression |
| 6 | **Enhanced Compression + zstd** | **1.0 MB** | **79.7x** | **Advanced pattern-aware algorithms** |
| 7 | Downsampled (total) | 0.9 MB | 90.4x | Multi-resolution long-term storage |

**🎯 Key Achievement: 79.7x compression** with enhanced pattern-aware algorithms + maximum zstd compression

## 🔬 Enhanced Compression Features

### Advanced Pattern Detection
- **Near-constant detection**: Minimal variation series (server status, process IDs)
- **Power-of-2 optimization**: Buffer sizes, memory allocations
- **Integer-heavy encoding**: Predominantly integer data with occasional decimals
- **Exponential patterns**: Growth/decay series (traffic scaling, resource usage)
- **Periodic patterns**: Daily/weekly cyclical metrics (load patterns)
- **Quantized steps**: Discrete level changes (threshold-based metrics)

### Sophisticated Algorithms
- **Enhanced XOR compression**: Bit-level optimization with leading/trailing zero detection
- **Advanced delta encoding**: Variable-length encoding with zero optimization
- **Dictionary compression**: For series with limited unique values
- **Metadata optimization**: Aggressive compression of series metadata
- **Maximum zstd**: Level 22 compression for ultimate efficiency

## 🔬 Data Generation Options

### Synthetic Data Generator (Default)
Creates realistic time-series patterns that improve compression without sacrificing realism:

- **Infrastructure Correlation**: Services on same platforms show shared load patterns
- **Value Quantization**: Realistic precision levels (percentages to 1-2 decimals, latencies rounded appropriately)  
- **Timestamp Regularity**: High percentage of perfect intervals reflecting modern monitoring systems

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
DATASET_SIZE=huge    # ~100,000,000 points

# Cache management (automatic, per generator+size combination)
rm output/raw_dataset.pkl  # Force regeneration
```

## 📖 Technical Documentation

### Complete Phase Analysis
- [Phase 1: NDJSON Characteristics](docs/phase1-ndjson-characteristics.md) - Baseline format analysis
- [Phase 2: CBOR Characteristics](docs/phase2-cbor-characteristics.md) - Binary serialization benefits
- [Phase 3: CBOR + zstd Characteristics](docs/phase3-cbor-zstd-characteristics.md) - General-purpose compression
- [Phase 4: Binary Table + zstd Characteristics](docs/phase4-binary-table-zstd-characteristics.md) - Structural optimization + compression
- [Phase 5: Columnar Storage + zstd Characteristics](docs/phase5-columnar-storage-zstd-characteristics.md) - Data organization optimization
- [Phase 6: Enhanced Compression Tricks + zstd Characteristics](docs/phase6-compression-tricks-zstd-characteristics.md) - Advanced pattern-aware algorithms + compression
- [Phase 7: Downsampling + zstd Characteristics](docs/phase7-downsampling-zstd-characteristics.md) - Multi-resolution storage

## 💡 Key Insights

### Compression Technique Hierarchy
1. **Binary encoding** (JSON → CBOR): **1.3x** compression
2. **General-purpose compression** (CBOR + zstd): **21.1x** with minimal changes
3. **String deduplication + zstd** (binary table): **29.4x** compression with structural optimization
4. **Columnar organization + zstd** (series grouping): **40.2x** by eliminating redundancy
5. **🏆 Enhanced pattern-aware + zstd** (advanced algorithms): **79.7x** ultimate compression

### Advanced Pattern Exploitation
- **Near-constant series**: Store base value + tiny deltas (massive compression)
- **Power-of-2 patterns**: Logarithmic encoding vs full float storage
- **Integer-heavy data**: Separate integer/fractional compression paths
- **Periodic patterns**: Template + deviation encoding for cyclical data
- **Exponential series**: Base + ratio + deviations for growth patterns

### Production Database Convergent Evolution
Time-series databases independently converged on similar techniques:
- **Facebook Gorilla**: XOR compression with bit packing
- **InfluxDB**: Timestamp + value compression with specialized encoding
- **TimescaleDB**: Columnar storage + compression optimization
- **Apache Parquet**: Dictionary encoding + columnar layout + compression

## 🌍 Real-World Applications

This evolution mirrors production time-series databases:

- **Prometheus**: Uses columnar storage with compression
- **InfluxDB**: Implements similar timestamp/value compression techniques
- **TimescaleDB**: Combines relational and time-series optimizations
- **VictoriaMetrics**: Advanced compression for high-cardinality metrics
