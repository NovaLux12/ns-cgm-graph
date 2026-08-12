# ns-cgm-graph

Generate an SVG graph of recent Nightscout CGM data.

## Usage

```bash
python3 ns-cgm-graph.py [--url http://127.0.0.1:1337] [--hours 24] [--out cgm.svg]
```

Reads `NS_URL` from env (default `http://127.0.0.1:1337`) and `NS_ENV` for the Nightscout `.env` path (default `/home/jack/nightscout/.env`).

## Requirements

- Python 3.9+ (stdlib only)
