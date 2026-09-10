#!/usr/bin/env python3
"""Unit tests for ns-cgm-graph v0.1.0 (stdlib only, no network).

Run with: python -m pytest -q
or: python3 -m unittest test_ns_cgm_graph.py -v
"""

import hashlib
import importlib.util
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

_HERE = os.path.dirname(os.path.abspath(__file__))

# Support both `ns_cgm_graph` (shim) and hyphenated `ns-cgm-graph.py`
try:
    from ns_cgm_graph import MGDL_TO_MMOL, _env_path, api_hash, fetch_entries, main, mmol
except ImportError:
    spec = importlib.util.spec_from_file_location(
        "ns_cgm_graph", os.path.join(_HERE, "ns-cgm-graph.py")
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["ns_cgm_graph"] = mod
    spec.loader.exec_module(mod)
    from ns_cgm_graph import MGDL_TO_MMOL, _env_path, api_hash, fetch_entries, main, mmol


class MmolTest(unittest.TestCase):
    def test_mmol_basic(self):
        self.assertAlmostEqual(mmol(180), 10.0)
        self.assertAlmostEqual(mmol(90), 5.0)
        self.assertAlmostEqual(mmol(0), 0.0)
        self.assertAlmostEqual(mmol(18), 1.0)

    def test_mmol_constant(self):
        self.assertEqual(MGDL_TO_MMOL, 18.0)
        self.assertAlmostEqual(mmol(360), 20.0)

    def test_mmol_roundtrip(self):
        for mgdl in [36, 72, 180, 250]:
            self.assertAlmostEqual(mmol(mgdl) * MGDL_TO_MMOL, mgdl)


class EnvPathTest(unittest.TestCase):
    def test_env_path_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            # Ensure NS_ENV is unset
            if "NS_ENV" in os.environ:
                del os.environ["NS_ENV"]
            with self.assertRaises(RuntimeError) as ctx:
                _env_path()
            self.assertIn("NS_ENV", str(ctx.exception))

    def test_env_path_present(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf:
            tf.write("API_SECRET=test\n")
            tf.flush()
            path = tf.name
        try:
            with patch.dict(os.environ, {"NS_ENV": path}):
                self.assertEqual(_env_path(), path)
        finally:
            os.unlink(path)


class ApiHashTest(unittest.TestCase):
    def test_api_hash_success(self):
        secret = "mysecret123"
        expected = hashlib.sha1(secret.encode()).hexdigest()
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf:
            tf.write(f"API_SECRET={secret}\n")
            tf.write("OTHER=value\n")
            tf.flush()
            path = tf.name
        try:
            with patch.dict(os.environ, {"NS_ENV": path}):
                self.assertEqual(api_hash(), expected)
        finally:
            os.unlink(path)

    def test_api_hash_missing_secret(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf:
            tf.write("OTHER=value\n")
            tf.flush()
            path = tf.name
        try:
            with patch.dict(os.environ, {"NS_ENV": path}):
                with self.assertRaises(RuntimeError) as ctx:
                    api_hash()
                self.assertIn("API_SECRET", str(ctx.exception))
        finally:
            os.unlink(path)


class FetchEntriesTest(unittest.TestCase):
    def test_fetch_entries_calls_ns_get(self):
        fake_entries = [{"date": 1700000000000, "sgv": 120}]
        with patch("ns_cgm_graph.ns_get", return_value=fake_entries) as mock_get:
            result = fetch_entries("http://example.com", 24)
            self.assertEqual(result, fake_entries)
            # Verify ns_get called with correct path
            args, kwargs = mock_get.call_args
            self.assertEqual(args[0], "http://example.com")
            self.assertEqual(args[1], "/api/v1/entries.json")
            # params should contain find[date][$gte] and count=10000
            self.assertIn("find[date][$gte]=", args[2])
            self.assertIn("count=10000", args[2])

    def test_fetch_entries_empty(self):
        with patch("ns_cgm_graph.ns_get", return_value=[]):
            result = fetch_entries("http://example.com", 24)
            self.assertEqual(result, [])

    def test_fetch_entries_none_returns_empty(self):
        # ns_get returns None -> fetch_entries should return []
        with patch("ns_cgm_graph.ns_get", return_value=None):
            result = fetch_entries("http://example.com", 24)
            self.assertEqual(result, [])


class SvgAvgLabelTest(unittest.TestCase):
    """Regression: the SVG avg label must show the mean in mmol/L.

    points[] already holds mmol values, so wrapping the mean in mmol()
    again divided the label by 18 (8.0 mmol/L rendered as 0.4 mmol/L).
    """

    def _entries(self):
        return [
            {"date": 1_700_000_000_000 + i * 300_000, "sgv": 144}  # 144 mg/dL = 8.0 mmol/L
            for i in range(6)
        ]

    def test_avg_label_shows_mmol(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "cgm.svg")
            argv = ["ns-cgm-graph", "--hours", "24", "--out", out]
            with patch("ns_cgm_graph.fetch_entries", return_value=self._entries()), \
                    patch.object(sys, "argv", argv):
                self.assertEqual(main(), 0)
            with open(out) as f:
                svg = f.read()
        self.assertIn("avg 8.0 mmol/L", svg)
        self.assertIn("<polyline", svg)
        self.assertIn("#4ade80", svg)  # TIR band

if __name__ == "__main__":
    unittest.main()
