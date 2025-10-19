# Phase 1: NDJSON Storage - Characteristics and Analysis

Phase 1 establishes the **baseline** with human-readable NDJSON format, demonstrating the inefficiencies that drive the need for optimization.

## 📋 Format Overview

**NDJSON (Newline Delimited JSON)** stores each metrics data point as a separate JSON object on its own line:

```json
{"timestamp": 1760860006, "metric_name": "cpu_usage_percent", "value": 45.2, "labels": {"host": "server-a", "region": "us-west-2", "environment": "prod"}}
{"timestamp": 1760860021, "metric_name": "cpu_usage_percent", "value": 47.1, "labels": {"host": "server-a", "region": "us-west-2", "environment": "prod"}}
{"timestamp": 1760860036, "metric_name": "memory_usage_percent", "value": 73.4, "labels": {"host": "server-b", "region": "us-west-2", "environment": "prod"}}
```

## 🔍 Inefficiency Analysis

### Key Repetition Problem
With 500,000 data points, the redundancy is massive:

```
Key Repetitions:
- 'labels': 500,000 times
- 'labels.environment': 500,000 times  
- 'labels.host': 500,000 times
- 'labels.region': 500,000 times
- 'labels.source': 500,000 times
- 'metric_name': 500,000 times
- 'timestamp': 500,000 times
- 'value': 500,000 times

Most Repeated Label Values:
- 'host=unknown': 500,000 times
- 'region=us-west-2': 500,000 times  
- 'environment=test': 500,000 times
- 'source=real_dataset': 500,000 times

Estimated redundant key bytes: ~41,000,000 bytes
```

### Text Encoding Overhead
- **Numbers as text**: `"45.2"` instead of binary float (8 bytes vs 4+ characters)
- **JSON syntax**: `{"`, `":`, `",`, `}` characters add ~20% overhead
- **String quotes**: Every string value wrapped in quotes
- **No type preservation**: All values become strings requiring parsing

## 📊 Storage Characteristics

```
📊 NDJSON Storage Results:
File size: 84,761,228 bytes (80.83 MB)
Bytes per data point: 169.52
Average JSON size per point: ~168 bytes
```

**Size Breakdown:**
- **JSON syntax overhead**: ~25,000,000 bytes (30%)
- **Key repetition**: ~41,000,000 bytes (48%) 
- **Actual data**: ~18,000,000 bytes (22%)

## 💡 Format Characteristics

### ✅ Advantages (Pros)

**Human Readable**
- Can be viewed and edited in any text editor
- Easy to understand data structure at a glance
- Debugging is straightforward

**Tool Ecosystem**
- Standard Unix tools work: `grep`, `awk`, `sed`, `jq`
- Easy to process with scripts in any language
- No custom parsers or libraries required

**Streamable and Appendable**
- Can write data points one at a time
- No need to rewrite entire file when adding data
- Works well with log rotation and streaming pipelines

**Standards Compliant**
- JSON is a widely adopted, standardized format
- NDJSON follows established conventions
- Maximum compatibility across systems

### ❌ Disadvantages (Cons)

**Massive Redundancy**
- Keys repeated in every record (41MB of redundant keys)
- Label values duplicated across similar metrics
- No structural optimization possible

**Inefficient Number Representation**
- Floating point numbers stored as text
- Integers lose type information
- Timestamps take 10 characters instead of 8 bytes

**No Compression**
- Raw text with no built-in compression
- Repeated data stored verbatim
- Large storage footprint

**Performance Impact**
- Slow parsing (JSON text → data structures)
- High memory usage during processing
- Network transfer costs for large datasets

## 🎯 Real-World Usage

NDJSON is commonly used for:
- **Development and debugging** where human readability is crucial
- **Log aggregation systems** (ELK stack, Splunk)
- **Data streaming pipelines** where simplicity matters
- **Configuration and setup files** for metrics systems
- **Temporary data exchange** between different systems

## 🔄 Why We Need to Evolve

The NDJSON baseline demonstrates key problems that subsequent phases address:

1. **Redundancy** → Phases 4-5 eliminate repeated keys/metadata
2. **Text encoding** → Phase 2 introduces binary serialization  
3. **No compression** → Phase 3+ add compression layers
4. **Type inefficiency** → Phase 2+ preserve native data types
5. **Size overhead** → All subsequent phases reduce storage footprint

This baseline establishes that while NDJSON is excellent for human interaction, production metrics storage requires structural optimization for cost-effective scale.

The **169.52 bytes per data point** baseline gives us a target to beat through the remaining phases of the evolution.