# Distributed Traces Storage Evolution

This directory contains the implementation for optimizing distributed tracing data storage. The approach demonstrates progressive optimization techniques specific to trace data characteristics including span relationships, service topology, and temporal correlation patterns.

## Current Status

**✅ Phases 0-5 Implemented** - Advanced columnar storage complete!

### Implemented Phases

- ✅ **Phase 0**: Generate realistic distributed trace data (100-10K traces)
- ✅ **Phase 1**: NDJSON baseline storage (1.0x baseline)
- ✅ **Phase 2**: CBOR binary encoding (**1.80x compression**)
- ✅ **Phase 3**: CBOR + Zstandard compression (**10.44x compression**)
- ✅ **Phase 4**: Span relationship compression (**18.34x compression**)
- ✅ **Phase 5**: Columnar trace storage (**14.90x compression**)

### Current Results
#### Small Dataset (100 traces, 251 spans)
- **18.34x compression** achieved at Phase 4 (optimal for small datasets)
- **Columnar storage** trades off to 14.90x for analytical capabilities
- **100% data integrity** maintained across all phases
- **Sub-second processing** for complete pipeline

#### Medium Dataset (1,000 traces, 2,811 spans)  
- **22.21x compression** vs NDJSON baseline at Phase 4
- **Columnar storage** provides 17.82x with better query performance
- **Better scaling** with larger datasets showing improved compression ratios
- **Advanced relationship patterns** and service topology optimization

## Microservices Architecture Simulated

The trace generator creates realistic distributed system patterns:

```
api-gateway → user-service → auth-service → auth-db
            → order-service → payment-service → bank-api
                           → fraud-detection → ml-model-service  
                           → inventory-service → inventory-db
                           → order-db
```

## Planned Next Phases

6. **Phase 6**: Advanced trace pattern detection (target: 30-60x)
7. **Phase 7**: Multi-resolution trace storage (target: 60-150x)
8. **Phase 8**: Intelligent trace sampling & compression (target: 200-500x)

## Key Technical Features

- **Realistic Data**: Complex microservices with fan-out patterns, error propagation
- **Span Relationships**: Parent-child relationships with realistic timing
- **Service Topology**: 12+ services with dependencies and latency distributions
- **Error Simulation**: Realistic error rates and propagation patterns

## Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Generate and process all phases
python main.py --size small

# Run specific phase
python main.py --phase 01 --size medium

# Available sizes: small (100 traces), medium (1K), big (10K)
python main.py --size big
```

## Performance Results

### Small Dataset (100 traces)
| Phase | Format | Size (bytes) | Compression | Features |
|-------|---------|-------------|-------------|----------|
| 0 | Raw JSON | 126,401 | 1.00x | Original data |
| 1 | NDJSON | 125,834 | 1.00x | Baseline format |
| 2 | CBOR | 69,989 | **1.80x** | Binary encoding |
| 3 | CBOR+Zstd | 12,053 | **10.44x** | Dictionary compression |
| 4 | Relationships | 6,863 | **18.34x** | Topology + delta encoding |
| 5 | Columnar | 8,446 | **14.90x** | Column-oriented + analytics |

### Medium Dataset (1,000 traces)  
| Phase | Format | Size (bytes) | Compression | Features |
|-------|---------|-------------|-------------|----------|
| 1 | NDJSON | 1,411,286 | 1.00x | Baseline format |
| 2 | CBOR | 786,141 | **1.80x** | Binary encoding |
| 3 | CBOR+Zstd | 131,651 | **10.72x** | Dictionary compression |
| 4 | Relationships | 63,549 | **22.21x** | Service topology optimization |
| 5 | Columnar | 79,193 | **17.82x** | Analytical query optimization |

**Achievement**: **18-22x compression** with multiple optimization strategies!

## Technical Implementation

### Trace Data Model

Each trace contains multiple spans with realistic microservices characteristics:

```python
@dataclass
class Span:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    service_name: str
    start_time: int  # nanoseconds
    end_time: int    # nanoseconds
    tags: Dict[str, Any]
    logs: List[Dict[str, Any]]
    status_code: int  # 0=OK, 1=ERROR
```

### Compression Strategies Implemented

1. **CBOR Binary Encoding**: Compact binary representation with field name optimization
2. **Field Optimization**: Shortened field names for space efficiency
3. **Data Type Optimization**: Integer timestamps, status code simplification

### Compression Techniques Implemented

1. **CBOR Binary Encoding**: Compact binary representation with optimized field names
2. **Zstandard Dictionary Compression**: Custom dictionaries for service/operation patterns  
3. **Service Topology Mapping**: Deduplicated service and operation name references
4. **Parent-Child Delta Encoding**: Efficient span relationship compression
5. **Timestamp Delta Compression**: Time-based deltas within trace boundaries
6. **Tag/Log Optimization**: Key mapping and value deduplication
7. **MessagePack + Zstd**: Efficient serialization with high-level compression
8. **Columnar Storage**: Column-oriented layout with column-specific algorithms
9. **Advanced Column Strategies**: Dictionary, delta, run-length, and power-of-2 encoding

### Key Achievements

- **22x compression** achieved at Phase 4 while maintaining 100% data integrity
- **Dual optimization paths**: Relationship-focused (Phase 4) vs Analytics-focused (Phase 5)
- **Complete trace reconstruction** capability preserved across all phases
- **Microservices pattern detection** enabling topology-aware compression
- **Column-specific algorithms** providing 74x compression for service names
- **Scalable architecture** showing improved compression ratios with larger datasets
- **Production-ready techniques** applicable to real-world distributed tracing systems

### Trade-off Analysis

**Phase 4 (Relationship Compression)**: Optimal for storage efficiency and trace reconstruction
**Phase 5 (Columnar Storage)**: Better for analytical queries and business intelligence workloads

Both approaches maintain complete data fidelity while optimizing for different access patterns.