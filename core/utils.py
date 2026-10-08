"""Utilidades diversas: hash Gravatar, geração de dorks, links de busca."""

import hashlib
import re


USERNAME_RE = re.compile(r"^[A-Za-z0-9._\-]{2,40}$")


def valid_username(username: str) -> bool:
    """Valida caracteres permitidos."""
    return bool(USERNAME_RE.match(username or ""))


def gravatar_hash(username: str) -> str:
    """Hash MD5 do e-mail/username para consulta ao Gravatar."""
    return hashlib.md5(username.strip().lower().encode()).hexdigest()


def gravatar_url(username: str) -> str:
    return f"https://www.gravatar.com/avatar/{gravatar_hash(username)}?d=404"


def google_dorks(username: str) -> list[str]:
    """Dorks prontos para uso investigativo."""
    return [
        f'"{username}"',
        f'site:instagram.com "{username}"',
        f'site:twitter.com "{username}"',
        f'site:facebook.com "{username}"',
        f'site:linkedin.com "{username}"',
        f'site:github.com "{username}"',
        f'site:reddit.com "{username}"',
        f'"{username}" email',
        f'"{username}" filetype:pdf',
        f'inurl:"{username}"',
    ]


def search_engine_links(username: str) -> dict:
    """Links diretos para buscadores."""
    from urllib.parse import quote_plus
    q = quote_plus(f'"{username}"')
    return {
        "Google": f"https://www.google.com/search?q={q}",
        "Bing": f"https://www.bing.com/search?q={q}",
        "DuckDuckGo": f"https://duckduckgo.com/?q={q}",
        "Yandex": f"https://yandex.com/search/?text={q}",
    }
