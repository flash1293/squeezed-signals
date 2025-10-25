"""
Shared configuration for the squeezed-signals project.

This module provides centralized configuration values that can be used
across logs, metrics, and traces compression pipelines.
"""

# Default Zstandard compression level (1-22, where 22 is maximum compression)
# This can be overridden via command-line arguments in main.py scripts
DEFAULT_ZSTD_LEVEL = 22
