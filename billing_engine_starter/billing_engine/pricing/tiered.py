"""
TieredPricing — different price per unit depending on the tier the quantity falls into.

This is the "cumulative" / "stacked" tier model, NOT the "volume" model:
    Tiers: [(0, 1000, ₹2.00), (1000, 5000, ₹1.50), (5000, None, ₹1.00)]
    Quantity = 6000:
        First 1000 units  @ ₹2.00 = ₹2000
        Next  4000 units  @ ₹1.50 = ₹6000
        Last  1000 units  @ ₹1.00 = ₹1000
        ------------------------------------
        Total                     = ₹9000

A tier with `to_units = None` is the open-ended top tier.

Tier boundaries are HALF-OPEN on the right: a tier (from, to, price)
covers units strictly less than `to` (i.e. [from, to)).
"""

from dataclasses import dataclass
from typing import Optional

from billing_engine.money import Money
from billing_engine.pricing.base import PricingStrategy


@dataclass(frozen=True)
class Tier:
    from_units: int
    to_units: Optional[int]   # None means "unlimited" / open-ended
    unit_price: Money


class TieredPricing(PricingStrategy):
    """Charges across multiple price tiers based on cumulative quantity."""

    def __init__(self, tiers: list[Tier]) -> None:
        if not tiers:
            raise ValueError("tier should have some value")
        for i in range(len(tiers)):
            if tiers[i].from_units != tiers[i].to_units:
                raise ValueError("tier should not be empty")
            if tiers[i].to_units is None and i!=len(tiers):
                raise ValueError("only last element can be zero")
        for i in tiers:
            if tiers.unit_price.currency!=tiers.unit_price.currency:
                raise ValueError ("all curency value should be same")
        self.tiers=tiers

    def calculate(self, quantity: int) -> Money:
        if quantity<0:
            raise ValueError("quantity can't be negative")
        currency=self.tiers[0].unit_price.currency
        total=Money.zero(currency)
        for i in self.tiers:
            if i.to_units is None:
                c=max(0,quantity-i.from_units)
            else:
                if quantity>i.from_units:
                    c=min(quantity,i.to_units)-i.from_units
                else:
                    c=0
            total=total+(i.unit_price*c)
        return total
Tiers=  [(0, 1000, "₹2.00") , (1000, 5000, "₹1.50"), (5000, None, "₹1.00") ]
Quantity = 6000
