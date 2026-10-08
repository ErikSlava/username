"""
Motor de busca assíncrono com semáforo, retry, rotação de User-Agent.
Emite eventos via callback para permitir streaming (SSE).
"""

from __future__ import annotations

import asyncio
import random
import time
from typing import Awaitable, Callable

import httpx

from sites.definitions import SiteDefinition, get_sites
from core.verifiers import verify_site

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
]


class Searcher:
    """Executa buscas em paralelo com controle de concorrência."""

    def __init__(
        self,
        concurrency: int = 20,
        timeout: float = 10.0,
        retries: int = 2,
        proxy: str | None = None,
    ):
        self.concurrency = concurrency
        self.timeout = timeout
        self.retries = retries
        self.proxy = proxy
        self._sem = asyncio.Semaphore(concurrency)

    async def search(
        self,
        username: str,
        categories: list[str] | None = None,
        include_nsfw: bool = False,
        on_result: Callable[[dict], Awaitable[None]] | None = None,
    ) -> list[dict]:
        """
        Executa busca completa. Se `on_result` for passado, chama a cada site concluído
        (streaming em tempo real).
        """
        sites = get_sites(categories=categories, include_nsfw=include_nsfw)
        results: list[dict] = []

        transport = None
        client_kwargs = {
            "timeout": self.timeout,
            "follow_redirects": True,
            "verify": False,  # alguns sites têm certs esquisitos; ainda assim HTTPS
            "http2": False,
            "limits": httpx.Limits(max_connections=self.concurrency * 2),
        }
        if self.proxy:
            client_kwargs["proxies"] = self.proxy

        async with httpx.AsyncClient(**client_kwargs) as client:
            tasks = [
                self._run_one(client, site, username, on_result)
                for site in sites
            ]
            for coro in asyncio.as_completed(tasks):
                res = await coro
                results.append(res)

        return results

    async def _run_one(
        self,
        client: httpx.AsyncClient,
        site: SiteDefinition,
        username: str,
        on_result: Callable[[dict], Awaitable[None]] | None,
    ) -> dict:
        async with self._sem:
            start = time.monotonic()
            result = None
            for attempt in range(self.retries + 1):
                result = await verify_site(client, site, username)
                if result["status"] != "erro":
                    break
                if attempt < self.retries:
                    await asyncio.sleep(0.5 * (attempt + 1))

            result["elapsed_ms"] = int((time.monotonic() - start) * 1000)
            if on_result:
                try:
                    await on_result(result)
                except Exception:
                    pass
            return result


def search_sync(username: str, **kwargs) -> list[dict]:
    """Wrapper síncrono para uso em CLI."""
    return asyncio.run(Searcher().search(username, **kwargs))
