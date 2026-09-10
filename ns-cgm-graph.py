#!/usr/bin/env python3
"""Direct-run entry point for ns-cgm-graph.

Thin shim over the canonical ``ns_cgm_graph`` module so the two
entry points can never drift apart again (fixes #3): ``python3
ns-cgm-graph.py`` behaves exactly like ``python3 ns_cgm_graph.py``
and the installed ``ns-cgm-graph`` console script.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ns_cgm_graph import main

if __name__ == "__main__":
    raise SystemExit(main())
