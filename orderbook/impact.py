"""
orderbook/impact.py
Market impact models:
  - Kyle lambda (linear permanent impact)
  - Square-root impact model
  - Temporary vs permanent impact decomposition
"""

import numpy as np
from dataclasses import dataclass


@dataclass
class ImpactParams:
    sigma:       float = 0.02    # daily volatility
    adv:         float = 1e6     # average daily volume
    bid_ask:     float = 0.02    # bid-ask spread
    perm_coef:   float = 0.1     # permanent impact coefficient
    temp_coef:   float = 0.5     # temporary impact coefficient


def kyle_lambda(order_flow: float, sigma: float, adv: float) -> float:
    """Kyle (1985) linear market impact model."""
    return sigma / np.sqrt(adv) * order_flow


def sqrt_impact(quantity: float, adv: float,
                sigma: float, eta: float = 0.1) -> float:
    """Square-root market impact model."""
    return eta * sigma * np.sqrt(quantity / adv)


def total_impact(quantity: float, params: ImpactParams) -> dict:
    """Decompose total impact into permanent and temporary components."""
    perm = params.perm_coef * params.sigma * np.sqrt(quantity / params.adv)
    temp = params.temp_coef * params.bid_ask / 2
    slippage = perm + temp
    cost     = slippage * quantity
    return {
        "permanent_impact": round(perm, 6),
        "temporary_impact": round(temp, 6),
        "total_slippage":   round(slippage, 6),
        "total_cost":       round(cost, 4),
        "cost_bps":         round(slippage / params.bid_ask * params.bid_ask * 10000, 2),
    }


def impact_curve(adv: float, sigma: float,
                 quantities: np.ndarray = None) -> dict:
    """Compute impact curve across order sizes."""
    if quantities is None:
        quantities = np.logspace(2, 6, 50)
    params = ImpactParams(sigma=sigma, adv=adv)
    impacts = [total_impact(q, params) for q in quantities]
    return {
        "quantities":  quantities.tolist(),
        "perm_impacts":[i["permanent_impact"] for i in impacts],
        "temp_impacts":[i["temporary_impact"]  for i in impacts],
        "total_costs": [i["total_cost"]        for i in impacts],
        "cost_bps":    [i["cost_bps"]          for i in impacts],
    }
