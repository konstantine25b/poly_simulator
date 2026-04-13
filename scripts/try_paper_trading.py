import sys
from pathlib import Path

_src = str(Path(__file__).resolve().parent.parent / "src")
if _src in sys.path:
    sys.path.remove(_src)
sys.path.insert(0, _src)
for _k in list(sys.modules):
    if _k == "polymarket" or _k.startswith("polymarket."):
        del sys.modules[_k]

from polymarket.auth import Access
from polymarket.db import create_tables, get_connection
from polymarket.trading.service import TradingService

conn = get_connection()
create_tables(conn)
conn.close()

RELAX = Access(1, True)
svc = TradingService(1, RELAX)

print(
    """
Paper trading REPL helpers are loaded.

  RELAX            -> Access(1, True)  (local REPL: treat as admin for all portfolios)
  svc              -> TradingService(1, RELAX)
  TradingService   -> class (create_portfolio, list_portfolios, …)

Try:
  TradingService.list_portfolios(RELAX)
  TradingService.create_portfolio(RELAX, name="MyBook", balance=500)
  svc.get_portfolio()              # default portfolio for this svc
  svc.get_portfolio(2)             # any portfolio by id
  svc.get_portfolio("MyBook")      # or by name (case-insensitive match)
  svc.get_positions("MyBook")
  svc.get_trades(2)
  svc.place_bet("will-spain-win-the-2026-fifa-world-cup-963", "Yes", 1.0)
  svc.place_bet("…slug…", "Yes", 1.0, portfolio=2)     # debit portfolio 2 instead
  svc.close_position(<position_id>, portfolio=2)     # close a position on portfolio 2
  svc.close_position(<position_id>)        # sell all (default portfolio)
  svc.close_position(<position_id>, 0.5)   # sell part
  svc.close_position_settled(<id>, won=True)            # ended market you won ($1/share)
  svc.close_position_settled(<id>, won=False)           # ended market you lost ($0)
  svc.close_position_settled(<id>, won=True, portfolio=3)  # settle on another portfolio when svc defaults to 1

Run interactively from repo root:
  source venv/bin/activate
  python -i scripts/try_paper_trading.py
"""
)
