# ns-cgm-graph

[![CI](https://github.com/NovaLux12/ns-cgm-graph/actions/workflows/ci.yml/badge.svg)](https://github.com/NovaLux12/ns-cgm-graph/actions/workflows/ci.yml) [![Release](https://github.com/NovaLux12/ns-cgm-graph/actions/workflows/release.yml/badge.svg)](https://github.com/NovaLux12/ns-cgm-graph/actions/workflows/release.yml) [![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/) [![Python 3.11-3.13](https://img.shields.io/badge/tested-3.11%E2%80%933.13-green)](https://github.com/NovaLux12/ns-cgm-graph/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Generate an SVG graph of recent Nightscout CGM data. Zero dependencies — Python stdlib only.

## Install

```bash
# clone and run directly (no install)
git clone https://github.com/NovaLux12/ns-cgm-graph.git
cd ns-cgm-graph
python3 ns-cgm-graph.py --help

# isolated CLI via pipx
pipx install git+https://github.com/NovaLux12/ns-cgm-graph.git
ns-cgm-graph --help

# pip in a venv
pip install .
```

Requires Python 3.9+ (tested on 3.11–3.13). No third-party deps.

## Usage

```bash
python3 ns-cgm-graph.py [--url http://127.0.0.1:1337] [--hours 24] [--out cgm.svg]
python3 ns-cgm-graph.py --hours 72 --out cgm-72h.svg
python3 ns-cgm-graph.py --url https://your-ns.example.com --hours 24 --out cgm.svg
ns-cgm-graph --hours 24 --out cgm.svg   # after pipx/pip install
```

Reads `NS_URL` from env (default `http://127.0.0.1:1337`) and `NS_ENV` for the path to your Nightscout `.env` file (e.g. `~/.nightscout.env` containing `API_SECRET`).

```
$ python3 ns-cgm-graph.py --help
usage: ns_cgm_graph.py [-h] [--url URL] [--hours HOURS] [--out OUT]
  --url URL      Nightscout base URL (default: NS_URL env or http://127.0.0.1:1337)
  --hours HOURS  Lookback window in hours (default: 24)
  --out OUT      Output SVG path (default: cgm.svg)
```

Output is a single SVG (`cgm.svg` by default, 900×320, dark background with TIR band). Open with any browser or image viewer:

```bash
xdg-open cgm.svg   # linux
open cgm.svg       # macOS
```

To produce PNG, convert the SVG (e.g. `rsvg-convert cgm.svg -o cgm.png` or open in a browser and export).

## Development

```bash
python -m pytest -q
python3 -m unittest test_ns_cgm_graph.py -v
python -m py_compile ns_cgm_graph.py
pip install build && python -m build
```

Stdlib only — `pytest` and `build` are the only dev extras (CI installs `pytest` and runs on 3.11–3.13).

## License

MIT — see [LICENSE](LICENSE).
