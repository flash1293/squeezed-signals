# Log Data Compression Evolution

This directory demonstrates advanced log compression techniques inspired by the YScope CLP (Compressed Log Processor) algorithm. The approach focuses on exploiting the structured yet variable nature of log data.

## Core Concept: Template + Variable Separation

The fundamental insight is that log messages are not random text but follow highly repetitive patterns:

```
Original logs:
INFO: User 'alice' logged in from IP 192.168.1.10 at 2023-10-20T14:30:15Z
INFO: User 'bob' logged in from IP 10.0.0.5 at 2023-10-20T14:31:22Z
ERROR: Failed login attempt for user 'eve' from IP 172.16.1.1

Becomes:
Templates:
  T1: "INFO: User '' logged in from IP  at "
  T2: "ERROR: Failed login attempt for user '' from IP "

Variables (columnar):
  template_ids: [T1, T1, T2]
  usernames: ['alice', 'bob', 'eve']
  ip_addresses: ['192.168.1.10', '10.0.0.5', '172.16.1.1']
  timestamps: ['2023-10-20T14:30:15Z', '2023-10-20T14:31:22Z', null]
```

## Implementation Phases

1. **Phase 0**: Generate realistic log data
2. **Phase 1**: Plain text baseline
3. **Phase 2**: Standard zstd compression
4. **Phase 3**: Core CLP - template extraction + columnar variables
5. **Phase 4**: Advanced variable encoding (delta, dictionary, pattern recognition)
6. **Phase 5**: Smart log ordering for maximum compression efficiency

## Key Algorithms

### Template Discovery
- Parse log lines to identify static vs. dynamic parts
- Use regex-like patterns to detect variable types
- Build template dictionary with placeholder markers

### Variable Classification
- **Timestamps**: ISO8601, epoch, relative times
- **Identifiers**: UUIDs, session IDs, user IDs
- **Network**: IP addresses, URLs, ports
- **Numerical**: Integers, floats, measurements
- **Text**: Free-form strings, paths, messages

### Columnar Encoding
- Group variables by type and template
- Apply type-specific compression (delta, dictionary, pattern)
- Store in columnar format for efficient access

### Smart Ordering
- Group logs by template type for locality
- Sort by variable similarity within template groups
- Cluster logs sharing correlation IDs
- Maintain semantic relationships while maximizing compression

## Expected Results
- **10-20x** compression with basic template extraction
- **25-50x** compression with advanced variable encoding
- **50-100x** compression with smart ordering optimization
- **Sub-second** search capabilities on compressed data
- **Perfect reconstruction** of original log messages

## Real-World Applications
- Reducing log storage costs by 95%+
- Enabling faster log searches and analytics
- Real-time log compression for streaming data
- Optimizing log transmission and archival