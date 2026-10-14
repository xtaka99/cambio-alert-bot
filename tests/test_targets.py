import json

import pytest

from cambio_alert.targets import Target, load_targets, parse_pair


def test_parse_pair_accepts_common_formats():
    assert parse_pair("usd-brl") == ("USD", "BRL")
    assert parse_pair("JPY/BRL") == ("JPY", "BRL")


@pytest.mark.parametrize("bad", ["USDBRL", "US-BRL", "USD-BRL-EUR", "123-BRL", ""])
def test_parse_pair_rejects_bad_input(bad):
    with pytest.raises(ValueError):
        parse_pair(bad)


def test_below_target():
    t = Target("USD", "BRL", below=5.20)
    assert t.is_hit(5.19)
    assert t.is_hit(5.20)          # exactly on target counts
    assert not t.is_hit(5.21)


def test_above_target():
    t = Target("USD", "JPY", above=158)
    assert t.is_hit(160)
    assert not t.is_hit(150)


def test_band_target_hits_on_either_side():
    t = Target("USD", "BRL", below=5.0, above=6.0)
    assert t.is_hit(4.9) and t.is_hit(6.1)
    assert not t.is_hit(5.5)


def test_load_targets_requires_a_threshold(tmp_path):
    f = tmp_path / "t.json"
    f.write_text(json.dumps({"targets": [{"pair": "USD-BRL"}]}))
    with pytest.raises(ValueError):
        load_targets(f)


def test_shipped_example_config_is_valid():
    assert len(load_targets("config/targets.json")) >= 1
