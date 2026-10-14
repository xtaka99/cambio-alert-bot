"""Command-line interface.

    python -m cambio_alert rates            show current rates for your targets
    python -m cambio_alert check            check targets and send alerts
    python -m cambio_alert check --dry-run  check, but only print (send nothing)
"""

import argparse
import sys

from dotenv import load_dotenv

from .history import append_history
from .messages import build_alert, format_rate
from .notify import ConsoleNotifier, NotifyError, notifiers_from_env
from .rates import RateError, fetch_all
from .state import AlertState
from .targets import load_targets


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cambio_alert",
                                     description="Exchange-rate alert bot.")
    parser.add_argument("--targets", default="config/targets.json")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("rates", help="print current rates")

    check = sub.add_parser("check", help="check targets and alert on hits")
    check.add_argument("--dry-run", action="store_true",
                       help="print alerts instead of sending them")
    check.add_argument("--no-state", action="store_true",
                       help="alert on every hit (do not remember past alerts)")
    check.add_argument("--state-file", default="alert_state.json")
    check.add_argument("--history", default="rates_history.csv",
                       help="CSV file to log rates into ('' to disable)")
    check.add_argument("--language", choices=["en", "pt"], default="en")
    return parser


def run(argv: list[str] | None = None, session=None) -> int:
    """Returns an exit code: 0 ok, 1 error. `session` is for tests only."""
    args = build_parser().parse_args(argv)
    load_dotenv()                                    # reads secrets from .env

    try:
        targets = load_targets(args.targets)
        pairs = [(t.base, t.quote) for t in targets]
        quotes = fetch_all(pairs, session=session) if session else fetch_all(pairs)
    except (FileNotFoundError, ValueError, KeyError, RateError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    if args.command == "rates":
        for t in targets:
            q = quotes.get(t.pair)
            shown = format_rate(q.rate) if q else "n/a"
            print(f"{t.pair:<10}{shown:>10}   target {t.describe()}")
        return 0

    # ---- check ----
    if args.history:
        append_history(args.history, list(quotes.values()))

    state = AlertState(None if (args.no_state or args.dry_run) else args.state_file)
    hits = []
    for t in targets:
        q = quotes.get(t.pair)
        if q is None:
            print(f"Warning: no rate returned for {t.pair}", file=sys.stderr)
            continue
        if state.should_alert(t.pair, t.is_hit(q.rate)):
            hits.append((t, q))
    state.save()

    if not hits:
        print("No new targets hit.")
        return 0

    text = build_alert(hits, args.language)
    notifiers = [ConsoleNotifier()] if args.dry_run else notifiers_from_env()
    failed = False
    for n in notifiers:
        try:
            n.send(text)
            if n.name != "console":
                print(f"Alert sent via {n.name}.")
        except NotifyError as err:
            print(f"Error: {err}", file=sys.stderr)
            failed = True
    return 1 if failed else 0
