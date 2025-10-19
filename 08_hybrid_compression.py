#!/usr/bin/env python3
"""
Phase 8: Hybrid Compression (Compression Tricks + zstd)

This phase combines the specialized compression algorithms from Phase 5
with general-purpose zstd compression on top for ultimate compression ratios.
"""

import os
import sys
import pickle
import zstandard as zstd
import msgpack
import time

def main():
    """Apply hybrid compression to the compressed data from Phase 5."""
    print("=" * 60)
    print("Phase 8: Hybrid Compression (Compression Tricks + zstd)")
    print("=" * 60)
    
    # Load the compressed data from Phase 5
    compressed_file = "output/metrics.compressed.msgpack"
    if not os.path.exists(compressed_file):
        print(f"❌ Error: {compressed_file} not found")
        print("Please run Phase 5 (05_compression_tricks.py) first")
        sys.exit(1)
    
    print(f"Loading compressed data from Phase 5: {compressed_file}")
    
    with open(compressed_file, 'rb') as f:
        compressed_data = f.read()
    
    original_size = len(compressed_data)
    print(f"Phase 5 compressed size: {original_size:,} bytes ({original_size / 1024 / 1024:.2f} MB)")
    
    # Apply zstd compression on top of the already compressed data
    print("\nApplying zstd compression on top of Phase 5 compression...")
    
    # Test different compression levels to find the best ratio
    compression_levels = [1, 3, 6, 9, 15, 19, 22]
    best_ratio = 0
    best_level = 1
    best_compressed = None
    
    print("Testing zstd compression levels:")
    for level in compression_levels:
        start_time = time.time()
        
        # Compress with zstd
        compressor = zstd.ZstdCompressor(level=level)
        compressed = compressor.compress(compressed_data)
        
        compress_time = time.time() - start_time
        compressed_size = len(compressed)
        ratio = original_size / compressed_size if compressed_size > 0 else 0
        
        print(f"  Level {level:2d}: {compressed_size:,} bytes ({ratio:.2f}x) - {compress_time:.3f}s")
        
        if ratio > best_ratio:
            best_ratio = ratio
            best_level = level
            best_compressed = compressed
    
    # Use the best compression level
    final_size = len(best_compressed)
    
    print(f"\n🏆 Best compression: Level {best_level} ({best_ratio:.2f}x over Phase 5)")
    
    # Save the hybrid compressed data
    hybrid_file = "output/metrics.hybrid.zst"
    with open(hybrid_file, 'wb') as f:
        f.write(best_compressed)
    
    print(f"\nSaved hybrid compressed data to: {hybrid_file}")
    
    # Test decompression to verify integrity
    print("\n🔍 Verifying data integrity...")
    start_time = time.time()
    
    decompressor = zstd.ZstdDecompressor()
    decompressed = decompressor.decompress(best_compressed)
    
    decompress_time = time.time() - start_time
    
    if decompressed == compressed_data:
        print(f"✅ Data integrity verified ({decompress_time:.3f}s decompression)")
    else:
        print(f"❌ Data integrity check failed!")
        sys.exit(1)
    
    # Calculate compression ratios vs other formats
    print("\n" + "=" * 60)
    print("HYBRID COMPRESSION RESULTS")
    print("=" * 60)
    
    # Load original data for comparison
    raw_file = "output/raw_dataset.pkl"
    if os.path.exists(raw_file):
        with open(raw_file, 'rb') as f:
            raw_data = pickle.load(f)
        
        print(f"Original dataset: {len(raw_data):,} data points")
    
    # Compare with other formats
    comparison_files = {
        "output/metrics.ndjson": "NDJSON Baseline",
        "output/metrics.cbor": "CBOR Format", 
        "output/metrics.bintable.bin": "Binary Table",
        "output/metrics.columnar.msgpack": "Columnar Format",
        "output/metrics.compressed.msgpack": "Phase 5: Compression Tricks",
        "output/metrics.ndjson.zst": "Phase 7: NDJSON + zstd"
    }
    
    print(f"\n📊 Compression Comparison:")
    print(f"{'Format':<35} {'Size (bytes)':<15} {'vs Original':<12} {'vs Phase 5':<12}")
    print(f"{'-'*35} {'-'*15} {'-'*12} {'-'*12}")
    
    for filepath, description in comparison_files.items():
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            
            # Compare vs NDJSON if available
            ndjson_file = "output/metrics.ndjson"
            if os.path.exists(ndjson_file):
                ndjson_size = os.path.getsize(ndjson_file)
                vs_original = ndjson_size / size if size > 0 else 0
            else:
                vs_original = 0
            
            # Compare vs Phase 5
            vs_phase5 = original_size / size if size > 0 else 0
            
            print(f"{description:<35} {size:>14,} {vs_original:>11.1f}x {vs_phase5:>11.1f}x")
    
    # Show hybrid results
    ndjson_file = "output/metrics.ndjson"
    if os.path.exists(ndjson_file):
        ndjson_size = os.path.getsize(ndjson_file)
        vs_original_hybrid = ndjson_size / final_size if final_size > 0 else 0
    else:
        vs_original_hybrid = 0
    
    vs_phase5_hybrid = original_size / final_size if final_size > 0 else 0
    
    print(f"{'-'*35} {'-'*15} {'-'*12} {'-'*12}")
    print(f"{'🏆 Phase 8: Hybrid (Tricks+zstd)':<35} {final_size:>14,} {vs_original_hybrid:>11.1f}x {vs_phase5_hybrid:>11.1f}x")
    
    print(f"\n💡 Hybrid Compression Characteristics:")
    print(f"  ✅ Pros:")
    print(f"    - Ultimate compression ratio ({vs_original_hybrid:.1f}x over baseline)")
    print(f"    - Leverages both specialized and general-purpose algorithms")
    print(f"    - {best_ratio:.1f}x improvement over already-compressed data")
    print(f"    - Production-ready zstd format")
    print(f"  ❌ Cons:")
    print(f"    - Double compression overhead (Phase 5 + zstd)")
    print(f"    - Complex two-stage decompression required")
    print(f"    - Higher computational cost for read/write operations")
    print(f"    - Diminishing returns on already-compressed data")
    
    print(f"\n📈 Performance Summary:")
    print(f"  Compression level: {best_level} (zstd)")
    print(f"  Final size: {final_size:,} bytes ({final_size / 1024:.1f} KB)")
    print(f"  Bytes per data point: {final_size / len(raw_data):.3f}" if 'raw_data' in locals() else "")
    print(f"  Additional compression over Phase 5: {best_ratio:.2f}x")
    
    if vs_original_hybrid > 0:
        print(f"  Overall compression vs baseline: {vs_original_hybrid:.1f}x")
    
    print(f"\n✅ Phase 8 completed successfully!")
    
    return {
        "compressed_size": final_size,
        "compression_level": best_level,
        "ratio_vs_phase5": best_ratio,
        "ratio_vs_baseline": vs_original_hybrid
    }

if __name__ == "__main__":
    main()