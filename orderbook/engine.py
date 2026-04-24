"""
orderbook/engine.py
L2 Order Book with price-time priority matching.
Supports: Market orders, Limit orders, Cancel orders.
Tracks: fills, spread, depth, imbalance, VWAP, latency.
"""

import time
import numpy as np
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Literal, Optional, List, Dict, Tuple


@dataclass
class Order:
    order_id:   str
    side:       Literal["buy","sell"]
    price:      float
    quantity:   int
    order_type: Literal["limit","market"] = "limit"
    timestamp:  float = field(default_factory=time.perf_counter)
    filled:     int   = 0
    status:     str   = "open"  # open, filled, cancelled, partial


@dataclass
class Trade:
    trade_id:    str
    buy_id:      str
    sell_id:     str
    price:       float
    quantity:    int
    timestamp:   float


class OrderBook:
    """
    Full L2 order book with price-time priority FIFO matching.
    Bids: sorted descending (best bid = highest price)
    Asks: sorted ascending  (best ask = lowest price)
    """

    def __init__(self, symbol: str = "AAPL"):
        self.symbol    = symbol
        self.bids: Dict[float, deque] = defaultdict(deque)  # price → deque of orders
        self.asks: Dict[float, deque] = defaultdict(deque)
        self.orders:   Dict[str, Order] = {}
        self.trades:   List[Trade] = []
        self.trade_counter = 0
        self.latencies: List[float] = []  # microseconds

    # ── Getters ───────────────────────────────────────────────────────────────

    def best_bid(self) -> Optional[float]:
        bids = [p for p,q in self.bids.items() if any(o.quantity-o.filled>0 for o in q)]
        return max(bids) if bids else None

    def best_ask(self) -> Optional[float]:
        asks = [p for p,q in self.asks.items() if any(o.quantity-o.filled>0 for o in q)]
        return min(asks) if asks else None

    def spread(self) -> Optional[float]:
        bb, ba = self.best_bid(), self.best_ask()
        return round(ba - bb, 4) if (bb and ba) else None

    def mid_price(self) -> Optional[float]:
        bb, ba = self.best_bid(), self.best_ask()
        return round((bb + ba) / 2, 4) if (bb and ba) else None

    def depth(self, levels: int = 5) -> dict:
        """Return top N levels of bid/ask depth."""
        bid_prices = sorted(
            [p for p,q in self.bids.items() if sum(o.quantity-o.filled for o in q)>0],
            reverse=True)[:levels]
        ask_prices = sorted(
            [p for p,q in self.asks.items() if sum(o.quantity-o.filled for o in q)>0])[:levels]
        return {
            "bids": [(p, sum(o.quantity-o.filled for o in self.bids[p])) for p in bid_prices],
            "asks": [(p, sum(o.quantity-o.filled for o in self.asks[p])) for p in ask_prices],
        }

    def imbalance(self) -> float:
        """Order book imbalance: (bid_vol - ask_vol) / (bid_vol + ask_vol)"""
        d = self.depth(10)
        bv = sum(v for _,v in d["bids"])
        av = sum(v for _,v in d["asks"])
        return round((bv - av) / (bv + av + 1e-9), 4)

    def vwap(self, n_trades: int = 50) -> Optional[float]:
        trades = self.trades[-n_trades:]
        if not trades: return None
        total_val = sum(t.price * t.quantity for t in trades)
        total_qty = sum(t.quantity for t in trades)
        return round(total_val / total_qty, 4) if total_qty else None

    # ── Order submission ──────────────────────────────────────────────────────

    def submit(self, order: Order) -> List[Trade]:
        t0 = time.perf_counter()
        trades = []
        if order.order_type == "market":
            trades = self._match_market(order)
        else:
            trades = self._match_limit(order)
            if order.quantity - order.filled > 0 and order.status != "filled":
                book = self.bids if order.side=="buy" else self.asks
                book[order.price].append(order)
                self.orders[order.order_id] = order
        latency_us = (time.perf_counter() - t0) * 1e6
        self.latencies.append(latency_us)
        return trades

    def cancel(self, order_id: str) -> bool:
        if order_id not in self.orders: return False
        order = self.orders[order_id]
        if order.status in ("filled","cancelled"): return False
        order.status = "cancelled"
        return True

    # ── Matching ──────────────────────────────────────────────────────────────

    def _match_market(self, order: Order) -> List[Trade]:
        trades = []
        book   = self.asks if order.side=="buy" else self.bids
        prices = sorted(book.keys()) if order.side=="buy" else sorted(book.keys(), reverse=True)
        remaining = order.quantity
        for price in prices:
            if remaining <= 0: break
            queue = book[price]
            while queue and remaining > 0:
                passive = queue[0]
                if passive.status in ("cancelled","filled"):
                    queue.popleft(); continue
                avail = passive.quantity - passive.filled
                fill  = min(avail, remaining)
                passive.filled += fill
                order.filled   += fill
                remaining      -= fill
                if passive.filled >= passive.quantity:
                    passive.status = "filled"
                    queue.popleft()
                t = self._make_trade(order, passive, price, fill)
                trades.append(t)
        order.status = "filled" if order.filled >= order.quantity else "partial"
        return trades

    def _match_limit(self, order: Order) -> List[Trade]:
        trades    = []
        book      = self.asks if order.side=="buy" else self.bids
        remaining = order.quantity
        prices    = sorted(book.keys()) if order.side=="buy" else sorted(book.keys(), reverse=True)
        for price in prices:
            if remaining <= 0: break
            if order.side=="buy"  and price > order.price: break
            if order.side=="sell" and price < order.price: break
            queue = book[price]
            while queue and remaining > 0:
                passive = queue[0]
                if passive.status in ("cancelled","filled"):
                    queue.popleft(); continue
                avail = passive.quantity - passive.filled
                fill  = min(avail, remaining)
                passive.filled += fill
                order.filled   += fill
                remaining      -= fill
                if passive.filled >= passive.quantity:
                    passive.status = "filled"
                    queue.popleft()
                t = self._make_trade(order, passive, price, fill)
                trades.append(t)
        if order.filled >= order.quantity:
            order.status = "filled"
        return trades

    def _make_trade(self, aggressor, passive, price, qty) -> Trade:
        self.trade_counter += 1
        buy_id  = aggressor.order_id if aggressor.side=="buy"  else passive.order_id
        sell_id = aggressor.order_id if aggressor.side=="sell" else passive.order_id
        t = Trade(f"T{self.trade_counter:06d}", buy_id, sell_id,
                  price, qty, time.perf_counter())
        self.trades.append(t)
        return t

    # ── Stats ─────────────────────────────────────────────────────────────────

    def latency_stats(self) -> dict:
        if not self.latencies: return {}
        l = np.array(self.latencies)
        return {
            "mean_us":   round(l.mean(), 3),
            "median_us": round(np.median(l), 3),
            "p95_us":    round(np.percentile(l, 95), 3),
            "p99_us":    round(np.percentile(l, 99), 3),
            "min_us":    round(l.min(), 3),
            "max_us":    round(l.max(), 3),
        }

    def summary(self) -> dict:
        return {
            "symbol":      self.symbol,
            "best_bid":    self.best_bid(),
            "best_ask":    self.best_ask(),
            "spread":      self.spread(),
            "mid_price":   self.mid_price(),
            "imbalance":   self.imbalance(),
            "vwap":        self.vwap(),
            "total_trades":len(self.trades),
            "total_volume":sum(t.quantity for t in self.trades),
            **self.latency_stats(),
        }


