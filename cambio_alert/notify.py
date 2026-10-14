"""Sends alert messages. Each notifier has one method: send(text).

Because they all share the same method, the rest of the program does not
care which one it is talking to. (This idea is called polymorphism.)
"""

import os

import requests

TIMEOUT_SECONDS = 15


class NotifyError(Exception):
    """Raised when a message could not be delivered."""


class ConsoleNotifier:
    """Prints to the terminal. Used for --dry-run and when nothing is set up."""

    name = "console"

    def send(self, text: str) -> None:
        print(text)


class DiscordNotifier:
    """Posts to a Discord channel through a webhook URL."""

    name = "discord"

    def __init__(self, webhook_url: str, session=requests):
        self.webhook_url = webhook_url
        self.session = session

    def send(self, text: str) -> None:
        try:
            r = self.session.post(self.webhook_url, json={"content": text},
                                  timeout=TIMEOUT_SECONDS)
            r.raise_for_status()
        except requests.RequestException as err:
            # Never print the webhook URL itself: it is a secret.
            raise NotifyError(f"Discord delivery failed: {type(err).__name__}") from err


class TelegramNotifier:
    """Sends a message through a Telegram bot."""

    name = "telegram"

    def __init__(self, bot_token: str, chat_id: str, session=requests):
        self.url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        self.chat_id = chat_id
        self.session = session

    def send(self, text: str) -> None:
        try:
            r = self.session.post(self.url, json={"chat_id": self.chat_id, "text": text},
                                  timeout=TIMEOUT_SECONDS)
            r.raise_for_status()
        except requests.RequestException as err:
            raise NotifyError(f"Telegram delivery failed: {type(err).__name__}") from err


def notifiers_from_env(env=os.environ) -> list:
    """Build notifiers from environment variables (loaded from the .env file).

    Secrets live in the environment, never in the code or in Git.
    """
    found = []
    if env.get("DISCORD_WEBHOOK_URL"):
        found.append(DiscordNotifier(env["DISCORD_WEBHOOK_URL"]))
    if env.get("TELEGRAM_BOT_TOKEN") and env.get("TELEGRAM_CHAT_ID"):
        found.append(TelegramNotifier(env["TELEGRAM_BOT_TOKEN"], env["TELEGRAM_CHAT_ID"]))
    return found or [ConsoleNotifier()]
