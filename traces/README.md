# Distributed Traces Storage Evolution

This directory contains the implementation for optimizing distributed tracing data storage. The approach demonstrates progressive optimization techniques specific to trace data characteristics including span relationships, service topology, and temporal correlation patterns.

## Current Status

**✅ Phases 0-4 Implemented** - Advanced relationship compression complete!

### Implemented Phases

- ✅ **Phase 0**: Generate realistic distributed trace data (100-10K traces)
- ✅ **Phase 1**: NDJSON baseline storage (1.0x baseline)
- ✅ **Phase 2**: CBOR binary encoding (**1.80x compression**)
- ✅ **Phase 3**: CBOR + Zstandard compression (**10.72x compression**)
- ✅ **Phase 4**: Span relationship compression (**22.21x compression**)

### Current Results
#### Small Dataset (100 traces, 287 spans)
- **19.10x compression** vs NDJSON baseline
- **100% data integrity** maintained across all phases
- **Sub-second processing** for complete pipeline

#### Medium Dataset (1,000 traces, 2,811 spans)  
- **22.21x compression** vs NDJSON baseline
- **Better scaling** with larger datasets
- **Advanced relationship patterns** detected and compressed

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

5. **Phase 5**: Columnar trace storage (target: 30-50x)
6. **Phase 6**: Advanced trace pattern detection (target: 60-100x)
7. **Phase 7**: Multi-resolution trace storage (target: 100-200x)
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
| 0 | Raw JSON | 144,331 | 1.00x | Original data |
| 1 | NDJSON | 144,421 | 1.00x | Baseline format |
| 2 | CBOR | 80,529 | **1.79x** | Binary encoding |
| 3 | CBOR+Zstd | 13,794 | **10.47x** | Dictionary compression |
| 4 | Relationships | 7,563 | **19.10x** | Topology + delta encoding |

### Medium Dataset (1,000 traces)
| Phase | Format | Size (bytes) | Compression | Features |
|-------|---------|-------------|-------------|----------|
| 1 | NDJSON | 1,411,286 | 1.00x | Baseline format |
| 2 | CBOR | 786,141 | **1.80x** | Binary encoding |
| 3 | CBOR+Zstd | 131,651 | **10.72x** | Dictionary compression |
| 4 | Relationships | 63,549 | **22.21x** | Service topology optimization |

**Achievement**: **22x compression** with complete relationship preservation!

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

### Key Achievements

- **22x compression** achieved while maintaining 100% data integrity
- **Complete trace reconstruction** capability preserved
- **Microservices pattern detection** enabling topology-aware compression
- **Scalable architecture** showing improved compression ratios with larger datasets
- **Production-ready techniques** applicable to real-world distributed tracing systems