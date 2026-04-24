# ⚡ HFT Order Book Simulator

> L2 order book engine with price-time priority matching, market impact
> modeling, latency benchmarking, spread analytics, and live simulation dashboard.

## Features
- Full L2 order book (bids + asks) with price-time priority
- Market orders, limit orders, cancel orders
- Market impact model (Kyle lambda)
- Spread, depth, imbalance, VWAP analytics
- Latency benchmarking (microsecond simulation)
- Strategy backtesting on simulated flow

## Quick Start
```bash
pip install -r requirements.txt
python run_all.py
streamlit run dashboard/app.py
```

## Resume Bullets
- Built L2 order book simulator with price-time priority matching engine
  processing market/limit/cancel orders with microsecond latency tracking
- Implemented Kyle lambda market impact model; computed bid-ask spread,
  order book imbalance, VWAP, and depth analytics in real time
- Simulated 3 HFT strategies (market making, momentum, mean reversion)
  and benchmarked fill rates, P&L, and latency distributions
- Deployed live order book visualization dashboard with depth chart,
  trade tape, and real-time spread monitor
