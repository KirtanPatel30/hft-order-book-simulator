"""api/main.py — FastAPI order book REST API."""
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal, Optional

app = FastAPI(title="HFT Order Book API", version="1.0.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])

# Global order book instance
from orderbook.engine import OrderBook, Order, seed_order_book
_book = OrderBook("AAPL")
_book = seed_order_book(_book, 150.0, levels=10)
_oid  = [0]

class OrderRequest(BaseModel):
    side:       Literal["buy","sell"]
    price:      Optional[float] = None
    quantity:   int = Field(..., ge=1, le=100000)
    order_type: Literal["limit","market"] = "limit"

class SimRequest(BaseModel):
    n_steps:   int   = Field(500, ge=100, le=5000)
    mid_price: float = Field(150.0)
    volatility:float = Field(0.002)

@app.get("/health")
def health():
    return {"status":"healthy","symbol":_book.symbol,"trades":len(_book.trades)}

@app.get("/book/summary")
def book_summary():
    return _book.summary()

@app.get("/book/depth")
def book_depth(levels: int = 5):
    return _book.depth(levels)

@app.post("/order")
def submit_order(req: OrderRequest):
    _oid[0] += 1
    o = Order(f"API{_oid[0]:06d}", req.side,
              req.price or 0, req.quantity, req.order_type)
    trades = _book.submit(o)
    return {"order_id": o.order_id, "status": o.status,
            "filled": o.filled, "trades": len(trades),
            "summary": _book.summary()}

@app.get("/latency")
def latency_stats():
    return _book.latency_stats()

@app.post("/simulate")
def run_simulation(req: SimRequest):
    from orderbook.simulator import simulate, SimConfig
    cfg = SimConfig(n_steps=req.n_steps, mid_price=req.mid_price,
                    volatility=req.volatility)
    result = simulate(cfg)
    return {
        "summary":     result["summary"],
        "latency":     result["latency"],
        "n_trades":    len(result["trades_df"]),
        "avg_spread":  round(float(np.mean([s for s in result["spreads"] if s>0])),4),
        "avg_imbalance":round(float(np.mean(result["imbalances"])),4),
    }

@app.get("/impact")
def market_impact(quantity: float = 10000, adv: float = 1e6, sigma: float = 0.02):
    from orderbook.impact import total_impact, ImpactParams
    return total_impact(quantity, ImpactParams(sigma=sigma, adv=adv))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
