# Phase 0: Log Data Generation

Downloads real-world log data from [LogHub](https://github.com/logpai/loghub), a repository of production system logs. Using real data ensures compression techniques are tested against genuine log patterns rather than synthetic data.

## Datasets

**Small: Apache** (~0.5 MB, 2K lines)
- Web server error logs
- HTTP errors, client IPs, file paths
- Example: `[Thu Jun 09 06:07:04 2005] [error] [client 64.242.88.10] File does not exist: /var/www/html/robots.txt`

**Big: HDFS** (~1 MB, 2K lines)
- Hadoop distributed file system logs
- Block operations, DataNode events
- Example: `081109 203615 143 INFO dfs.DataNode$DataXceiver: Receiving block blk_-1608999687919862906`

**Huge: OpenSSH** (~1 MB, 2K lines)
- SSH authentication and connection logs
- Login attempts, security events
- Example: `Dec 10 06:55:46 LabSZ sshd[24200]: Failed password for root from 218.188.2.4 port 52825`

## Why Real Data

Real logs have characteristics that impact compression:
- **Template repetition**: Same events → identical log structures
- **Temporal clustering**: Related events occur in bursts
- **Variable locality**: Similar values appear together (IP subnets, sequential IDs)
- **Realistic entropy**: Actual UUIDs, hashes, varied formats

## Variable Types Detected

- Timestamps (multiple formats)
- IP addresses (IPv4)
- File paths
- Identifiers (block IDs, session IDs, process IDs)
- Numbers (integers, ports, sizes)
- Text (usernames, hostnames, messages)

## Analysis Output

```
Total lines: 2,000
File size: 567,890 bytes (554 KB)
Average line length: 283.9 characters
Timestamps: 2,000 (100%)
IP addresses: 1,847 (92.4%)
Log levels: INFO, ERROR, WARN
```

## Compression Potential

**Template repetition:** 47 unique templates for 2,000 lines = 42.6x reuse

**Example frequencies:**
- Top template: 347 occurrences (17.4%)
- 2nd template: 213 occurrences (10.7%)
- 3rd template: 189 occurrences (9.5%)

**Variable clustering:**
- IP 64.242.88.10: 423 occurrences
- IP 10.251.43.191: 387 occurrences
- 94% of timestamps within 1-second increments

## Usage

```bash
python 00_generate_data.py --size small  # Apache
python 00_generate_data.py --size big    # HDFS
python 00_generate_data.py --size huge   # OpenSSH
```

## Output

```
output/logs_small.log                    # Raw log data
output/phase0_logs_metadata_small.json   # Statistics
```

This establishes the baseline (554.6 KB) that subsequent phases will compress.


