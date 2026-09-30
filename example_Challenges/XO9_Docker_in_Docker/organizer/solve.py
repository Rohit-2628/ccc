#!/usr/bin/env python3
"""
Organizer Clean-Room Solve Script for XO-9 (Honorport Heist - Docker in Docker)
"""
import sys
from pathlib import Path

# Import parent solve logic
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from solve import solve, main

if __name__ == "__main__":
    main()
