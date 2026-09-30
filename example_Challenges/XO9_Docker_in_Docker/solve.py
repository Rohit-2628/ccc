#!/usr/bin/env python3
import sys
from pathlib import Path

# Forward to organizer/solve.py
organizer_solve = Path(__file__).resolve().parent / "organizer" / "solve.py"
exec(organizer_solve.read_text())
