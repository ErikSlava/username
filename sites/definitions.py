"""
Definições de sites suportados pela ferramenta OSINT.
Cada site usa a técnica de verificação mais confiável possível.

Tipos de verificação:
- status_code: 200 = existe, 404 = não existe
- text_presence: string presente indica existência
- text_absence: string presente indica NÃO existência (404 mascarado)
- json_field: consome API e verifica campo
- redirect_check: 302/301 indica existência (ou não)
- meta_tag: presença de <meta property="og:title"> etc.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SiteDefinition:
    name: str
    url_template: str
    category: str
    verification: str = "status_code"
    absence_strings: list = field(default_factory=list)
    presence_strings: list = field(default_factory=list)
    json_check: Optional[dict] = None          # ex: {"field": "login", "value_expected": True}
    headers: dict = field(default_factory=dict)
    delay: float = 0.0
    requires_method: str = "GET"
    post_payload_template: Optional[str] = None  # JSON com {username}
    nsfw: bool = False
    icon: str = "🌐"
    url_profile: Optional[str] = None          # template para link de perfil mostrado ao usuário


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,pt-BR;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


# =========================================================================
# REDES SOCIAIS
# =========================================================================
SITES = [
    SiteDefinition(
        name="Instagram",
        url_template="https://www.instagram.com/{username}/",
        url_profile="https://www.instagram.com/{username}/",
        category="rede_social",
        verification="text_absence",
        # Instagram devolve 200 mesmo para inexistentes; a string abaixo só aparece em 404 real
        absence_strings=['"Sorry, this page isn\'t available."', "Sorry, this page isn"],
        icon="📸",
    ),
    SiteDefinition(
        name="Twitter/X (via Nitter)",
        url_template="https://nitter.net/{username}",
        url_profile="https://x.com/{username}",
        category="rede_social",
        verification="text_absence",
        absence_strings=["User not found", "does not exist"],
        icon="🐦",
    ),
    SiteDefinition(
        name="TikTok",
        url_template="https://www.tiktok.com/@{username}",
        url_profile="https://www.tiktok.com/@{username}",
        category="rede_social",
        verification="text_absence",
        absence_strings=["Couldn't find this account", "Não foi possível encontrar esta conta"],
        icon="🎵",
    ),
    SiteDefinition(
        name="Reddit",
        url_template="https://www.reddit.com/user/{username}/about.json",
        url_profile="https://www.reddit.com/user/{username}",
        category="rede_social",
        verification="json_field",
        json_check={"field": "data.name", "must_exist": True, "suspended_field": "data.is_suspended"},
        headers={**DEFAULT_HEADERS, "Accept": "application/json"},
        icon="👽",
    ),
    SiteDefinition(
        name="Pinterest",
        url_template="https://www.pinterest.com/{username}/",
        url_profile="https://www.pinterest.com/{username}/",
        category="rede_social",
        verification="text_absence",
        absence_strings=["User not found", "isn't available"],
        icon="📌",
    ),
    SiteDefinition(
        name="Telegram",
        url_template="https://t.me/{username}",
        url_profile="https://t.me/{username}",
        category="rede_social",
        verification="text_presence",
        presence_strings=["tgme_page_title", "tgme_page_extra"],
        icon="✈️",
    ),
    SiteDefinition(
        name="YouTube",
        url_template="https://www.youtube.com/@{username}",
        url_profile="https://www.youtube.com/@{username}",
        category="rede_social",
        verification="status_code",  # 404 quando canal não existe
        icon="▶️",
    ),
    SiteDefinition(
        name="Tumblr",
        url_template="https://{username}.tumblr.com/",
        url_profile="https://{username}.tumblr.com/",
        category="rede_social",
        verification="status_code",
        icon="📓",
    ),
    SiteDefinition(
        name="Mastodon (mastodon.social)",
        url_template="https://mastodon.social/@{username}",
        url_profile="https://mastodon.social/@{username}",
        category="rede_social",
        verification="status_code",
        icon="🐘",
    ),
    SiteDefinition(
        name="VK",
        url_template="https://vk.com/{username}",
        url_profile="https://vk.com/{username}",
        category="rede_social",
        verification="text_absence",
        absence_strings=["Page not found", "Страница не найдена"],
        icon="🅥",
    ),

    # =====================================================================
    # DESENVOLVIMENTO / CÓDIGO
    # =====================================================================
    SiteDefinition(
        name="GitHub",
        url_template="https://api.github.com/users/{username}",
        url_profile="https://github.com/{username}",
        category="dev",
        verification="json_field",
        json_check={"field": "login", "must_exist": True},
        headers={**DEFAULT_HEADERS, "Accept": "application/vnd.github+json"},
        icon="🐙",
    ),
    SiteDefinition(
        name="GitLab",
        url_template="https://gitlab.com/api/v4/users?username={username}",
        url_profile="https://gitlab.com/{username}",
        category="dev",
        verification="json_field",
        json_check={"array_not_empty": True},
        headers={**DEFAULT_HEADERS, "Accept": "application/json"},
        icon="🦊",
    ),
    SiteDefinition(
        name="Bitbucket",
        url_template="https://api.bitbucket.org/2.0/users/{username}",
        url_profile="https://bitbucket.org/{username}/",
        category="dev",
        verification="status_code",
        headers={**DEFAULT_HEADERS, "Accept": "application/json"},
        icon="🪣",
    ),
    SiteDefinition(
        name="Dev.to",
        url_template="https://dev.to/api/users/by_username?url={username}",
        url_profile="https://dev.to/{username}",
        category="dev",
        verification="json_field",
        json_check={"field": "username", "must_exist": True},
        headers={**DEFAULT_HEADERS, "Accept": "application/json"},
        icon="👩‍💻",
    ),
    SiteDefinition(
        name="Medium",
        url_template="https://medium.com/@{username}",
        url_profile="https://medium.com/@{username}",
        category="dev",
        verification="status_code",
        icon="✍️",
    ),
    SiteDefinition(
        name="HackerNews",
        url_template="https://hacker-news.firebaseio.com/v0/user/{username}.json",
        url_profile="https://news.ycombinator.com/user?id={username}",
        category="dev",
        verification="json_field",
        json_check={"not_null": True},
        headers={**DEFAULT_HEADERS, "Accept": "application/json"},
        icon="🟠",
    ),
    SiteDefinition(
        name="Stack Overflow",
        url_template="https://stackoverflow.com/users/filter?search={username}",
        url_profile="https://stackoverflow.com/users/filter?search={username}",
        category="dev",
        verification="status_code",
        icon="📚",
    ),
    SiteDefinition(
        name="CodePen",
        url_template="https://codepen.io/{username}",
        url_profile="https://codepen.io/{username}",
        category="dev",
        verification="status_code",
        icon="🖊️",
    ),
    SiteDefinition(
        name="Replit",
        url_template="https://replit.com/@{username}",
        url_profile="https://replit.com/@{username}",
        category="dev",
        verification="status_code",
        icon="🔁",
    ),
    SiteDefinition(
        name="Kaggle",
        url_template="https://www.kaggle.com/{username}",
        url_profile="https://www.kaggle.com/{username}",
        category="dev",
        verification="status_code",
        icon="📊",
    ),
    SiteDefinition(
        name="Pastebin",
        url_template="https://pastebin.com/u/{username}",
        url_profile="https://pastebin.com/u/{username}",
        category="dev",
        verification="text_absence",
        absence_strings=["Not Found", "not found"],
        icon="📋",
    ),
    SiteDefinition(
        name="Keybase",
        url_template="https://keybase.io/_/api/1.0/user/lookup.json?username={username}",
        url_profile="https://keybase.io/{username}",
        category="dev",
        verification="json_field",
        json_check={"field": "them", "not_null": True},
        headers={**DEFAULT_HEADERS, "Accept": "application/json"},
        icon="🔑",
    ),
    SiteDefinition(
        name="HackerRank",
        url_template="https://www.hackerrank.com/{username}",
        url_profile="https://www.hackerrank.com/{username}",
        category="dev",
        verification="text_absence",
        absence_strings=["404", "not found"],
        icon="🟢",
    ),
    SiteDefinition(
        name="LeetCode",
        url_template="https://leetcode.com/{username}/",
        url_profile="https://leetcode.com/{username}/",
        category="dev",
        verification="status_code",
        icon="🧩",
    ),
    SiteDefinition(
        name="Docker Hub",
        url_template="https://hub.docker.com/v2/users/{username}/",
        url_profile="https://hub.docker.com/u/{username}",
        category="dev",
        verification="status_code",
        headers={**DEFAULT_HEADERS, "Accept": "application/json"},
        icon="🐳",
    ),

    # =====================================================================
    # GAMING
    # =====================================================================
    SiteDefinition(
        name="Steam",
        url_template="https://steamcommunity.com/id/{username}",
        url_profile="https://steamcommunity.com/id/{username}",
        category="gaming",
        verification="text_absence",
        absence_strings=["The specified profile could not be found"],
        icon="🎮",
    ),
    SiteDefinition(
        name="Roblox",
        url_template="https://users.roblox.com/v1/usernames/users",
        url_profile="https://www.roblox.com/search/users?keyword={username}",
        category="gaming",
        verification="json_field",
        requires_method="POST",
        post_payload_template='{"usernames": ["{username}"], "excludeBannedUsers": false}',
        json_check={"field": "data", "array_not_empty": True},
        headers={**DEFAULT_HEADERS, "Content-Type": "application/json", "Accept": "application/json"},
        icon="🧱",
    ),
    SiteDefinition(
        name="Twitch",
        url_template="https://www.twitch.tv/{username}",
        url_profile="https://www.twitch.tv/{username}",
        category="gaming",
        verification="text_absence",
        absence_strings=["Sorry. Unless you've got a time machine", "content is unavailable"],
        icon="🟣",
    ),
    SiteDefinition(
        name="Xbox Gamertag",
        url_template="https://xboxgamertag.com/search/{username}",
        url_profile="https://xboxgamertag.com/search/{username}",
        category="gaming",
        verification="status_code",
        icon="🎯",
    ),
    SiteDefinition(
        name="PSN Profiles",
        url_template="https://psnprofiles.com/{username}",
        url_profile="https://psnprofiles.com/{username}",
        category="gaming",
        verification="status_code",
        icon="🎮",
    ),
    SiteDefinition(
        name="Epic Games (Fortnite Tracker)",
        url_template="https://fortnitetracker.com/profile/all/{username}",
        url_profile="https://fortnitetracker.com/profile/all/{username}",
        category="gaming",
        verification="status_code",
        icon="🚀",
    ),
    SiteDefinition(
        name="Chess.com",
        url_template="https://api.chess.com/pub/player/{username}",
        url_profile="https://www.chess.com/member/{username}",
        category="gaming",
        verification="json_field",
        json_check={"field": "username", "must_exist": True},
        headers={**DEFAULT_HEADERS, "Accept": "application/json"},
        icon="♟️",
    ),
    SiteDefinition(
        name="Lichess",
        url_template="https://lichess.org/api/user/{username}",
        url_profile="https://lichess.org/@/{username}",
        category="gaming",
        verification="status_code",
        headers={**DEFAULT_HEADERS, "Accept": "application/json"},
        icon="♜",
    ),

    # =====================================================================
    # STREAMING / MÚSICA
    # =====================================================================
    SiteDefinition(
        name="Spotify",
        url_template="https://open.spotify.com/user/{username}",
        url_profile="https://open.spotify.com/user/{username}",
        category="streaming",
        verification="status_code",
        icon="🟢",
    ),
    SiteDefinition(
        name="SoundCloud",
        url_template="https://soundcloud.com/{username}",
        url_profile="https://soundcloud.com/{username}",
        category="streaming",
        verification="status_code",
        icon="☁️",
    ),
    SiteDefinition(
        name="Bandcamp",
        url_template="https://{username}.bandcamp.com",
        url_profile="https://{username}.bandcamp.com",
        category="streaming",
        verification="status_code",
        icon="🎼",
    ),
    SiteDefinition(
        name="Mixcloud",
        url_template="https://www.mixcloud.com/{username}/",
        url_profile="https://www.mixcloud.com/{username}/",
        category="streaming",
        verification="status_code",
        icon="🎧",
    ),
    SiteDefinition(
        name="Vimeo",
        url_template="https://vimeo.com/{username}",
        url_profile="https://vimeo.com/{username}",
        category="streaming",
        verification="status_code",
        icon="🎬",
    ),

    # =====================================================================
    # PROFISSIONAL / PORTFÓLIO
    # =====================================================================
    SiteDefinition(
        name="LinkedIn",
        url_template="https://www.linkedin.com/in/{username}",
        url_profile="https://www.linkedin.com/in/{username}",
        category="profissional",
        verification="status_code",
        # LinkedIn bloqueia muito; marcar como indeterminado quando 999/403
        icon="💼",
    ),
    SiteDefinition(
        name="Behance",
        url_template="https://www.behance.net/{username}",
        url_profile="https://www.behance.net/{username}",
        category="profissional",
        verification="status_code",
        icon="🎨",
    ),
    SiteDefinition(
        name="Dribbble",
        url_template="https://dribbble.com/{username}",
        url_profile="https://dribbble.com/{username}",
        category="profissional",
        verification="status_code",
        icon="🏀",
    ),
    SiteDefinition(
        name="About.me",
        url_template="https://about.me/{username}",
        url_profile="https://about.me/{username}",
        category="profissional",
        verification="status_code",
        icon="👤",
    ),
    SiteDefinition(
        name="AngelList/Wellfound",
        url_template="https://wellfound.com/u/{username}",
        url_profile="https://wellfound.com/u/{username}",
        category="profissional",
        verification="status_code",
        icon="👼",
    ),

    # =====================================================================
    # CROWDFUNDING / APOIO
    # =====================================================================
    SiteDefinition(
        name="Patreon",
        url_template="https://www.patreon.com/{username}",
        url_profile="https://www.patreon.com/{username}",
        category="apoio",
        verification="status_code",
        icon="🎗️",
    ),
    SiteDefinition(
        name="Ko-fi",
        url_template="https://ko-fi.com/{username}",
        url_profile="https://ko-fi.com/{username}",
        category="apoio",
        verification="status_code",
        icon="☕",
    ),
    SiteDefinition(
        name="Buy Me a Coffee",
        url_template="https://www.buymeacoffee.com/{username}",
        url_profile="https://www.buymeacoffee.com/{username}",
        category="apoio",
        verification="status_code",
        icon="🍵",
    ),

    # =====================================================================
    # LINK AGGREGATORS
    # =====================================================================
    SiteDefinition(
        name="Linktree",
        url_template="https://linktr.ee/{username}",
        url_profile="https://linktr.ee/{username}",
        category="links",
        verification="status_code",
        icon="🌳",
    ),
    SiteDefinition(
        name="Carrd",
        url_template="https://{username}.carrd.co",
        url_profile="https://{username}.carrd.co",
        category="links",
        verification="status_code",
        icon="🃏",
    ),

    # =====================================================================
    # FÓRUNS
    # =====================================================================
    SiteDefinition(
        name="Disqus",
        url_template="https://disqus.com/by/{username}/",
        url_profile="https://disqus.com/by/{username}/",
        category="forum",
        verification="status_code",
        icon="💬",
    ),

    # =====================================================================
    # NSFW (desativados por padrão)
    # =====================================================================
    SiteDefinition(
        name="OnlyFans",
        url_template="https://onlyfans.com/{username}",
        url_profile="https://onlyfans.com/{username}",
        category="nsfw",
        verification="status_code",
        nsfw=True,
        icon="🔞",
    ),
    SiteDefinition(
        name="Fansly",
        url_template="https://fansly.com/{username}",
        url_profile="https://fansly.com/{username}",
        category="nsfw",
        verification="status_code",
        nsfw=True,
        icon="🔞",
    ),
]


def get_sites(categories: list[str] | None = None, include_nsfw: bool = False) -> list[SiteDefinition]:
    """Filtra sites por categoria e flag NSFW."""
    out = []
    for s in SITES:
        if s.nsfw and not include_nsfw:
            continue
        if categories and s.category not in categories:
            continue
        out.append(s)
    return out


def list_categories() -> list[str]:
    """Retorna lista de categorias únicas (sem NSFW)."""
    return sorted({s.category for s in SITES if not s.nsfw})
