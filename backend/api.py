"""Rotas FastAPI."""
from __future__ import annotations

import asyncio
import json
import os
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse, Response
from sse_starlette.sse import EventSourceResponse

from backend.models import SearchRequest
from backend import history
from core.searcher import Searcher
from core.utils import valid_username, google_dorks, search_engine_links, gravatar_url
from core.variations import generate_variations
from core.exporters import to_json, to_csv, to_markdown, to_html
from sites.definitions import SITES, list_categories, get_sites
from core.logger import get_logger

router = APIRouter(prefix="/api")
log = get_logger()


@router.get("/health")
async def health():
    return {"status": "ok", "sites": len(SITES)}


@router.get("/sites")
async def sites():
    return {
        "categories": list_categories(),
        "sites": [
            {
                "name": s.name, "category": s.category, "icon": s.icon,
                "nsfw": s.nsfw, "verification": s.verification,
            }
            for s in SITES
        ],
    }


@router.get("/history")
async def get_history():
    return {"history": history.all()}


@router.get("/export/{search_id}")
async def export(search_id: str, format: str = "json"):
    entry = history.get(search_id)
    if not entry:
        raise HTTPException(404, "Busca não encontrada")
    fmt = format.lower()
    if fmt == "json":
        return Response(to_json(entry), media_type="application/json",
                        headers={"Content-Disposition": f"attachment; filename=osint_{search_id}.json"})
    if fmt == "csv":
        return Response(to_csv(entry), media_type="text/csv",
                        headers={"Content-Disposition": f"attachment; filename=osint_{search_id}.csv"})
    if fmt == "md":
        return Response(to_markdown(entry), media_type="text/markdown",
                        headers={"Content-Disposition": f"attachment; filename=osint_{search_id}.md"})
    if fmt == "html":
        return HTMLResponse(to_html(entry))
    raise HTTPException(400, "Formato inválido. Use json|csv|md|html")


@router.post("/search/stream")
async def search_stream(req: SearchRequest, request: Request):
    """Streaming SSE com resultados em tempo real."""
    if not valid_username(req.username):
        raise HTTPException(400, "Username inválido. Use apenas letras, números, . _ -")

    search_id = str(uuid.uuid4())[:8]
    searcher = Searcher(
        concurrency=int(os.getenv("OSINT_CONCURRENCY", "20")),
        timeout=float(os.getenv("OSINT_TIMEOUT", "10")),
        retries=int(os.getenv("OSINT_RETRIES", "2")),
        proxy=os.getenv("OSINT_PROXY") or None,
    )

    queue: asyncio.Queue = asyncio.Queue()
    collected: list[dict] = []

    async def on_result(r: dict):
        collected.append(r)
        await queue.put({"type": "result", "data": r})

    async def runner():
        try:
            await searcher.search(
                req.username, req.categories, req.include_nsfw, on_result=on_result
            )
            entry = _summarize(search_id, req.username, collected)
            history.add(entry)
            await queue.put({"type": "done", "data": entry})
        except Exception as e:
            log.error(f"Erro na busca: {e}")
            await queue.put({"type": "error", "data": str(e)})
        finally:
            await queue.put(None)

    async def event_stream() -> AsyncGenerator[dict, None]:
        # metadados extras
        yield {
            "event": "meta",
            "data": json.dumps({
                "search_id": search_id,
                "username": req.username,
                "variations": generate_variations(req.username),
                "dorks": google_dorks(req.username),
                "search_engines": search_engine_links(req.username),
                "gravatar": gravatar_url(req.username),
                "total_sites": len(get_sites(req.categories, req.include_nsfw)),
            }),
        }
        task = asyncio.create_task(runner())
        try:
            while True:
                if await request.is_disconnected():
                    task.cancel()
                    break
                item = await queue.get()
                if item is None:
                    break
                yield {"event": "message", "data": json.dumps(item)}
        finally:
            if not task.done():
                task.cancel()

    return EventSourceResponse(event_stream())


@router.post("/search")
async def search_sync(req: SearchRequest):
    """Busca síncrona (não streaming) — útil para CLI/API."""
    if not valid_username(req.username):
        raise HTTPException(400, "Username inválido")
    searcher = Searcher()
    results = await searcher.search(req.username, req.categories, req.include_nsfw)
    search_id = str(uuid.uuid4())[:8]
    entry = _summarize(search_id, req.username, results)
    history.add(entry)
    return entry


def _summarize(search_id: str, username: str, results: list[dict]) -> dict:
    found = sum(1 for r in results if r["status"] == "encontrado")
    nf = sum(1 for r in results if r["status"] == "não encontrado")
    err = sum(1 for r in results if r["status"] == "erro")
    return {
        "search_id": search_id,
        "username": username,
        "total": len(results),
        "found": found,
        "not_found": nf,
        "errors": err,
        "results": sorted(results, key=lambda r: (r["status"] != "encontrado", r["category"])),
    }
