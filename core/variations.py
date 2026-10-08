"""Gera variações de username para investigação."""


def generate_variations(username: str) -> dict:
    """Retorna variações: leetspeak, com pontos, underscores, números."""
    base = username.lower()
    leet_map = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"}

    leet = "".join(leet_map.get(c, c) for c in base)
    leet_upper = "".join(leet_map.get(c, c).upper() if c in leet_map else c.upper() for c in base)

    variations = {
        "original": username,
        "lower": base,
        "upper": base.upper(),
        "leetspeak": leet,
        "leetspeak_upper": leet_upper,
        "with_dot": base.replace("_", ".").replace("-", "."),
        "with_underscore": base.replace(".", "_").replace("-", "_"),
        "with_dash": base.replace(".", "-").replace("_", "-"),
        "no_separator": base.replace("_", "").replace("-", "").replace(".", ""),
        "with_year_2024": f"{base}2024",
        "with_year_2025": f"{base}2025",
        "with_number": f"{base}1",
        "prefix_the": f"the{base}",
        "suffix_x": f"{base}x",
        "suffix_official": f"{base}_official",
    }
    return variations
