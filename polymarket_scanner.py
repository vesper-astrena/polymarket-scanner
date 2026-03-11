"""
Polymarket Scanner (Free Edition)
Scan prediction markets for mispricings using the public Gamma API.

This is the free version with basic scanning capabilities.
Full version with advanced analysis available at:
https://vesperfinch.gumroad.com/l/kxbax
"""

import requests
import json
import time
import re
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional

GAMMA_API = "https://gamma-api.polymarket.com"


@dataclass
class Market:
    question: str
    yes_price: float
    no_price: float
    liquidity: float
    volume_24h: float
    condition_id: str
    event_title: str = ""


class PolymarketClient:
    """Lightweight client for the Polymarket Gamma API (read-only, no auth needed)."""

    def __init__(self, rate_limit_delay: float = 0.4):
        self.delay = rate_limit_delay

    def get_events(self, max_pages: int = 10) -> list[dict]:
        """Fetch active events with pagination."""
        all_events = []
        offset = 0
        for _ in range(max_pages):
            try:
                resp = requests.get(
                    f"{GAMMA_API}/events",
                    params={"closed": "false", "limit": 50, "offset": offset,
                            "order": "volume24hr", "ascending": "false"},
                    timeout=30,
                )
                resp.raise_for_status()
                events = resp.json()
                if not events:
                    break
                all_events.extend(events)
                offset += 50
                time.sleep(self.delay)
            except Exception as e:
                print(f"  Error at offset {offset}: {e}")
                break
        return all_events

    def parse_market(self, raw: dict, event_title: str = "") -> Optional[Market]:
        """Parse raw market data into a Market object."""
        prices_raw = raw.get("outcomePrices")
        if not prices_raw:
            return None
        try:
            prices = json.loads(prices_raw) if isinstance(prices_raw, str) else prices_raw
            if len(prices) < 2:
                return None
            yes_price, no_price = float(prices[0]), float(prices[1])
            if yes_price == 0 and no_price == 0:
                return None
        except (ValueError, TypeError):
            return None
        return Market(
            question=raw.get("question", ""),
            yes_price=yes_price, no_price=no_price,
            liquidity=float(raw.get("liquidity", 0) or 0),
            volume_24h=float(raw.get("volume24hr", 0) or 0),
            condition_id=raw.get("conditionId", ""),
            event_title=event_title,
        )


def scan_exclusive_outcomes(client: PolymarketClient, events: list[dict]) -> list[dict]:
    """
    Detect mispricing in mutually exclusive outcome events.
    Free version: basic detection with confidence filtering.
    """
    opportunities = []
    for event in events:
        title = event.get("title", "")
        markets = []
        for rm in event.get("markets", []):
            m = client.parse_market(rm, title)
            if m and m.liquidity >= 100:
                markets.append(m)
        if len(markets) < 2:
            continue

        total_yes = sum(m.yes_price for m in markets)
        deviation = abs(total_yes - 1.0)
        if deviation <= 0.03:
            continue

        # Only high-confidence (truly exclusive) events
        is_exclusive = any(kw in title.lower() for kw in ["winner", "champion", "who will win"])
        if not is_exclusive:
            continue

        opportunities.append({
            "event": title,
            "num_markets": len(markets),
            "total_yes": round(total_yes, 4),
            "deviation_pct": round(deviation * 100, 2),
            "min_liquidity": round(min(m.liquidity for m in markets), 2),
        })

    opportunities.sort(key=lambda x: x["deviation_pct"], reverse=True)
    return opportunities


def scan_ladder_contradictions(client: PolymarketClient, events: list[dict]) -> list[dict]:
    """
    Detect logical contradictions in threshold markets.
    Free version: basic HIGH direction detection.

    Full version includes LOW direction, cross-market analysis,
    and confidence scoring: https://vesperfinch.gumroad.com/l/kxbax
    """
    findings = []
    for event in events:
        title = event.get("title", "")
        numeric_markets = []
        for rm in event.get("markets", []):
            m = client.parse_market(rm, title)
            if not m or m.liquidity < 100:
                continue
            numbers = re.findall(r'\$?([\d,]+\.?\d*)', m.question)
            if not numbers:
                continue
            try:
                value = float(numbers[-1].replace(",", ""))
            except ValueError:
                continue
            q_lower = m.question.lower()
            if any(kw in q_lower for kw in ["high", "above", "reach", "hit"]):
                numeric_markets.append({"market": m, "value": value})

        numeric_markets.sort(key=lambda x: x["value"])
        for i in range(len(numeric_markets) - 1):
            lower, higher = numeric_markets[i], numeric_markets[i + 1]
            if lower["value"] == higher["value"]:
                continue
            lm, hm = lower["market"], higher["market"]
            if lm.yes_price < hm.yes_price and lm.yes_price > 0.01:
                findings.append({
                    "event": title,
                    "lower": f"${lower['value']:,.0f} @ {lm.yes_price:.2%}",
                    "higher": f"${higher['value']:,.0f} @ {hm.yes_price:.2%}",
                    "deviation_pct": round((hm.yes_price - lm.yes_price) * 100, 2),
                    "min_liquidity": round(min(lm.liquidity, hm.liquidity), 2),
                })

    findings.sort(key=lambda x: x["deviation_pct"], reverse=True)
    return findings


def main():
    print(f"=== Polymarket Scanner (Free Edition) ===")
    print(f"Time: {datetime.now().isoformat()}\n")

    client = PolymarketClient()

    print("Fetching events...")
    events = client.get_events(max_pages=10)
    total_markets = sum(len(e.get("markets", [])) for e in events)
    print(f"  {len(events)} events, {total_markets} markets\n")

    print("Scanning exclusive outcomes...")
    exclusive = scan_exclusive_outcomes(client, events)
    print(f"  {len(exclusive)} high-confidence opportunities\n")

    print("Scanning ladder contradictions...")
    ladders = scan_ladder_contradictions(client, events)
    print(f"  {len(ladders)} contradictions found\n")

    if exclusive:
        print("--- Exclusive Outcome Mispricings ---")
        for i, opp in enumerate(exclusive[:10]):
            print(f"  #{i+1} {opp['event']}")
            print(f"     Sum(Yes)={opp['total_yes']}, Deviation={opp['deviation_pct']}%")
            print(f"     Min Liquidity: ${opp['min_liquidity']:,.0f}")

    if ladders:
        print("\n--- Ladder Contradictions ---")
        for i, f in enumerate(ladders[:10]):
            print(f"  #{i+1} {f['event']}")
            print(f"     {f['lower']} vs {f['higher']}")
            print(f"     Deviation: {f['deviation_pct']}%, Liq: ${f['min_liquidity']:,.0f}")

    print(f"\n---")
    print(f"Full version with cross-market analysis, scheduled monitoring,")
    print(f"and advanced confidence scoring:")
    print(f"  https://vesperfinch.gumroad.com/l/kxbax")


if __name__ == "__main__":
    main()
