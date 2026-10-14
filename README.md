# cambio-alert-bot

![tests](https://github.com/xtaka99/cambio-alert-bot/actions/workflows/tests.yml/badge.svg)

A small bot that watches exchange rates and sends a **Discord or Telegram alert
when a rate hits a target you set**. "Câmbio" is Portuguese for exchange rate.

My family's import business buys stock in USD, JPY, EUR, CNY and HKD and sells
in BRL. A few cents of movement on the day a supplier gets paid changes the
margin on a whole shipment. Instead of checking rates by hand, this bot checks
them every weekday and only speaks up when it matters.

## What it does

- Pulls rates from the free [Frankfurter API](https://frankfurter.dev) (European Central Bank reference rates, no API key)
- Checks any number of targets: `below`, `above`, or both
- Sends alerts to **Discord** (webhook) and/or **Telegram** (bot), in English or Portuguese
- **Does not spam**: alerts once when a target is hit, stays quiet while it remains hit, re-arms when the rate leaves the range
- Logs every reading to `rates_history.csv` for charting later
- Runs three ways: by hand, on a Linux `cron` schedule, or **free on GitHub Actions** with no computer on

## Example

```
$ python -m cambio_alert rates
USD-BRL        5.312   target <= 5.2
JPY-BRL       0.0339   target <= 0.034
EUR-BRL        6.214   target <= 6
USD-JPY      156.700   target >= 158

$ python -m cambio_alert check --dry-run --language pt
Alerta de câmbio
• JPY-BRL está em 0.0339 (alvo <= 0.034) - good day for Japan orders
Taxa de referência do BCE de 2026-09-17. A taxa do banco ou cartão será um pouco maior.
```

## Setup

Requires Python 3.10+.

```bash
git clone https://github.com/xtaka99/cambio-alert-bot.git
cd cambio-alert-bot
pip install -r requirements.txt
python -m cambio_alert rates
```

1. Edit `config/targets.json` with the pairs and thresholds you care about.
2. Copy `.env.example` to `.env` and paste your Discord webhook URL and/or Telegram bot details.
3. Test without sending anything: `python -m cambio_alert check --dry-run`
4. Run for real: `python -m cambio_alert check`

`.env` is listed in `.gitignore`. A webhook URL or bot token is a password:
anyone who has it can post as the bot, so it must never be committed.

## Scheduling

**Linux cron** (every weekday at 13:00):

```
0 13 * * 1-5  cd /home/you/cambio-alert-bot && /usr/bin/python3 -m cambio_alert check >> bot.log 2>&1
```

**GitHub Actions** (no server needed): `.github/workflows/daily-check.yml` runs
the bot every weekday. Add your webhook/token under
*Settings > Secrets and variables > Actions* and it starts working. The
*Actions* tab also has a "Run workflow" button for manual runs.

## How it works

| File | Job |
|---|---|
| `cambio_alert/targets.py` | `Target` dataclass, pair validation, loads `targets.json` |
| `cambio_alert/rates.py` | Calls the API, one request per base currency, turns failures into a clear `RateError` |
| `cambio_alert/state.py` | Remembers active alerts in a JSON file so the bot alerts once per event |
| `cambio_alert/notify.py` | Discord, Telegram and console notifiers sharing one `send()` method |
| `cambio_alert/messages.py` | Builds the alert text (EN/PT) |
| `cambio_alert/history.py` | Appends readings to a CSV log |
| `cambio_alert/cli.py` | `argparse` commands tying it all together |
| `tests/` | 28 pytest tests. HTTP is faked, so tests are fast and never touch the internet |

## Limits worth knowing

Frankfurter publishes **reference rates once per working day** (around 16:00
CET). They are not live trading quotes, and the rate a bank or card charges
includes a spread and, in Brazil, IOF tax. The bot is a signal for *when to
look*, not a quote.

## What I learned

- Calling a REST API with `requests`, with timeouts and error handling
- Keeping secrets out of source control with `.env` files and GitHub Secrets
- Dependency injection: passing a fake `session` into functions so tests need no network
- Persisting state between runs to make alerts idempotent
- Scheduling jobs with cron and with a GitHub Actions `schedule` trigger

## License

MIT
