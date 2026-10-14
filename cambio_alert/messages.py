"""Builds the alert text, in English or Portuguese."""

from .rates import Quote
from .targets import Target

TEXT = {
    "en": {
        "title": "Exchange rate alert",
        "line": "{pair} is at {rate} (target {target})",
        "footer": "ECB reference rate from {date}. Your bank or card rate will be slightly higher.",
    },
    "pt": {
        "title": "Alerta de câmbio",
        "line": "{pair} está em {rate} (alvo {target})",
        "footer": "Taxa de referência do BCE de {date}. A taxa do banco ou cartão será um pouco maior.",
    },
}


def format_rate(rate: float) -> str:
    """Small rates (JPY-BRL is about 0.03) need more decimal places."""
    return f"{rate:.4f}" if rate < 1 else f"{rate:.3f}"


def build_alert(hits: list[tuple[Target, Quote]], language: str = "en") -> str:
    t = TEXT.get(language, TEXT["en"])
    lines = [t["title"]]
    for target, quote in hits:
        line = t["line"].format(pair=target.pair, rate=format_rate(quote.rate),
                                target=target.describe())
        if target.note:
            line += f" - {target.note}"
        lines.append("• " + line)
    lines.append(t["footer"].format(date=hits[0][1].date))
    return "\n".join(lines)
