"""tests/test_orderbook.py — Unit tests for order book engine."""
import sys
import numpy as np
import pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orderbook.engine import OrderBook, Order, seed_order_book
from orderbook.impact import total_impact, ImpactParams, kyle_lambda, sqrt_impact


def fresh_book(mid=150.0, levels=5):
    b = OrderBook("TEST")
    return seed_order_book(b, mid, levels=levels)


class TestOrderBook:
    def test_seed_creates_depth(self):
        b = fresh_book()
        assert b.best_bid() is not None
        assert b.best_ask() is not None

    def test_best_bid_lt_best_ask(self):
        b = fresh_book()
        assert b.best_bid() < b.best_ask()

    def test_spread_positive(self):
        b = fresh_book()
        assert b.spread() > 0

    def test_mid_price(self):
        b = fresh_book(mid=100.0)
        assert 99.5 < b.mid_price() < 100.5

    def test_market_buy_fills(self):
        b = fresh_book()
        o = Order("MKT1","buy",0,50,"market")
        trades = b.submit(o)
        assert len(trades) > 0
        assert o.filled > 0

    def test_market_sell_fills(self):
        b = fresh_book()
        o = Order("MKT2","sell",0,50,"market")
        trades = b.submit(o)
        assert len(trades) > 0

    def test_limit_order_rests(self):
        b = fresh_book()
        bb = b.best_bid()
        o  = Order("LIM1","buy",bb-0.10,100,"limit")
        b.submit(o)
        assert b.orders.get("LIM1") is not None

    def test_cancel_order(self):
        b = fresh_book()
        bb = b.best_bid()
        o  = Order("CNCL1","buy",bb-0.05,100,"limit")
        b.submit(o)
        result = b.cancel("CNCL1")
        assert result == True
        assert b.orders["CNCL1"].status == "cancelled"

    def test_imbalance_range(self):
        b = fresh_book()
        assert -1.0 <= b.imbalance() <= 1.0

    def test_latency_recorded(self):
        b = fresh_book()
        assert len(b.latencies) > 0


class TestMatching:
    def test_price_priority(self):
        """Better priced orders should fill first."""
        b = OrderBook("PRIO")
        b.submit(Order("A1","sell",100.05,100,"limit"))
        b.submit(Order("A2","sell",100.02,100,"limit"))  # better ask
        mkt = Order("B1","buy",0,50,"market")
        trades = b.submit(mkt)
        assert all(t.price == 100.02 for t in trades)

    def test_full_fill(self):
        b = fresh_book()
        o = Order("FF1","buy",0,1,"market")
        b.submit(o)
        assert o.status == "filled"

    def test_trade_recorded(self):
        b = fresh_book()
        b.submit(Order("TR1","buy",0,50,"market"))
        assert len(b.trades) > 0


class TestImpact:
    def test_kyle_lambda_positive(self):
        assert kyle_lambda(1000, 0.02, 1e6) > 0

    def test_sqrt_impact_positive(self):
        assert sqrt_impact(1000, 1e6, 0.02) > 0

    def test_total_impact_components(self):
        result = total_impact(10000, ImpactParams())
        assert result["permanent_impact"] >= 0
        assert result["temporary_impact"] >= 0
        assert result["total_cost"] >= 0

    def test_larger_order_higher_cost(self):
        p = ImpactParams()
        c1 = total_impact(1000,  p)["total_cost"]
        c2 = total_impact(100000,p)["total_cost"]
        assert c2 > c1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
