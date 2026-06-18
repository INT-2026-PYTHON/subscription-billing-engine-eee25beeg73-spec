"""
CLI entrypoint.

Subcommands to implement (Day 4):
    billing init                              -- create / migrate the DB
    billing customer add <name> <email> <country> [--state CODE]
    billing plan list
    billing subscribe <customer_id> <plan_id> [--trial-days N] [--discount CODE]
    billing bill run [--date YYYY-MM-DD]
    billing invoice show <invoice_id>          -- prints PLAIN TEXT invoice
    billing upgrade <subscription_id> <new_plan_id> [--date YYYY-MM-DD]   (STRETCH)
    billing demo                              -- run the scripted scenario

Use argparse with subparsers. Keep each subcommand handler in its own function.

PDF rendering is OUT OF SCOPE for the core project — `invoice show` should
print a clean PLAIN-TEXT invoice (see helper `format_invoice_text` below).
PDF generation is BONUS: see `billing_engine/pdf/renderer.py`.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date

from billing_engine.models import Invoice


def format_invoice_text(invoice: Invoice, customer_name: str, plan_name: str) -> str:
    """Render an invoice as a plain-text receipt. Pure function — easy to test."""
    l=[f"INVOICE:{invoice}","\n",f"cudtomer:{customer_name}","\n",f"plan:{plan_name}","\n",f"duration:{invoice.period_start} to {invoice.period_end}"]
    for i in invoice.line_items:
        l.append(f"{i.description},amount:{i.amount}")
    l.append("\n",f"total:{invoice.total}")
    l.append("\n"f"status:{invoice.status}")
    return "\n".join(l)
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="billing", description="Subscription Billing CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="initialize the database")
    sub.add_parser("demo", help="run the demo scenario")
    args = parser.parse_args(argv)
    if args.cmd=='init':
        try:
            print("initializing database:")
            return 0
        except Exception as e:
            print(f"error initializing database {e}",file=sys.stderr)
    elif args.cmd=="demo":
        return run_demo()
    else:
        print (f"unknomn command {args.cmd}",file=sys.stderr)
        return 2

def run_demo() -> int:
    try:
        print("Executing demo:", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"Demo failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
