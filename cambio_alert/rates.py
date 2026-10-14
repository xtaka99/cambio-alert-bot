"""Fetches exchange rates from the Frankfurter API (https://frankfurter.dev).

Frankfurter is free, needs no API key, and publishes European Central Bank
reference rates once per working day. These are reference rates: the rate a
bank or card actually charges will be a little worse (spread + fees).
"""

from dataclasses import dataclass

import requests

API_URL = "https://api.frankfurter.dev/v1/latest"
TIMEOUT_SECONDS = 15


class RateError(Exception):
    """Raised when rates cannot be fetched or the reply makes no sense."""


@dataclass(frozen=True)
class Quote:
    base: str
    quote: str
    rate: float      # how many `quote` units one `base` unit costs
    date: str        # the day the rate was published (YYYY-MM-DD)

    @property
    def pair(self) -> str:
        return f"{self.base}-{self.quote}"


def fetch_quotes(base: str, quotes: list[str], session=requests) -> list[Quote]:
    """One API call returns every requested quote currency for one base.

    `session` exists so tests can pass in a fake object instead of hitting
    the real internet. In normal use it is simply the `requests` library.
    """
    params = {"base": base, "symbols": ",".join(sorted(set(quotes)))}
    try:
        response = session.get(API_URL, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as err:
        raise RateError(f"Could not reach the rates API: {err}") from err
    except ValueError as err:                       # reply was not valid JSON
        raise RateError("Rates API returned something that is not JSON") from err

    rates = data.get("rates")
    if not isinstance(rates, dict) or not rates:
        raise RateError(f"Rates API reply has no rates for {base}: {data}")

    return [
        Quote(base=base, quote=code, rate=float(value), date=data.get("date", ""))
        for code, value in rates.items()
    ]


def fetch_all(pairs: list[tuple[str, str]], session=requests) -> dict[str, Quote]:
    """Fetch many pairs using as few API calls as possible (one per base)."""
    by_base: dict[str, list[str]] = {}
    for base, quote in pairs:
        by_base.setdefault(base, []).append(quote)

    result: dict[str, Quote] = {}
    for base, quote_codes in by_base.items():
        for q in fetch_quotes(base, quote_codes, session=session):
            result[q.pair] = q
    return result
