import json

import pytest

from cambio_alert.cli import run
from cambio_alert.notify import (ConsoleNotifier, DiscordNotifier, NotifyError,
                                 TelegramNotifier, notifiers_from_env)

from .fakes import FakeSession


def test_discord_posts_content():
    session = FakeSession()
    DiscordNotifier("https://example.test/hook", session=session).send("hello")
    method, url, body = session.calls[0]
    assert (method, body) == ("POST", {"content": "hello"})


def test_telegram_posts_chat_id_and_text():
    session = FakeSession()
    TelegramNotifier("TOKEN", "42", session=session).send("hello")
    _, url, body = session.calls[0]
    assert url.endswith("/botTOKEN/sendMessage")
    assert body == {"chat_id": "42", "text": "hello"}


def test_delivery_failure_hides_the_secret_url():
    notifier = DiscordNotifier("https://example.test/SECRET", session=FakeSession(fail=True))
    with pytest.raises(NotifyError) as info:
        notifier.send("hello")
    assert "SECRET" not in str(info.value)


def test_env_selects_notifiers():
    assert isinstance(notifiers_from_env({})[0], ConsoleNotifier)
    both = notifiers_from_env({"DISCORD_WEBHOOK_URL": "x", "TELEGRAM_BOT_TOKEN": "t",
                               "TELEGRAM_CHAT_ID": "1"})
    assert [n.name for n in both] == ["discord", "telegram"]


def test_check_dry_run_prints_only_the_hit(tmp_path, capsys):
    targets = tmp_path / "targets.json"
    targets.write_text(json.dumps({"targets": [
        {"pair": "USD-BRL", "below": 5.20},
        {"pair": "EUR-BRL", "below": 6.00},
    ]}))
    session = FakeSession({"USD": {"BRL": 5.10}, "EUR": {"BRL": 6.40}})
    code = run(["--targets", str(targets), "check", "--dry-run", "--history", ""],
               session=session)
    out = capsys.readouterr().out
    assert code == 0
    assert "USD-BRL" in out and "EUR-BRL" not in out


def test_check_reports_api_failure(tmp_path, capsys):
    targets = tmp_path / "targets.json"
    targets.write_text(json.dumps({"targets": [{"pair": "USD-BRL", "below": 5.2}]}))
    code = run(["--targets", str(targets), "check", "--dry-run", "--history", ""],
               session=FakeSession(fail=True))
    assert code == 1
    assert "Could not reach" in capsys.readouterr().err


def test_history_file_is_written(tmp_path):
    targets = tmp_path / "targets.json"
    targets.write_text(json.dumps({"targets": [{"pair": "USD-BRL", "below": 1}]}))
    history = tmp_path / "h.csv"
    run(["--targets", str(targets), "check", "--dry-run", "--history", str(history)],
        session=FakeSession({"USD": {"BRL": 5.10}}))
    rows = history.read_text().strip().splitlines()
    assert rows[0].startswith("checked_at_utc") and "USD-BRL" in rows[1]
