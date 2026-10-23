"""Process runners, the run manager, log buffers, and signal mapping.

Layer 2 (domain service). May import layers 0-1. Must not import other domain
services; ``actions`` and ``status`` may import this package.
"""
