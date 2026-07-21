def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def format_percentage(value: float) -> str:
    return f"{value:+.2f}%"


def get_market_from_symbol(symbol: str) -> str:
    if symbol.endswith(".DE"):
        return "EU"
    elif symbol.endswith(".AS"):
        return "EU"
    elif symbol.endswith(".PA"):
        return "EU"
    elif symbol.endswith(".L"):
        return "EU"
    elif symbol.endswith(".T"):
        return "AS"
    elif symbol.endswith(".HK"):
        return "AS"
    else:
        return "US"
