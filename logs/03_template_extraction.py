#!/usr/bin/env python3
"""
Phase 3: Template Extraction

This phase implements the core of the CLP (Compressed Log Processing) approach
by separating log lines into templates and variables. Templates capture the
static structure while variables store the dynamic content.

This is inspired by YScope's CLP algorithm which achieves 100x+ compression
by exploiting the repetitive structure in log data.

Expected result: ~40-60x compression (better than Zstd's 29x)
"""

import json
import time
import re
import zstandard as zstd
from pathlib import Path
from typing import Dict, List, Any, Tuple, Set
from collections import defaultdict
import pickle


class LogTemplateExtractor:
    """
    Extracts templates from log lines using pattern recognition and stores
    variables in optimized columnar format for maximum compression.
    
    The algorithm:
    1. Extract templates with typed placeholders
    2. Store variables in type-specific columns  
    3. Use template structure to reconstruct without heavy indices
    4. Apply delta encoding and compression per column type
    """
    
    def __init__(self):
        self.templates: Dict[str, int] = {}  # template -> template_id
        self.template_id_counter = 0
        self.variable_patterns = [
            # More specific patterns first to avoid overlaps
            (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '<IP>'),  # IP addresses
            (r'\b\w{8}-\w{4}-\w{4}-\w{4}-\w{12}\b', '<UUID>'),  # UUIDs
            (r'\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', '<TIMESTAMP>'),  # ISO timestamps
            (r'\[\w+\s+\w+\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+\d{4}\]', '<BRACKET_TIME>'),  # [Thu Jun 09 06:07:04 2005]
            (r'/[^\s\]]+', '<PATH>'),                   # File paths (not ending with ])
            (r'\b[0-9a-f]{8,}\b', '<HEX>'),            # Hex strings
            (r'\b\d+\b', '<NUM>'),                     # Numbers (last to avoid conflicts)
        ]
        
        # Optimized columnar storage
        self.variable_columns = {
            'IP': [],           # IP addresses
            'UUID': [],         # UUIDs  
            'TIMESTAMP': [],    # ISO timestamps
            'BRACKET_TIME': [], # Bracket timestamps
            'PATH': [],         # File paths
            'HEX': [],          # Hex strings
            'NUM': [],          # Numbers (stored as strings for now, could be int-encoded later)
        }
        
        # Mapping structures - optimized to reduce overhead
        self.line_to_template: List[int] = []
        self.line_variable_counts: List[List[int]] = []  # [IP_count, UUID_count, ...] per line
        
        # Template analysis for reconstruction
        self.template_variable_patterns: Dict[int, List[str]] = {}  # template_id -> ordered placeholder types
        
        self.extracted_data = {
            'templates': [],
            'variable_columns': {},
            'line_to_template': [],
            'line_variable_counts': [],
            'template_variable_patterns': {},
            'total_lines': 0,
            'unique_templates': 0
        }
    
    def extract_template(self, log_line: str) -> Tuple[str, List[Tuple[str, str]]]:
        """
        Extract template and typed variables from a log line.
        
        Returns:
            (template, typed_variables) where template has placeholders and
            typed_variables contains (type, value) tuples in order of appearance
        """
        original_line = log_line.strip()
        
        # Find all matches first, then sort by position
        replacements = []
        for pattern, placeholder in self.variable_patterns:
            for match in re.finditer(pattern, original_line):
                replacements.append((match.start(), match.end(), match.group(), placeholder))
        
        # Sort by position (earliest first) and remove overlaps
        replacements.sort(key=lambda x: x[0])
        
        # Remove overlapping matches (keep first occurrence)
        filtered_replacements = []
        last_end = -1
        for start, end, value, placeholder in replacements:
            if start >= last_end:  # No overlap
                filtered_replacements.append((start, end, value, placeholder))
                last_end = end
        
        # Collect typed variables in left-to-right order
        typed_variables = []
        for start, end, value, placeholder in filtered_replacements:
            var_type = placeholder.strip('<>')  # Remove < >
            typed_variables.append((var_type, value))
        
        # Apply replacements from right to left to maintain positions in template
        template = original_line
        for start, end, value, placeholder in reversed(filtered_replacements):
            template = template[:start] + placeholder + template[end:]
        
        return template, typed_variables
    
    def get_template_id(self, template: str) -> int:
        """Get or create a template ID"""
        if template not in self.templates:
            self.templates[template] = self.template_id_counter
            self.template_id_counter += 1
        return self.templates[template]
    
    def process_log_lines(self, log_lines: List[str]) -> Dict[str, Any]:
        """Process all log lines and extract templates/variables into optimized columnar storage"""
        print(f"Extracting templates from {len(log_lines):,} log lines...")
        
        template_frequencies = defaultdict(int)
        
        # Track current position in each column for efficient appending
        column_positions = {col_type: 0 for col_type in self.variable_columns.keys()}
        
        for line_num, line in enumerate(log_lines):
            if line_num % 1000 == 0 and line_num > 0:
                print(f"  Processed {line_num:,} lines...")
            
            template, typed_variables = self.extract_template(line)
            template_id = self.get_template_id(template)
            
            template_frequencies[template] += 1
            
            # Store template mapping
            self.line_to_template.append(template_id)
            
            # Store template variable pattern for efficient reconstruction
            if template_id not in self.template_variable_patterns:
                # Extract placeholder order from template
                placeholders = []
                import re
                for match in re.finditer(r'<(\w+)>', template):
                    placeholders.append(match.group(1))
                self.template_variable_patterns[template_id] = placeholders
            
            # Count variables by type for this line
            line_var_counts = [0] * len(self.variable_columns)
            col_type_to_index = {col_type: i for i, col_type in enumerate(self.variable_columns.keys())}
            
            # Add variables to columns and count them
            for var_type, value in typed_variables:
                self.variable_columns[var_type].append(value)
                line_var_counts[col_type_to_index[var_type]] += 1
            
            self.line_variable_counts.append(line_var_counts)
        
        # Create final template list (ordered by ID)
        self.extracted_data['templates'] = [''] * len(self.templates)
        for template, template_id in self.templates.items():
            self.extracted_data['templates'][template_id] = template
        
        # Store optimized columnar data
        self.extracted_data['variable_columns'] = self.variable_columns
        self.extracted_data['line_to_template'] = self.line_to_template
        self.extracted_data['line_variable_counts'] = self.line_variable_counts
        self.extracted_data['template_variable_patterns'] = self.template_variable_patterns
        
        self.extracted_data['total_lines'] = len(log_lines)
        self.extracted_data['unique_templates'] = len(self.templates)
        
        # Calculate template statistics
        template_stats = []
        for template, freq in sorted(template_frequencies.items(), key=lambda x: x[1], reverse=True):
            template_id = self.templates[template]
            template_stats.append({
                'template_id': template_id,
                'template': template,
                'frequency': freq,
                'percentage': (freq / len(log_lines)) * 100
            })
        
        self.extracted_data['template_stats'] = template_stats[:20]  # Top 20 templates
        
        print(f"✅ Template extraction completed:")
        print(f"   Total lines: {len(log_lines):,}")
        print(f"   Unique templates: {len(self.templates):,}")
        print(f"   Compression ratio: {len(log_lines) / len(self.templates):.2f}x")
        
        return self.extracted_data
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Calculate storage statistics for optimized columnar storage"""
        
        # Calculate sizes for templates
        templates_size = sum(len(template.encode('utf-8')) for template in self.extracted_data['templates'])
        
        # Calculate sizes for template ID mappings
        template_ids_size = len(self.extracted_data['line_to_template']) * 4  # 4 bytes per int
        
        # Calculate sizes for variable columns
        variable_columns_size = {}
        total_variables_size = 0
        
        for col_type, values in self.extracted_data['variable_columns'].items():
            if values:
                # Size of values in this column
                column_size = sum(len(str(value).encode('utf-8')) for value in values)
                variable_columns_size[col_type] = {
                    'count': len(values),
                    'size_bytes': column_size
                }
                total_variables_size += column_size
            else:
                variable_columns_size[col_type] = {'count': 0, 'size_bytes': 0}
        
        # Calculate size for optimized variable counts (much smaller than indices)
        variable_counts_size = 0
        for line_counts in self.extracted_data['line_variable_counts']:
            # Each count is a small integer - estimate 1 byte per count, 7 types = 7 bytes per line
            variable_counts_size += len(line_counts) * 1
        
        # Template patterns size
        template_patterns_size = sum(
            sum(len(pattern_type.encode('utf-8')) for pattern_type in patterns)
            for patterns in self.extracted_data['template_variable_patterns'].values()
        )
        
        total_compressed_size = templates_size + template_ids_size + total_variables_size + variable_counts_size + template_patterns_size
        
        return {
            'templates_size_bytes': templates_size,
            'template_ids_size_bytes': template_ids_size,
            'variable_columns_size_bytes': total_variables_size,
            'variable_columns_breakdown': variable_columns_size,
            'variable_counts_size_bytes': variable_counts_size,
            'template_patterns_size_bytes': template_patterns_size,
            'total_compressed_size_bytes': total_compressed_size,
            'unique_templates': self.extracted_data['unique_templates'],
            'total_lines': self.extracted_data['total_lines'],
            'template_reuse_ratio': self.extracted_data['total_lines'] / self.extracted_data['unique_templates']
        }
    
    def save_to_file(self, output_path: Path) -> Dict[str, Any]:
        """Save the extracted templates and variables with Zstd Level 22 compression"""
        
        # Serialize data to bytes first
        data_bytes = pickle.dumps(self.extracted_data, protocol=pickle.HIGHEST_PROTOCOL)
        uncompressed_size = len(data_bytes)
        
        # Apply Zstd Level 22 compression on top of template extraction
        compressor = zstd.ZstdCompressor(level=22)
        compressed_data = compressor.compress(data_bytes)
        
        # Save compressed data
        with open(output_path, 'wb') as f:
            f.write(compressed_data)
        
        file_size = output_path.stat().st_size
        storage_stats = self.get_storage_stats()
        
        return {
            'file_size_bytes': file_size,
            'uncompressed_size_bytes': uncompressed_size,
            'zstd_compression_ratio': uncompressed_size / file_size,
            'storage_stats': storage_stats,
            'extraction_data': self.extracted_data
        }
    
    def load_from_file(self, input_path: Path) -> Dict[str, Any]:
        """Load extracted data from file (with Zstd decompression)"""
        
        # Read compressed data
        with open(input_path, 'rb') as f:
            compressed_data = f.read()
        
        # Decompress with Zstd
        decompressor = zstd.ZstdDecompressor()
        decompressed_data = decompressor.decompress(compressed_data)
        
        # Deserialize from bytes
        self.extracted_data = pickle.loads(decompressed_data)
        return self.extracted_data
    
    def reconstruct_logs(self, input_path: Path) -> List[str]:
        """Reconstruct original log lines from templates and optimized columnar variables"""
        print("Reconstructing log lines from templates and optimized columnar variables...")
        
        extracted_data = self.load_from_file(input_path)
        reconstructed_lines = []
        
        # Track current position in each column for reconstruction
        column_positions = {col_type: 0 for col_type in extracted_data['variable_columns'].keys()}
        col_type_to_index = {col_type: i for i, col_type in enumerate(extracted_data['variable_columns'].keys())}
        
        for line_idx in range(extracted_data['total_lines']):
            template_id = extracted_data['line_to_template'][line_idx]
            template = extracted_data['templates'][template_id]
            line_var_counts = extracted_data['line_variable_counts'][line_idx]
            template_pattern = extracted_data['template_variable_patterns'][template_id]
            
            # Reconstruct by replacing placeholders with variables from columns
            reconstructed = template
            
            # Process variables in the order they appear in the template
            var_used_counts = {col_type: 0 for col_type in extracted_data['variable_columns'].keys()}
            
            for placeholder_type in template_pattern:
                placeholder = f'<{placeholder_type}>'
                if placeholder in reconstructed:
                    # Get the next value of this type for this line
                    current_pos = column_positions[placeholder_type]
                    
                    # Find the value: we need to skip to the right position for this line
                    # Based on how many of this type we've used in previous lines
                    value = extracted_data['variable_columns'][placeholder_type][current_pos]
                    
                    # Replace the first occurrence of this placeholder
                    reconstructed = reconstructed.replace(placeholder, value, 1)
                    
                    # Track that we used one of this type
                    var_used_counts[placeholder_type] += 1
                    column_positions[placeholder_type] += 1
            
            reconstructed_lines.append(reconstructed)
        
        print(f"✅ Reconstructed {len(reconstructed_lines):,} log lines")
        return reconstructed_lines


def process_log_file(input_file: Path, output_file: Path, metadata_file: Path) -> Dict[str, Any]:
    """Process a log file with template extraction"""
    print(f"Processing {input_file.name} with template extraction...")
    
    start_time = time.time()
    
    # Read log lines
    print(f"Reading log file...")
    log_lines = []
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if line:  # Skip empty lines
                log_lines.append(line)
    
    print(f"Loaded {len(log_lines):,} log lines")
    
    # Extract templates
    extractor = LogTemplateExtractor()
    extraction_data = extractor.process_log_lines(log_lines)
    
    # Save extracted data
    save_result = extractor.save_to_file(output_file)
    
    # Calculate original size
    original_size = sum(len(line.encode('utf-8')) + 1 for line in log_lines)  # +1 for newline
    
    processing_time = time.time() - start_time
    compression_ratio = original_size / save_result['file_size_bytes']
    
    # Create metadata with enhanced compression details
    metadata = {
        'phase': 'Phase 3 - Template Extraction + Zstd Level 22',
        'storage_format': 'template_variables_pickle_zstd22',
        'file_size_bytes': save_result['file_size_bytes'],
        'original_size_bytes': original_size,
        'uncompressed_pickle_size_bytes': save_result.get('uncompressed_size_bytes', save_result['file_size_bytes']),
        'overall_compression_ratio': compression_ratio,
        'template_structure_ratio': extraction_data['total_lines'] / extraction_data['unique_templates'],
        'zstd_compression_ratio': save_result.get('zstd_compression_ratio', 1.0),
        'processing_time_seconds': processing_time,
        'lines_processed': len(log_lines),
        'unique_templates': extraction_data['unique_templates'],
        'template_reuse_ratio': extraction_data['total_lines'] / extraction_data['unique_templates'],
        'storage_breakdown': save_result['storage_stats'],
        'top_templates': extraction_data['template_stats'][:10]  # Top 10 for metadata
    }
    
    # Save metadata
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"  Completed in {processing_time:.2f} seconds")
    print(f"  Lines processed: {len(log_lines):,}")
    print(f"  Unique templates: {extraction_data['unique_templates']:,}")
    print(f"  Template reuse: {extraction_data['total_lines'] / extraction_data['unique_templates']:.2f}x")
    print(f"  Original size: {original_size:,} bytes")
    
    # Show compression breakdown
    if 'uncompressed_size_bytes' in save_result:
        print(f"  Template extraction size: {save_result['uncompressed_size_bytes']:,} bytes")
        print(f"  After Zstd Level 22: {save_result['file_size_bytes']:,} bytes")
        print(f"  Template structure compression: {original_size / save_result['uncompressed_size_bytes']:.2f}x")
        print(f"  Zstd compression: {save_result['zstd_compression_ratio']:.2f}x")
    else:
        print(f"  Compressed size: {save_result['file_size_bytes']:,} bytes")
    
    print(f"  Overall compression ratio: {compression_ratio:.2f}x")
    
    return metadata


def verify_reconstruction(input_file: Path, extracted_file: Path) -> bool:
    """Verify that we can perfectly reconstruct the original logs"""
    print("Verifying template extraction integrity...")
    
    # Read original lines
    original_lines = []
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if line:
                original_lines.append(line)
    
    # Reconstruct lines
    extractor = LogTemplateExtractor()
    reconstructed_lines = extractor.reconstruct_logs(extracted_file)
    
    # Verify
    if len(original_lines) != len(reconstructed_lines):
        print(f"❌ Line count mismatch: {len(original_lines)} != {len(reconstructed_lines)}")
        return False
    
    mismatches = 0
    for i, (orig, recon) in enumerate(zip(original_lines, reconstructed_lines)):
        if orig != recon:
            mismatches += 1
            if mismatches <= 5:  # Show first 5 mismatches
                print(f"❌ Line {i+1} mismatch:")
                print(f"   Original:     {repr(orig)}")
                print(f"   Reconstructed: {repr(recon)}")
    
    if mismatches == 0:
        print(f"✅ Perfect reconstruction: all {len(original_lines):,} lines match")
        return True
    else:
        print(f"❌ Reconstruction failed: {mismatches} mismatches out of {len(original_lines)} lines")
        return False


def main():
    """Main function to process logs with phase 3 template extraction"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Phase 3: Template Extraction')
    parser.add_argument('--size', choices=['small', 'big', 'huge'], default='small',
                       help='Dataset size to process (default: small)')
    parser.add_argument('--verify', action='store_true',
                       help='Verify reconstruction integrity')
    
    args = parser.parse_args()
    
    # Setup paths
    input_file = Path(f'output/logs_{args.size}.log')
    output_file = Path(f'output/phase3_logs_{args.size}.pkl')
    metadata_file = Path(f'output/phase3_logs_metadata_{args.size}.json')
    
    # Ensure output directory exists
    output_file.parent.mkdir(exist_ok=True)
    
    # Check input file exists
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        print(f"   Run Phase 0 first: python 00_generate_data.py --size {args.size}")
        return 1
    
    print("=" * 60)
    print(f"Phase 3: Template Extraction ({args.size})")
    print("=" * 60)
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    
    try:
        # Process the file
        metadata = process_log_file(input_file, output_file, metadata_file)
        
        # Verify reconstruction if requested
        if args.verify:
            print("\n" + "=" * 60)
            if not verify_reconstruction(input_file, output_file):
                print("❌ Reconstruction verification failed!")
                return 1
        
        print("\n📊 Phase 3 Template Extraction + Zstd Results:")
        print(f"  Lines processed: {metadata['lines_processed']:,}")
        print(f"  Unique templates: {metadata['unique_templates']:,}")
        print(f"  Template reuse: {metadata['template_reuse_ratio']:.2f}x per template")
        print(f"  Original size: {metadata['original_size_bytes']:,} bytes ({metadata['original_size_bytes']/1024:.1f} KB)")
        
        # Show compression breakdown if available
        if 'uncompressed_pickle_size_bytes' in metadata and metadata['uncompressed_pickle_size_bytes'] != metadata['file_size_bytes']:
            print(f"  Template extraction size: {metadata['uncompressed_pickle_size_bytes']:,} bytes ({metadata['uncompressed_pickle_size_bytes']/1024:.1f} KB)")
            print(f"  After Zstd Level 22: {metadata['file_size_bytes']:,} bytes ({metadata['file_size_bytes']/1024:.1f} KB)")
            print(f"  Template structure compression: {metadata['original_size_bytes'] / metadata['uncompressed_pickle_size_bytes']:.2f}x")
            print(f"  Zstd compression: {metadata.get('zstd_compression_ratio', 1.0):.2f}x")
        else:
            print(f"  Compressed size: {metadata['file_size_bytes']:,} bytes ({metadata['file_size_bytes']/1024:.1f} KB)")
        
        print(f"  Overall compression ratio: {metadata['overall_compression_ratio']:.2f}x")
        print(f"  Space saved: {(1 - metadata['file_size_bytes']/metadata['original_size_bytes'])*100:.1f}%")
        print(f"  Processing time: {metadata['processing_time_seconds']:.2f} seconds")
        
        print(f"\n🏆 Top Templates:")
        for i, template_info in enumerate(metadata['top_templates'][:5], 1):
            print(f"  {i}. {template_info['template'][:80]}...")
            print(f"     Frequency: {template_info['frequency']:,} ({template_info['percentage']:.1f}%)")
        
        print(f"\n✅ Phase 3 completed successfully!")
        print(f"   Output: {output_file}")
        print(f"   Metadata: {metadata_file}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error in Phase 3 processing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit(main())