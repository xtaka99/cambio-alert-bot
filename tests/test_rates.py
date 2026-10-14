import pytest

from cambio_alert.rates import RateError, fetch_all, fetch_quotes

from .fakes import FakeSession


def test_fetch_quotes_parses_reply():
    session = FakeSession({"USD": {"BRL": 5.31, "JPY": 157.2}})
    quotes = fetch_quotes("USD", ["BRL"], session=session)
    assert len(quotes) == 1
    assert quotes[0].pair == "USD-BRL"
    assert quotes[0].rate == 5.31
    assert quotes[0].date == "2026-09-17"


def test_fetch_all_makes_one_call_per_base_currency():
    session = FakeSession({"USD": {"BRL": 5.31, "JPY": 157.2}, "EUR": {"BRL": 6.2}})
    result = fetch_all([("USD", "BRL"), ("USD", "JPY"), ("EUR", "BRL")], session=session)
    assert set(result) == {"USD-BRL", "USD-JPY", "EUR-BRL"}
    assert len(session.calls) == 2         # USD once, EUR once (not three calls)


def test_network_failure_becomes_rate_error():
    with pytest.raises(RateError):
        fetch_quotes("USD", ["BRL"], session=FakeSession(fail=True))


def test_http_error_becomes_rate_error():
    with pytest.raises(RateError):
        fetch_quotes("USD", ["BRL"], session=FakeSession({"USD": {"BRL": 5}}, status=500))


def test_empty_rates_becomes_rate_error():
    with pytest.raises(RateError):
        fetch_quotes("USD", ["XXX"], session=FakeSession({"USD": {"BRL": 5}}))
