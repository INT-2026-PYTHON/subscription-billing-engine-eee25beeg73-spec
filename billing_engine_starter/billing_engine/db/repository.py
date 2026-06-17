"""
Repositories — the ONLY place SQL lives.

Each repository wraps the Database connection and exposes methods that
take/return domain dataclasses (defined in billing_engine/models/).

⚠️ YOU IMPLEMENT every method body marked TODO.
   The signatures, docstrings, and the LedgerRepository's append-only
   guarantee are already in place — do not change them.

Conventions:
  - Always use parameterized queries (`?` placeholders) — NEVER f-string SQL.
  - Money values are persisted as TEXT using `money.to_storage()`.
  - Dates are persisted as ISO strings (`date.isoformat()`).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from billing_engine.db import queries as q
from billing_engine.db.database import Database
from billing_engine.money import Money
from billing_engine.models import (
    Customer,
    Plan, PricingType, BillingPeriod,
    Subscription, SubscriptionStatus,
    Invoice, InvoiceStatus, InvoiceLineItem, LineItemKind,
    LedgerEntry, LedgerDirection,
)


# ============================================================
# CUSTOMERS
# ============================================================
class CustomerRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, customer: Customer) -> Customer:
        """Insert and return the customer with `id` populated."""
        with self.db.transaction() as c:
            new_id = q.insert_customer(c,customer.name,customer.email,customer.country_code,customer.state_code)
            return Customer(id=new_id,name=customer.name,email=customer.email,country_code=customer.country_code,state_code=customer.state_code,created_at=customer.created_at)
    def get(self, customer_id: int) -> Optional[Customer]:
        with self.db.connect() as c:
            r=q.select_customer_by_id(c,customer_id)
            if r:
                return Customer(id=r["id"],name=r["name"],email=r["email"],country_code=r["country_code"],state_code=r["state_code"])
            else:
                return None

    def find_by_email(self, email: str) -> Optional[Customer]:
        with self.db.connect() as c:
            r = q.select_customer_by_email(c, email)
            if r:
                return Customer(id=r["id"],name=r["name"],email=r["email"],country_code=r["country_code"],state_code=r["state_code"],created_at=r["created_at"],)
            else:
                return None
    def list_all(self) -> list[Customer]:
        with self.db.connect() as conn:
            r = q.select_all_plans(conn)
        return Customer(id=r["id"],name=r["name"],pricing_type=PricingType(r["pricing_type"]),billing_period=BillingPeriod(r["billing_period"]),currency=r["currency"],config_json=r["config_json"])
# ============================================================
# PLANS  +  PLAN TIERS
# ============================================================
class PlanRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, plan: Plan) -> Plan:
        plan_id=plan.id
        with self.db.transaction() as conn:
            return q.insert_plan_tier(conn, plan_id, plan.from_units, plan.to_units, plan.unit_price.to_storage())

    def get(self, plan_id: int) -> Optional[Plan]:
        with self.db.connect() as c:
            r = q.conn.execute(plan_id).fetchone()
        if r:
            return Customer( id=r["id"],name=r["name"],email=r["email"],country_code=r["country_code"],state_code=r["state_code"])
        else:
            return None

    def list_all(self) -> list[Plan]:
        with self.db.connect() as c:
            r = c.execute().fetchall()
        return [Plan( id=r["id"],name=r["name"],email=r["email"],country_code=r["country_code"],state_code=r["state_code"]) for row in r]
class PlanTierRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, plan_id: int, from_units: int, to_units: Optional[int], unit_price: Money) -> int:
        with self.db.transaction() as c:
            return int(c.execute((plan_id, from_units, to_units, unit_price)).lastrowid)
    def list_for_plan(self, plan_id: int, currency: str) -> list[tuple[int, Optional[int], Money]]:
        with self.db.connect() as c:
            r=c.execute(plan_id).fetchall()
        return [(row["from_units"], row["to_units"], Money(row["unit_price"], currency))for row in r]   

# ============================================================
# DISCOUNTS
# ============================================================
class DiscountRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, code: str, discount_type: str, value: str, currency: Optional[str] = None) -> int:
       with self.db.transaction() as c:
           return int(c.execute((code, discount_type, value, currency).lastrowid))

    def get_by_code(self, code: str) -> Optional[dict]:
        with self.db.connect() as c:
            r=c.execute( (code,)).fetchone()
        if r:
            return dict(r)
        else:
            return None

# ============================================================
# SUBSCRIPTIONS
# ============================================================
class SubscriptionRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, subscription: Subscription) -> Subscription:
        with self.db.transaction() as c:
            customer_id:int
            plan_id:int
            status:str
            current_period_start: str
            current_period_end: str
            trial_end: Optional[str]
            discount_id: Optional[int]
            past_due_since: Optional[str]
            n=int(c.execute((customer_id,plan_id,status,current_period_start,current_period_end,trial_end,discount_id,past_due_since,)).lastrowid)
        return Subscription(id=n,customer_id=subscription.customer_id,plan_id=subscription.plan_id,status=subscription.status,current_period_start=subscription.current_period_start,current_period_end=subscription.current_period_end,trial_end=subscription.trial_end,discount_id=subscription.discount_id,past_due_since=subscription.past_due_since)
    def get(self, subscription_id: int) -> Optional[Subscription]:
        with self.db.connect() as c:
            as_of_iso: str
            r=c.execute(as_of_iso,).fetchall()
        return Subscription(id=r["id"],customer_id=r["customer_id"],plan_id=r["plan_id"],status=SubscriptionStatus(r["status"]),current_period_start=date.fromisoformat(r["current_period_start"]),current_period_end=date.fromisoformat(r["current_period_end"]),trial_end= date.fromisoformat(r["trial_end"]),discount_id=r["discount_id"],past_due_since= date.fromisoformat(r["past_due_since"]),)
    def list_all(self) -> list[Subscription]:
        with self.db.connect() as c:
            r= c.execute().fetchall()
        return Subscription(id=r["id"],customer_id=r["customer_id"],plan_id=r["plan_id"],status=SubscriptionStatus(r["status"]),current_period_start=date.fromisoformat(r["current_period_start"]),current_period_end=date.fromisoformat(r["current_period_end"]),trial_end= date.fromisoformat(r["trial_end"]),discount_id=r["discount_id"],past_due_since= date.fromisoformat(r["past_due_since"]),)
    def get_due_for_billing(self, as_of: date) -> list[Subscription]:
        with self.db.connect() as c:
            as_of_iso:str
            r=c.execute(as_of_iso,).fetchall()
            return Subscription(id=r["id"],customer_id=r["customer_id"],plan_id=r["plan_id"],status=SubscriptionStatus(r["status"]),current_period_start=date.fromisoformat(r["current_period_start"]),current_period_end=date.fromisoformat(r["current_period_end"]),trial_end= date.fromisoformat(r["trial_end"]),discount_id=r["discount_id"],past_due_since= date.fromisoformat(r["past_due_since"]),)
    
    def update_period(self, subscription_id: int, new_start: date, new_end: date) -> None:
       # TODO Day 3.
       raise NotImplementedError("Day 3: implement SubscriptionRepository.update_period")
    def update_status(
        self,
        subscription_id: int,
        new_status: SubscriptionStatus,
        past_due_since: Optional[date] = None,
    ) -> None:
        # TODO Day 3.
        raise NotImplementedError("Day 3: implement SubscriptionRepository.update_status")

    def update_plan(self, subscription_id: int, new_plan_id: int) -> None:
        """Switch the subscription to a different plan (used by upgrade flow)."""
        # TODO Day 4.
        raise NotImplementedError("Day 4: implement SubscriptionRepository.update_plan")


# ============================================================
# USAGE
# ============================================================
class UsageRecordRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, subscription_id: int, metric: str, quantity: int) -> int:
        with self.db.transaction() as c:
            return int( c.execute((subscription_id, metric, quantity),).lastrowid)
    def sum_for_period(
        self, subscription_id: int, metric: str, period_start: date, period_end: date
    ) -> int:
        with self.db.connect() as c:
            return c.execute((subscription_id, metric),).fetchone()

# ============================================================
# INVOICES + LINE ITEMS
# ============================================================
class InvoiceRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, invoice: Invoice) -> Invoice:
         with self.db.transaction() as c:
            subscription_id: int
            period_start: str
            period_end: str
            currency: str
            subtotal: str
            discount_total: str
            tax_total: str
            total: str
            status: str
            issued_at: Optional[str]
            pdf_path: Optional[str]
            n=int(c.execute((invoice.subscription_id,invoice.period_start,invoice.period_end,invoice.currency,invoice.subtotal,invoice.discount_total,invoice.tax_total,invoice.total,invoice.status,invoice.issued_at,invoice.pdf_path,),).lastrowid)
            return Invoice(id=n,subscription_id=invoice.subscription_id,period_start=invoice.period_start,period_end=invoice.period_end,subtotal=invoice.subtotal,discount_total=invoice.discount_total,tax_total=invoice.tax_total,total=invoice.total,status=invoice.status,issued_at=invoice.issued_at,pdf_path=invoice.pdf_path,line_items=invoice.line_items,)
    def get(self, invoice_id: int) -> Optional[Invoice]:
        with self.db.connect() as c:
            r=c.execute((invoice_id,)).fetchone()
            currency = r["currency"]
            if r:
                return Invoice(id=r["id"],subscription_id=r["subscription_id"],period_start=date.fromisoformat(r["period_start"]),period_end=date.fromisoformat(r["period_end"]),subtotal=Money(r["subtotal"], currency),discount_total=Money(r["discount_total"], currency),tax_total=Money(r["tax_total"], currency),total=Money(r["total"], currency),status=InvoiceStatus(r["status"]),issued_at=datetime.fromisoformat(r["issued_at"]),pdf_path=r["pdf_path"],)
    def count_for_subscription(self, subscription_id: int) -> int:
        """Used by FirstMonthFree discount."""
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement InvoiceRepository.count_for_subscription")

    def mark_paid(self, invoice_id: int) -> None:
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement InvoiceRepository.mark_paid")

    def mark_failed(self, invoice_id: int) -> None:
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement InvoiceRepository.mark_failed")

    def set_pdf_path(self, invoice_id: int, path: str) -> None:
        # TODO Day 4.
        raise NotImplementedError("Day 4: implement InvoiceRepository.set_pdf_path")


class InvoiceLineItemRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, line_item: InvoiceLineItem) -> InvoiceLineItem:
        if line_item.invoice_id is None:
            raise ValueError("line_item.invoice_id is required")
        with self.db.transaction() as c:
            invoice_id: int
            description: str
            amount: str
            kind: str
            n=int(c.execute((invoice_id, description, amount, kind),).lastrowid)
            return InvoiceLineItem(id=n,invoice_id=line_item.invoice_id,description=line_item.description,amount=line_item.amount,kind=line_item.kind,)
    def list_for_invoice(self, invoice_id: int) -> list[InvoiceLineItem]:
        with self.db.connect() as c:
            i=c.execute((invoice_id,)).fetchone()
            if i is None:
                return []
            r=c.execute((invoice_id,),).fetchall()
            currency = r["currency"]
        return  InvoiceLineItem(id=r["id"],invoice_id=r["invoice_id"],description=r["description"],amount=Money(r["amount"], currency),kind=LineItemKind(r["kind"]))

# ============================================================
# LEDGER — APPEND-ONLY (do not implement update/delete)
# ============================================================
class LedgerRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(self, entry: LedgerEntry) -> LedgerEntry:
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement LedgerRepository.add")

    def list_for_customer(self, customer_id: int) -> list[LedgerEntry]:
        # TODO Day 2.
        raise NotImplementedError("Day 2: implement LedgerRepository.list_for_customer")

    # ✅ These two methods are intentionally implemented to REJECT — do not override.
    def update(self, *args, **kwargs):
        raise NotImplementedError("Ledger is append-only. Post a reversing entry instead.")

    def delete(self, *args, **kwargs):
        raise NotImplementedError("Ledger is append-only. Post a reversing entry instead.")


# ============================================================
# PAYMENT ATTEMPTS
# ============================================================
class PaymentAttemptRepository:
    def __init__(self, db: Database) -> None:
        self.db = db

    def add(
        self,
        invoice_id: int,
        attempt_no: int,
        status: str,
        failure_reason: Optional[str],
        next_retry_at: Optional[datetime],
    ) -> int:
        # TODO Day 3.
        raise NotImplementedError("Day 3: implement PaymentAttemptRepository.add")

    def list_for_invoice(self, invoice_id: int) -> list[dict]:
        # TODO Day 3.
        raise NotImplementedError("Day 3: implement PaymentAttemptRepository.list_for_invoice")

    def count_for_invoice(self, invoice_id: int) -> int:
        # TODO Day 3.
        raise NotImplementedError("Day 3: implement PaymentAttemptRepository.count_for_invoice")