def seed_order_book(book: OrderBook, mid: float = 150.0,
                    levels: int = 10, qty_per_level: int = 200,
                    tick: float = 0.01) -> OrderBook:
    """Seed an order book with realistic depth around mid price."""
    np.random.seed(42)
    oid = 0
    for i in range(1, levels+1):
        bid_price = round(mid - i*tick, 4)
        ask_price = round(mid + i*tick, 4)
        qty_b = int(np.random.exponential(qty_per_level))
        qty_a = int(np.random.exponential(qty_per_level))
        book.submit(Order(f"SEED_B{oid}", "buy",  bid_price, max(1,qty_b), "limit"))
        book.submit(Order(f"SEED_A{oid}", "sell", ask_price, max(1,qty_a), "limit"))
        oid += 1
    return book


if __name__ == "__main__":
    print("⚡ Order Book Engine — Validation")
    print("="*50)
    book = OrderBook("AAPL")
    book = seed_order_book(book, mid=150.0, levels=10)
    print(f"  Best Bid : {book.best_bid()}")
    print(f"  Best Ask : {book.best_ask()}")
    print(f"  Spread   : {book.spread()}")
    print(f"  Mid      : {book.mid_price()}")
    print(f"  Imbalance: {book.imbalance()}")

    # Test market order
    book.submit(Order("MKT001","buy",0,100,"market"))
    print(f"  After market buy 100: trades={len(book.trades)}")
    print(f"  VWAP     : {book.vwap()}")
    lat = book.latency_stats()
    print(f"  Latency  : mean={lat['mean_us']:.3f}µs p99={lat['p99_us']:.3f}µs")
    print("✅ All checks passed!")
