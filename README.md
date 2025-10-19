# Squeezed Signals: The Evolution of Observability Data Storage

This repository demonstrates the progressive optimization of observability data storage across **metrics**, **traces**, and **logs** - moving from simple, human-readable formats to highly compressed, efficient storage systems. Each signal type explores different compression challenges and optimization strategies.

## 🎯 Project Overview

Modern observability systems generate massive amounts of data across three primary signal types:

- **📊 Metrics**: Time-series numerical data (CPU usage, response times, etc.)
- **🔍 Traces**: Distributed request execution paths and timing
- **📝 Logs**: Structured and unstructured text-based event records

Each signal type presents unique storage optimization opportunities and challenges. This project demonstrates how to achieve dramatic compression ratios while maintaining data fidelity and query performance.

## 📁 Repository Structure

```
squeezed-signals/
├── README.md                    # This file - project overview
├── metrics/                     # Time-series metrics storage optimization
│   ├── README.md               # Metrics-specific documentation
│   ├── main.py                 # Metrics pipeline orchestration
│   ├── 00_generate_data.py     # Metrics data generation
│   ├── 01_ndjson_storage.py    # Baseline NDJSON storage
│   ├── 02_cbor_storage.py      # Binary serialization
│   ├── 03_cbor_zstd.py        # General-purpose compression
│   ├── 04_binary_table.py     # Fixed-width binary format
│   ├── 05_columnar_storage.py # Columnar organization
│   ├── 06_compression_tricks.py# Advanced time-series compression
│   ├── 07_downsampling_storage.py # Long-term storage via aggregation
│   ├── lib/                    # Shared utilities and encoders
│   ├── docs/                   # Per-phase analysis documentation
│   └── output/                 # Generated data files and results
├── traces/                      # [Coming Soon] Distributed trace optimization
│   └── README.md               # Trace-specific documentation
└── logs/                       # [Coming Soon] Log data optimization
    └── README.md               # Log-specific documentation
```

## 🚀 Getting Started

Each signal type is a complete, self-contained demonstration that can be run independently:

### Metrics Storage Evolution

```bash
cd metrics/
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run the complete metrics evolution pipeline
python main.py --size small

# Or test with real monitoring data
DATA_GENERATOR=real python main.py --size big
```

### Traces & Logs (Coming Soon)

```bash
# Future implementations
cd traces/
python main.py

cd logs/
python main.py
```

## 📊 Signal-Specific Optimization Strategies

### 📈 Metrics: Time-Series Compression
**Challenge**: Repetitive timestamps, correlated values, metadata redundancy  
**Techniques**: Delta encoding, XOR compression, columnar storage, downsampling  
**Results**: **79.7x compression** (84MB → 1MB) with enhanced algorithms

**Key Innovations:**
- **Pattern-aware compression**: Detects constant, sparse, quantized, and periodic patterns
- **Advanced timestamp encoding**: Double-delta with run-length encoding
- **Enhanced value compression**: Gorilla-style XOR with bit-level optimization
- **Intelligent downsampling**: Multi-resolution storage for long-term retention

### 🔍 Traces: Distributed Execution Optimization
**Challenge**: Complex nested structures, span relationships, high cardinality attributes  
**Techniques**: [To be implemented]  
**Target**: Efficient storage of distributed request traces with minimal overhead

**Planned Innovations:**
- **Span compression**: Leveraging parent-child relationships
- **Attribute deduplication**: Common tag extraction and referencing
- **Temporal correlation**: Exploiting timing patterns in distributed systems
- **Service topology**: Graph-based compression using service relationships

### 📝 Logs: Structured Text Compression
**Challenge**: Semi-structured text, repetitive patterns, variable field schemas  
**Techniques**: [To be implemented]  
**Target**: Maximum compression for both structured and unstructured log data

**Planned Innovations:**
- **Template extraction**: Pattern detection for log message templates
- **Field-specific compression**: Optimized encoding per log field type
- **Schema evolution**: Handling changing log structures over time
- **Content-aware compression**: Different strategies for stack traces, JSON, etc.

## 🎖️ Current Achievements

### Metrics Storage Evolution ✅ **COMPLETE**
- **54.58x compression** vs NDJSON baseline with enhanced algorithms
- **3.19 bytes per data point** using advanced pattern detection
- **24.2% improvement** over standard compression techniques
- **Perfect data fidelity** with comprehensive verification
- **Real dataset support** using Westermo monitoring data
- **Multi-resolution storage** with intelligent downsampling

**Advanced Features:**
- **10+ pattern detection algorithms** (near-constant, power-of-2, exponential, periodic)
- **Enhanced XOR compression** with bit-level optimization
- **Aggressive metadata compression** with dictionary encoding  
- **Maximum zstd compression** (level 22) for ultimate efficiency
- **Three dataset sizes** (small/big/huge) up to 100M data points

## 🔬 Technical Deep Dives

Each signal type includes comprehensive documentation of:

- **Algorithm explanations**: How each compression technique works
- **Performance analysis**: Detailed benchmarking and efficiency metrics
- **Trade-off discussions**: Space vs time complexity considerations
- **Real-world applicability**: When and where to use each approach
- **Implementation details**: Bit-level encoding and optimization techniques

## 🌟 Key Insights

### Universal Observability Principles
1. **Pattern Recognition**: All signal types benefit from identifying and exploiting data patterns
2. **Domain-Specific Knowledge**: Understanding data characteristics enables targeted optimization
3. **Layered Compression**: Combining specialized algorithms with general-purpose compression
4. **Trade-off Management**: Balancing storage efficiency with query performance and complexity

### Signal-Specific Learnings
- **Metrics**: Temporal correlation and value similarity enable massive compression gains
- **Traces**: [To be discovered] Relationship structures and execution patterns
- **Logs**: [To be discovered] Template extraction and field-specific optimization

## 🎯 Future Roadmap

### Phase 1: Traces Storage Evolution 🔄 **IN PROGRESS**
- Distributed trace data generation and modeling
- Span relationship compression techniques
- Service topology-aware optimization
- Multi-tenant trace storage strategies

### Phase 2: Logs Storage Evolution 📋 **PLANNED**
- Structured and unstructured log data handling
- Template-based compression for repetitive log patterns
- Field-specific optimization strategies
- Schema evolution and backwards compatibility

### Phase 3: Cross-Signal Optimization 🔗 **FUTURE**
- Correlation-aware compression across signal types
- Unified observability storage architecture
- Query-optimized data layouts
- Real-time vs batch processing trade-offs

## � Documentation

Each signal type includes detailed documentation:

- **Implementation guides**: Step-by-step technique explanations
- **Performance analysis**: Comprehensive benchmarking results
- **Algorithm deep dives**: Detailed technical breakdowns
- **Best practices**: When and how to apply each optimization

## 🤝 Contributing

This project demonstrates storage optimization techniques for educational and research purposes. Contributions welcome for:

- Additional compression algorithms and techniques
- Performance improvements and optimizations
- New signal types and data formats
- Real-world dataset integrations
- Documentation and analysis improvements

## 🏆 Project Goals

1. **Educational**: Demonstrate the evolution from naive to sophisticated storage approaches
2. **Practical**: Provide working implementations suitable for production adaptation
3. **Comprehensive**: Cover all major observability signal types and optimization strategies
4. **Research**: Explore cutting-edge compression techniques and novel approaches

## 📄 License

This project is licensed under the MIT License - see individual signal folders for specific licensing information.

---

**🎯 Start with the metrics implementation to see the complete evolution from 84MB NDJSON to 1MB compressed storage with perfect data fidelity!**

## �🔬 Metrics Data Generation Options
