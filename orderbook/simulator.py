"""
orderbook/simulator.py
Simulates realistic order flow on the order book.
Generates: random limit orders, market orders, cancellations.
Supports: market making, momentum, mean reversion strategies.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List
from orderbook.engine import OrderBook, Order, seed_order_book


@dataclass
class SimConfig:
    symbol:       str   = "AAPL"
    mid_price:    float = 150.0
    n_steps:      int   = 1000
    arrival_rate: float = 0.7   # prob of new order per step
    cancel_rate:  float = 0.15
    market_rate:  float = 0.10
    tick_size:    float = 0.01
    volatility:   float = 0.002
    seed:         int   = 42


def simulate(config: SimConfig = None) -> dict:
    if config is None: config = SimConfig()
    np.random.seed(config.seed)

    book  = OrderBook(config.symbol)
    book  = seed_order_book(book, config.mid_price, levels=8, tick=config.tick_size)

    mid   = config.mid_price
    oid   = 10000
    mids  = [mid]
    spreads, imbalances, depths_bid, depths_ask = [], [], [], []
    all_order_ids = []

    for step in range(config.n_steps):
        # Random walk mid price
        mid += np.random.normal(0, mid * config.volatility)
        mid  = max(mid, 1.0)

        # Random order arrivals
        if np.random.random() < config.arrival_rate:
            side  = np.random.choice(["buy","sell"])
            otype = "market" if np.random.random() < config.market_rate else "limit"
            qty   = max(1, int(np.random.exponential(100)))

            if otype == "market":
                o = Order(f"O{oid}", side, 0, qty, "market")
            else:
                offset = np.random.exponential(3) * config.tick_size
                price  = round(mid - offset if side=="buy" else mid + offset, 4)
                price  = max(0.01, price)
                o      = Order(f"O{oid}", side, price, qty, "limit")
                all_order_ids.append(f"O{oid}")
            book.submit(o)
            oid += 1

        # Random cancellations
        if all_order_ids and np.random.random() < config.cancel_rate:
            cancel_id = np.random.choice(all_order_ids)
            book.cancel(cancel_id)

        # Record metrics
        mids.append(round(mid, 4))
        sp = book.spread()
        spreads.append(sp if sp else 0)
        imbalances.append(book.imbalance())
        d = book.depth(5)
        depths_bid.append(sum(v for _,v in d["bids"]))
        depths_ask.append(sum(v for _,v in d["asks"]))

    # Build trade tape
    trades_df = pd.DataFrame([{
        "trade_id": t.trade_id,
        "price":    t.price,
        "quantity": t.quantity,
        "value":    t.price * t.quantity,
    } for t in book.trades])

    return {
        "book":        book,
        "mids":        mids,
        "spreads":     spreads,
        "imbalances":  imbalances,
        "depths_bid":  depths_bid,
        "depths_ask":  depths_ask,
        "trades_df":   trades_df,
        "summary":     book.summary(),
        "latency":     book.latency_stats(),
    }


class MarketMaker:
    """Simple market making strategy — post quotes around mid, earn spread."""

    def __init__(self, spread_target=0.04, qty=50):
        self.spread_target = spread_target
        self.qty  = qty
        self.pnl  = 0.0
        self.inventory = 0
        self.trades = []

    def run(self, config: SimConfig) -> dict:
        np.random.seed(config.seed)
        book = OrderBook(config.symbol)
        book = seed_order_book(book, config.mid_price, levels=5)
        mid  = config.mid_price
        oid  = 20000
        pnls = [0.0]
        inventories = [0]

        for step in range(config.n_steps):
            mid += np.random.normal(0, mid*config.volatility)
            half = self.spread_target / 2

            # Post bid and ask
            bid_p = round(mid - half, 4)
            ask_p = round(mid + half, 4)
            bid_o = Order(f"MM_B{oid}", "buy",  bid_p, self.qty, "limit")
            ask_o = Order(f"MM_A{oid}", "sell", ask_p, self.qty, "limit")
            bid_fills = book.submit(bid_o)
            ask_fills = book.submit(ask_o)

            for t in bid_fills:
                self.inventory += t.quantity
                self.pnl       -= t.price * t.quantity
                self.trades.append({"step":step,"side":"buy","price":t.price,"qty":t.quantity})
            for t in ask_fills:
                self.inventory -= t.quantity
                self.pnl       += t.price * t.quantity
                self.trades.append({"step":step,"side":"sell","price":t.price,"qty":t.quantity})

            # Mark to market
            mark_pnl = self.pnl + self.inventory * mid
            pnls.append(round(mark_pnl, 2))
            inventories.append(self.inventory)
            oid += 1

        return {
            "pnl_curve":   pnls,
            "inventory":   inventories,
            "final_pnl":   round(pnls[-1], 2),
            "trades":      self.trades,
            "total_fills": len(self.trades),
            "sharpe":      round(np.mean(np.diff(pnls)) /
                                 (np.std(np.diff(pnls)) + 1e-9) * np.sqrt(252*config.n_steps), 3),
        }
