# Squeezed Signals: The Evolution of Observability Data Storage

This repository demonstrates the progressive optimization of observability data storage across **metrics**, **traces**, and **logs**.

## 🎯 Project Overview

Modern observability systems generate massive amounts of data across three primary signal types:

- **📊 Metrics**: Time-series numerical data (CPU usage, response times, etc.)
- **🔍 Traces**: Distributed request execution paths and timing
- **📝 Logs**: Structured and unstructured text-based event records

Each signal type presents unique storage optimization opportunities and challenges. This project demonstrates how to achieve dramatic compression ratios while maintaining data fidelity and query performance.

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

### Traces Storage Evolution

```bash
cd traces/
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run the complete traces evolution pipeline
python main.py --size small

# Test with larger datasets
python main.py --size medium  # 1,000 traces
python main.py --size big     # 10,000 traces
```

### Logs Storage Evolution

```bash
cd logs/
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run the complete logs evolution pipeline
python main.py --size small

# Test with larger datasets
python main.py --size big
python main.py --size huge
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
**Techniques**: Service topology mapping, parent-child delta encoding, columnar storage  
**Results**: **22.21x compression** (1.4MB → 64KB) with relationship-aware algorithms

**Key Innovations:**
- **Span relationship compression**: Leveraging parent-child relationships with delta encoding
- **Service topology deduplication**: Common service/operation name extraction and referencing
- **Timestamp delta compression**: Exploiting temporal correlation within trace boundaries
- **Columnar trace storage**: Column-oriented layout with column-specific compression algorithms
- **Dual optimization paths**: Relationship-focused (22x) vs Analytics-focused (18x)
- **Microservices pattern detection**: Realistic 12+ service architecture simulation

### 📝 Logs: Structured Text Compression
**Challenge**: Semi-structured text, repetitive patterns, variable field schemas  
**Techniques**: Template extraction, variable classification, columnar encoding, smart ordering  
**Status**: **Implementation in progress** (Phases 0-6 complete)

**Implemented Innovations:**
- **Template extraction**: YScope CLP-inspired pattern detection for log message templates
- **Variable classification**: Detecting timestamps, identifiers, network addresses, numerical values
- **Columnar encoding**: Type-specific compression with delta, dictionary, and pattern recognition
- **Smart row ordering**: Grouping by template and variable similarity for maximum compression
- **Order preservation dropping**: Trading ordering for compression when appropriate

**Planned Results:**
- **10-20x** compression with basic template extraction
- **25-50x** compression with advanced variable encoding
- **50-100x** compression with smart ordering optimization

## 🎖️ Current Achievements

### Metrics Storage Evolution ✅ **COMPLETE**
- **79.7x compression** vs NDJSON baseline with enhanced algorithms
- **3.19 bytes per data point** using advanced pattern detection
- **24.2% improvement** over standard compression techniques
- **Perfect data fidelity** with comprehensive verification
- **Real dataset support** using Westermo monitoring data
- **Multi-resolution storage** with intelligent downsampling
- **7 phases implemented**: From NDJSON baseline to advanced downsampling

**Advanced Features:**
- **10+ pattern detection algorithms** (near-constant, power-of-2, exponential, periodic)
- **Enhanced XOR compression** with bit-level optimization
- **Aggressive metadata compression** with dictionary encoding  
- **Maximum zstd compression** (level 22) for ultimate efficiency
- **Three dataset sizes** (small/big/huge) up to 100M data points

### Traces Storage Evolution ✅ **COMPLETE**
- **22.21x compression** vs NDJSON baseline at Phase 4
- **100% data integrity** maintained across all phases
- **Sub-second processing** for complete pipeline
- **Dual optimization paths**: Relationship-focused vs Analytics-focused
- **5 phases implemented**: From NDJSON to advanced columnar storage

**Technical Achievements:**
- **Service topology optimization** with 74x compression for service names
- **Parent-child delta encoding** for span relationships
- **Columnar storage** optimized for analytical queries
- **Microservices simulation** with 12+ realistic services
- **Three dataset sizes** (small/medium/big) up to 10K traces

### Logs Storage Evolution 🔄 **IN PROGRESS**
- **6 phases implemented** (out of 6 planned)
- **Template extraction** using YScope CLP-inspired algorithms
- **Variable classification** for timestamps, identifiers, network data
- **Smart ordering** for maximum compression efficiency
- **Ready for testing and validation**

**Implementation Status:**
- ✅ Phase 0: Data generation
- ✅ Phase 1: Plain text baseline
- ✅ Phase 2: Zstd compression
- ✅ Phase 3: Template extraction
- ✅ Phase 4: Advanced variable encoding
- ✅ Phase 5: Smart row ordering
- ✅ Phase 6: Drop order preservation

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
- **Metrics**: Temporal correlation and value similarity enable massive compression gains (79.7x achieved)
- **Traces**: Relationship structures and service topology patterns enable excellent compression (22.21x achieved)
- **Logs**: Template extraction and variable classification show promise for high compression ratios (implementation complete, testing in progress)

## Documentation

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
