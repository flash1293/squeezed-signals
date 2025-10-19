# The Evolution of a Metrics Storage Engine

This project demonstrates the progressive optimization of time-series metric data storage, moving from a simple, human-readable format to a highly compressed, efficient binary format. Each step is a self-contained Python script that takes a generated dataset and writes it to disk, reporting the final storage size.

## 🎯 Project Overview

The goal is to show how real-world time-series databases achieve their impressive compression ratios and query performance through a series of incremental improvements. You'll see how we go from **gigabytes of JSON** to **megabytes of highly compressed binary data** while maintaining full fidelity.

## 🗂️ Project Structure

```
squeezed-signals/
├── 00_generate_data.py          # Phase 0: Generate realistic dataset
├── 01_ndjson_storage.py         # Phase 1: Baseline NDJSON format
├── 02_columnar_storage.py       # Phase 2: Columnar restructuring
├── 03_compressed_columnar.py    # Phase 3: Specialized compression
├── 04_custom_binary_format.py   # Phase 4: Self-contained binary format
├── 05_downsampling_storage.py   # Phase 5: Long-term retention via downsampling
├── main.py                      # Orchestrates all phases
├── lib/
│   ├── data_generator.py        # Realistic data generation utilities
│   └── encoders.py              # Compression algorithms (delta, RLE, XOR)
├── output/                      # All generated files
└── README.md                    # This file
```

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install msgpack
   ```

2. **Run the complete demonstration:**
   ```bash
   python main.py
   ```

   This will execute all phases sequentially and provide a comprehensive comparison.

3. **Or run individual phases:**
   ```bash
   python 00_generate_data.py
   python 01_ndjson_storage.py
   python 02_columnar_storage.py
   # ... and so on
   ```

## 📊 The Data Model

All phases operate on a consistent dataset representing typical observability metrics:

- **Timestamp:** 64-bit integer (nanoseconds since epoch)
- **Metric Name:** String (e.g., `cpu_usage_percent`, `http_requests_total`)
- **Value:** 64-bit float
- **Labels/Tags:** Dictionary of key-value strings (e.g., `{"host": "server-a", "region": "us-east-1"}`)

## 🛤️ The Evolution Journey

### Phase 0: Data Generation
**Goal:** Create realistic, compressible dataset

Generates time-series data that mimics real observability metrics with:
- Semi-regular intervals (15s ± jitter)
- Realistic value patterns (sine waves, random walks)
- Typical label cardinality and distribution

### Phase 1: Baseline NDJSON 📄
**Goal:** Establish simple, human-readable baseline

**Format:** One JSON object per line
```json
{"timestamp": 1697123456, "metric_name": "cpu_usage", "value": 75.2, "labels": {"host": "server-a"}}
```

**Characteristics:**
- ✅ Human-readable, debuggable with standard tools
- ❌ Massive key repetition, inefficient number encoding

### Phase 2: Columnar Storage 📋
**Goal:** Restructure from rows to columns

**Key Innovation:** Group by time series, separate metadata from data

**Format:**
```python
{
  "series_metadata": {
    "0": {"name": "cpu_usage", "labels": {"host": "server-a"}},
    "1": {"name": "cpu_usage", "labels": {"host": "server-b"}}
  },
  "series_data": {
    "0": {
      "timestamps": [1697123456, 1697123471, ...],
      "values": [75.2, 76.1, ...]
    }
  }
}
```

**Benefits:**
- Eliminates metadata repetition
- Enables column-specific compression
- Faster single-series queries

### Phase 3: Compressed Columnar 🗜️
**Goal:** Apply specialized compression algorithms

**Techniques:**
- **Double-Delta Encoding:** Timestamps → deltas → delta-of-deltas
- **Run-Length Encoding:** Compress sequences of zeros
- **XOR Encoding:** Gorilla-style float compression
- **Variable-Length Integer Encoding**

**Benefits:**
- 90%+ compression ratios typical
- Leverages data patterns (regular intervals, similar values)
- Maintains full precision

### Phase 4: Custom Binary Format 📦
**Goal:** Create self-contained, production-ready format

**Structure:**
```
[Header: METRICS! + Version]
[Index Section Length]
[Data Section Offset]
[Index Section: Series metadata + offsets]
[Data Section: Compressed series blocks]
```

**Benefits:**
- Self-documenting with version info
- Efficient random access via index
- Mimics real database file layout

### Phase 5: Downsampling 📉
**Goal:** Long-term retention via aggregation

**Process:**
1. Group high-resolution data into time buckets
2. Calculate multiple aggregates (avg, max, min, p95, p99)
3. Store using efficient format from Phase 4

**Aggregates Generated:**
- `cpu_usage_avg_5m`, `cpu_usage_max_5m`, `cpu_usage_p95_5m`
- Multiple intervals: 1min, 5min, 15min, 1hour

**Benefits:**
- Orders of magnitude data reduction
- Faster long-range queries
- Cost-effective long-term storage

## 📈 Expected Results

Typical compression ratios from a 50,000 data point dataset:

| Format | Size | Compression | Use Case |
|--------|------|-------------|----------|
| NDJSON | ~5 MB | 1.0x (baseline) | Development, debugging |
| Columnar | ~1 MB | 5x | Initial optimization |
| Compressed | ~200 KB | 25x | Production storage |
| Custom Binary | ~210 KB | 24x | Production + metadata |
| Downsampled Total | ~50 KB | 100x | Long-term retention |

## 🛠️ Real-World Applications

### Production Scaling
For a system with 1,000 metrics at 15-second intervals:
- **Raw NDJSON:** ~100 GB/day
- **Compressed:** ~4 GB/day  
- **With Downsampling:** ~1 GB/year for historical data

### Time-Series Database Features Demonstrated
- **InfluxDB/TimescaleDB:** Columnar storage with compression
- **Prometheus:** Custom binary format with efficient querying
- **Grafana/VictoriaMetrics:** Multi-resolution storage policies
- **AWS Timestream:** Automated tiered storage with downsampling

## 🎓 Educational Concepts

This project illustrates key computer science and systems concepts:

1. **Data Structure Trade-offs:** Row vs columnar storage
2. **Compression Algorithms:** Delta encoding, RLE, entropy coding
3. **File Format Design:** Headers, indexes, binary protocols
4. **Storage Hierarchies:** Hot, warm, cold data management
5. **Lossy vs Lossless Compression:** Precision vs storage efficiency

## 🔧 Implementation Notes

### Dependencies
- `msgpack`: Efficient binary serialization
- Standard library: `struct`, `statistics`, `pickle`

### Key Algorithms
- **Double-Delta Encoding:** Captures regular timestamp intervals
- **Gorilla XOR Encoding:** Exploits temporal locality in float values
- **Run-Length Encoding:** Compresses sequences of identical values
- **Variable-Length Integers:** Space-efficient integer storage

### Performance Considerations
- Memory usage scales with series count, not data points
- Compression is CPU-intensive but enables massive I/O savings
- Random access requires index structures

## 🚧 Extensions and Improvements

Potential enhancements for learning:

1. **Advanced Compression:**
   - Dictionary compression for label values
   - Bit packing for small integers
   - Huffman coding for symbol tables

2. **Query Optimization:**
   - Bloom filters for series existence
   - Time-based partitioning
   - Parallel decompression

3. **Production Features:**
   - Write-ahead logs for durability
   - Block-level checksums
   - Schema evolution support

4. **Distributed Systems:**
   - Sharding strategies
   - Replication and consistency
   - Cross-datacenter deployment

## 📚 Learning Resources

- [Gorilla Paper](https://www.vldb.org/pvldb/vol8/p1816-teller.pdf): Facebook's time-series compression
- [InfluxDB Storage Engine](https://docs.influxdata.com/influxdb/): TSM file format details
- [Prometheus TSDB](https://ganeshvernekar.com/blog/prometheus-tsdb-the-head-block/): Block structure analysis
- [Time-Series Databases Explained](https://blog.timescale.com/blog/what-the-heck-is-time-series-data-and-why-do-i-need-a-time-series-database-dcf3b1b18563/)

## 🤝 Contributing

This is an educational project. Suggestions for improvements:
- Additional compression algorithms
- More realistic data generation patterns
- Query performance benchmarks
- Alternative storage formats

## 📄 License

MIT License - Feel free to use this for educational purposes!

---

*This project demonstrates that the "magic" of time-series databases is really just good engineering applied systematically. Each optimization builds on the previous one, showing how small improvements compound into dramatic results.*