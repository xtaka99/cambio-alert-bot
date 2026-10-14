"""Fake HTTP objects so tests never touch the real internet.

Tests that depend on a live website are slow and fail randomly. Instead we
hand the code a fake `session` that returns whatever we tell it to.
"""

import requests


class FakeResponse:
    def __init__(self, payload=None, status=200):
        self.payload = payload
        self.status = status

    def raise_for_status(self):
        if self.status >= 400:
            raise requests.HTTPError(f"status {self.status}")

    def json(self):
        if self.payload is None:
            raise ValueError("not json")
        return self.payload


class FakeSession:
    """Pretends to be the `requests` library. Records every call it receives."""

    def __init__(self, rates_by_base=None, status=200, fail=False):
        self.rates_by_base = rates_by_base or {}
        self.status = status
        self.fail = fail
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append(("GET", url, params))
        if self.fail:
            raise requests.ConnectionError("no internet")
        base = params["base"]
        wanted = params["symbols"].split(",")
        rates = {c: v for c, v in self.rates_by_base.get(base, {}).items() if c in wanted}
        return FakeResponse({"base": base, "date": "2026-09-17", "rates": rates},
                            self.status)

    def post(self, url, json=None, timeout=None):
        self.calls.append(("POST", url, json))
        if self.fail:
            raise requests.ConnectionError("no internet")
        return FakeResponse({}, self.status)
