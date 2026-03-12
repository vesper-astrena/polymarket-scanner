# Polymarket Scanner (Free Edition)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![No API Key](https://img.shields.io/badge/API_key-not_required-brightgreen.svg)](#)

Scan 10,000+ prediction markets for mispricings using the public Polymarket Gamma API.

## Quick Start

```bash
pip install requests
python polymarket_scanner.py
```

No API key needed. No authentication required.

## What It Does

- **Exclusive Outcome Scanner** — Detects when mutually exclusive outcomes (elections, tournaments) don't sum to 100%
- **Ladder Contradiction Detector** — Finds logical impossibilities in threshold markets (e.g., "BTC > $100K" priced higher than "BTC > $90K")

## Example Output

```
=== Polymarket Scanner (Free Edition) ===
Fetching events...
  500 events, 8000 markets

Scanning exclusive outcomes...
  3 high-confidence opportunities

Scanning ladder contradictions...
  12 contradictions found

--- Ladder Contradictions ---
  #1 Bitcoin above ___ on March 16?
     $68,000 @ 67.50% vs $72,000 @ 31.50%
     Deviation: 36.0%, Liq: $19,341
```

## REST API

Don't want to run code locally? Use the **[Polymarket Scanner API](https://github.com/vesper-astrena/polymarket-scanner-api)** — a hosted REST endpoint that returns arbitrage opportunities as JSON:

```bash
curl https://polymarket-scanner-api.onrender.com/api/scan
```

Free tier: 3 requests/day. [Pro ($29/mo)](https://vesperfinch.gumroad.com/l/polymarket-api): unlimited.

## Full Version

The [full Polymarket Scanner Toolkit](https://vesperfinch.gumroad.com/l/kxbax) ($29) adds:

- **Cross-market logical implication analysis** — Finds inconsistencies between related markets across events
- **Bidirectional ladder detection** — HIGH and LOW threshold scanning
- **Confidence scoring system** — Automatically classifies exclusive vs. non-exclusive outcomes
- **Scheduled monitoring** with alerting — Run 24/7 and get notified of new opportunities
- **Extensible architecture** — Dataclass-based design, easy to add custom strategies
- **3 ready-to-use examples** — Basic scan, scheduled monitoring, ladder monitor

## Requirements

- Python 3.10+
- `requests`

## License

MIT — free for personal and commercial use.
