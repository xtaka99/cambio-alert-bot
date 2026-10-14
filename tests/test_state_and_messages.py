from cambio_alert.messages import build_alert, format_rate
from cambio_alert.rates import Quote
from cambio_alert.state import AlertState
from cambio_alert.targets import Target


def test_alerts_once_then_stays_quiet_then_rearms(tmp_path):
    path = tmp_path / "state.json"
    state = AlertState(path)
    assert state.should_alert("USD-BRL", True) is True       # first hit: alert
    assert state.should_alert("USD-BRL", True) is False      # still hit: quiet
    state.save()

    reloaded = AlertState(path)                              # survives a restart
    assert reloaded.should_alert("USD-BRL", True) is False
    assert reloaded.should_alert("USD-BRL", False) is False  # left range: re-arm
    assert reloaded.should_alert("USD-BRL", True) is True    # hit again: alert


def test_no_state_mode_alerts_every_time():
    state = AlertState(None)
    assert state.should_alert("USD-BRL", True)
    assert state.should_alert("USD-BRL", True)


def test_corrupted_state_file_does_not_crash(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("{not valid json")
    assert AlertState(path).should_alert("USD-BRL", True)


def test_format_rate_uses_more_decimals_for_small_rates():
    assert format_rate(0.03391) == "0.0339"
    assert format_rate(5.2) == "5.200"


def test_alert_text_in_both_languages():
    hit = [(Target("USD", "BRL", below=5.2, note="pay suppliers"),
            Quote("USD", "BRL", 5.15, "2026-09-17"))]
    en = build_alert(hit, "en")
    pt = build_alert(hit, "pt")
    assert "USD-BRL is at 5.150" in en and "pay suppliers" in en
    assert "Alerta de câmbio" in pt and "está em 5.150" in pt
