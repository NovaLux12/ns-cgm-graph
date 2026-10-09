# User guide

This guide is for people who want to **use** `ns-cgm-graph` to turn their
recent Nightscout CGM history into a picture they can open in a browser,
attach to a clinic appointment, or drop into a message. It assumes you
can type a command into a terminal; it does not assume you are a
programmer. To **read or modify** the code, start with
[README.md](./README.md).

> **Not a medical device.** Research and educational tooling only. It
> does not diagnose, recommend insulin doses, or substitute for clinical
> judgement. See [SECURITY.md](./SECURITY.md).

## What this does

`ns-cgm-graph` is a single Python script. Given the URL of a Nightscout
instance it downloads your recent CGM readings, converts them from mg/dL
to mmol/L, sorts them by time, and draws them as one continuous line on a
900×320 dark chart with a shaded band marking the 3.9–10.0 mmol/L target
range. The result is written to an SVG file — `cgm.svg` by default — and
one confirmation line is printed.

It runs once and exits, and nothing to configure beyond one URL, one
window, one output path, and the path to your Nightscout `.env` file. It
does not need to run on the same machine as Nightscout; any computer that
can reach the URL works. Where
[`ns-reports`](https://github.com/NovaLux12/ns-reports) gives you the
numbers, this gives you the shape.

## Is this for me?

You need all of these:

- **A Nightscout instance** with recent history in it — self-hosted,
  hosted by a provider, or a friend's instance you have read access to. If
  you don't have one, [nightscout.info](https://www.nightscout.info/) has
  setup instructions.
- **That instance's API secret** — the long random string set when the
  site was created. You need the value itself, not just browser access.
- **Python 3.9 or newer** (`python3 --version` to check), **`git`**, and
  read access to the data — the script only ever reads.

The packaging metadata declares `requires-python = ">=3.9"`, so 3.9 is
the floor the package claims. The automated test suite, however, only
runs on **3.11, 3.12 and 3.13** (see `.github/workflows/ci.yml`), so
those three are the versions actually exercised on every commit. The code
uses nothing newer than 3.9 features, so 3.9 and 3.10 should work — but
if you have a choice, use 3.11 or newer. Standard library only: nothing
else to install, no build step.

## Install

There is no package on PyPI: `pip install ns-cgm-graph` does not work,
because nothing is published there. The supported path is clone and run:

```bash
git clone https://github.com/NovaLux12/ns-cgm-graph.git
cd ns-cgm-graph
python3 ns-cgm-graph.py --help
```

The repo does carry a `pyproject.toml`, so if you would rather have an
`ns-cgm-graph` command on your `PATH` you can install from the clone you
already have — the README shows `pipx install git+…` and `pip install .`
as the two options. Both build from the source you downloaded; neither
contacts PyPI.

## Pointing it at your Nightscout

Pass the instance address with `--url`, or export `NS_URL`. If you give
neither it defaults to `http://127.0.0.1:1337`, the address a Nightscout
running on the same machine listens on. A trailing slash is stripped for
you.

The API secret comes from a `.env`-style file whose path you put in
`NS_ENV`. The script looks for a line starting with `API_SECRET=`, strips
whitespace, and sends the **SHA-1 hash** of the value in the `API-SECRET`
header — which is what the Nightscout API expects. It reads that one line
and nothing else from the file. Create it outside the repo so you can't
commit it by accident:

```bash
echo 'API_SECRET=your-nightscout-api-secret' > "$HOME/.nightscout.env"
chmod 600 "$HOME/.nightscout.env"
export NS_ENV="$HOME/.nightscout.env"
```

`NS_ENV` is not optional. The script has no unauthenticated mode: if the
variable is unset it stops with `NS_ENV must point to your Nightscout
.env file`.

## Running it

```bash
python3 ns-cgm-graph.py                                # last 24h → cgm.svg
python3 ns-cgm-graph.py --hours 72 --out cgm-72h.svg   # longer window
python3 ns-cgm-graph.py --url https://ns.example.com   # remote instance
```

| Flag | Default | What it does |
|---|---|---|
| `--url` | `NS_URL`, else `http://127.0.0.1:1337` | Base URL of the instance |
| `--hours` | `24` | Lookback window, in hours |
| `--out` | `cgm.svg` | Where to write the SVG |

On success it prints one line and exits:

```
Wrote cgm.svg (287 points, 24h)
```

Each run makes a single request for entries, with a 30-second timeout,
asking for up to 10 000 records. There is no retry logic: a request that
fails fails the run.

## Reading the chart

The chart is deliberately minimal, so knowing what is *not* there is as
useful as knowing what is.

- **The line** is your glucose over time, drawn left to right, oldest
  reading on the left. Values are converted from mg/dL to mmol/L (÷18)
  and plotted as one continuous polyline — there are no dots on
  individual readings.
- **The shaded green band** is the target range: 3.9 mmol/L at the bottom
  of the band, 10.0 mmol/L at the top. Time inside it is time in range;
  above it is highs, below it is lows.
- **The average**, top right, is the mean of every plotted reading in
  mmol/L, one decimal place. **The title**, top left, restates the window
  you asked for.
- **What is not on the chart:** no axis lines, no tick marks, no numeric
  scale on either axis, and no gridlines. The vertical scale is fitted to
  your data — one mmol/L below your lowest reading to one above your
  highest, clamped to 1.0–30.0 mmol/L — so **the height of the line is
  comparable between charts with similar ranges, but not across different
  weeks or different people.** The horizontal scale always spans exactly
  the window you asked for, and its right-hand edge is anchored on your
  **most recent reading**, not on the clock: if your CGM stopped
  uploading an hour ago the chart still ends at that last reading, and the
  hour of silence is simply not visible.

### The SVG file

The output is plain, self-contained SVG: 900×320 pixels with a matching
`viewBox`, a near-black background, and no external fonts, scripts or
images. Open it in any browser or image viewer (`xdg-open cgm.svg` on
Linux, `open cgm.svg` on macOS), attach it to an email, or keep it in a
folder of appointment notes. To get a PNG, convert it:

```bash
rsvg-convert cgm.svg -o cgm.png     # if rsvg-convert is installed
```

One caveat: many Markdown renderers, GitHub included, strip or block
inline SVG. To put the chart in a document, link to the file or convert
it to PNG first.

## Troubleshooting

- **`NS_ENV must point to your Nightscout .env file`** — the variable is
  unset or empty.
- **`API_SECRET not found in <path>`** — the check is
  `line.startswith("API_SECRET=")`, so `export API_SECRET=…`,
  `API_SECRET = …` with spaces, or an indented or commented line will not
  match. The line must start at column zero with exactly `API_SECRET=`.
- **`HTTP 401`** — the secret is wrong, or doesn't match what Nightscout
  was configured with. The script sends the SHA-1 hash of the value in
  the file, not the value itself.
- **`HTTP 404`, or `No entries found.`** — almost always a wrong base URL: a
  missing path segment, or the site root when your instance lives under a
  sub-path. `No entries found.` specifically means the request succeeded but
  returned nothing — an empty window or the wrong instance. Open
  `/api/v1/entries.json?count=1` in a browser and confirm it returns JSON,
  then try `--hours 72`.
- **`No SGV values found.`** — entries came back but none had an `sgv`
  field, so there is nothing to plot. That usually means you are pointed
  at an instance that stores something other than CGM readings.
- **The chart is empty on the right** — your most recent reading is older
  than you think, or newer readings exist but were not returned. Compare
  the `points` count in the confirmation line with what your Nightscout
  shows.
- **The line looks squashed or clipped** — the vertical scale is fitted to
  your data within the 1.0–30.0 mmol/L clamp, so a window holding both a
  deep hypo and a big high compresses everything in between. Narrow the
  window with `--hours` for more detail.
- **A `URLError` traceback** — the script handles HTTP error responses
  (`HTTP <code> from <url>`, exit 1) but not transport failures. A refused
  connection, DNS failure or 30-second timeout surfaces as an uncaught
  exception. Retry, or check the URL and your network.

## FAQ

**Does it change anything in my Nightscout?** No — one GET request,
nothing else. There is no code path that writes.

**Can I run it on a schedule?** A cron job or systemd timer works. Set
`NS_ENV` in the job's environment; it is not read from any config file:

```cron
0 */6 * * * NS_ENV=$HOME/.nightscout.env NS_URL=https://ns.example.com \
  python3 /home/you/ns-cgm-graph/ns-cgm-graph.py --hours 24 --out /home/you/cgm/cgm.svg
```

**Why is the chart in mmol/L?** Nightscout stores mg/dL; the script
divides by 18 for plotting and for the average label. There is no unit
flag.

**Can I change the target band or the colours?** Not in this version — the
band is fixed at 3.9–10.0 mmol/L and the scaling and colours are
constants in the source. Changing them means editing `ns_cgm_graph.py`.

**How far back can I go?** `--hours` takes any integer; `--hours 168` is a
week. The request asks for up to 10 000 records, which at five-minute
intervals is around 34 days.

## Disclaimer

Research and educational purposes only. **Not a medical device**, **not
FDA approved**, does not recommend insulin doses. **Not affiliated with or
endorsed by Medtronic**, and no relationship with your Nightscout
instance beyond the read request you ask it to make. Every treatment
decision stays with you and your diabetes team.

## License

MIT — see [LICENSE](./LICENSE). Part of
[Loopwise Health](https://loopwise.uk) — research and educational tooling
only.
