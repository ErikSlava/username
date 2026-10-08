"""
Verificadores por tipo. Cada função recebe o cliente httpx e a SiteDefinition
e devolve um dict com status, confidence e detalhes.
"""

from __future__ import annotations

import json
from typing import Any

import httpx


def _deep_get(obj: Any, path: str) -> Any:
    """Acessa campo aninhado tipo 'data.name' em dict."""
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


async def verify_site(client: httpx.AsyncClient, site, username: str) -> dict:
    """Executa a verificação conforme o tipo definido no site."""
    url = site.url_template.format(username=username)
    method = site.requires_method.upper()

    headers = {**site.headers} or {}
    if not headers:
        from sites.definitions import DEFAULT_HEADERS
        headers = {**DEFAULT_HEADERS}

    payload = None
    if method == "POST" and site.post_payload_template:
        payload = json.loads(site.post_payload_template.format(username=username))

    result = {
        "site": site.name,
        "category": site.category,
        "url": site.url_profile.format(username=username) if site.url_profile else url,
        "status": "indeterminado",
        "confidence": 0,
        "detail": "",
        "icon": site.icon,
        "http_status": None,
    }

    try:
        if method == "POST":
            resp = await client.post(url, headers=headers, content=json.dumps(payload), timeout=10)
        else:
            resp = await client.get(url, headers=headers, timeout=10, follow_redirects=True)

        result["http_status"] = resp.status_code
        return _classify(site, resp, result)

    except httpx.TimeoutException:
        result["status"] = "erro"
        result["detail"] = "Timeout"
        return result
    except httpx.HTTPError as e:
        result["status"] = "erro"
        result["detail"] = f"HTTP error: {e.__class__.__name__}"
        return result
    except Exception as e:
        result["status"] = "erro"
        result["detail"] = f"Erro: {e}"
        return result


def _classify(site, resp: httpx.Response, result: dict) -> dict:
    """Classifica com base no tipo de verificação do site."""

    # Rate limit / bloqueio genérico
    if resp.status_code in (429, 999):
        result["status"] = "rate-limited"
        result["detail"] = f"HTTP {resp.status_code}"
        result["confidence"] = 0
        return result

    v = site.verification

    if v == "status_code":
        if resp.status_code == 200:
            result["status"] = "encontrado"
            result["confidence"] = 85
            result["detail"] = "HTTP 200"
        elif resp.status_code == 404:
            result["status"] = "não encontrado"
            result["confidence"] = 95
            result["detail"] = "HTTP 404"
        elif resp.status_code in (401, 403):
            result["status"] = "indeterminado"
            result["confidence"] = 20
            result["detail"] = f"Bloqueado HTTP {resp.status_code}"
        else:
            result["status"] = "indeterminado"
            result["confidence"] = 30
            result["detail"] = f"HTTP {resp.status_code}"
        return result

    if v == "text_absence":
        text = resp.text
        for s in site.absence_strings:
            if s.lower() in text.lower():
                result["status"] = "não encontrado"
                result["confidence"] = 90
                result["detail"] = f"Marcador de ausência: '{s[:40]}'"
                return result
        if resp.status_code == 200:
            result["status"] = "encontrado"
            result["confidence"] = 80
            result["detail"] = "HTTP 200 sem marcador de ausência"
        elif resp.status_code == 404:
            result["status"] = "não encontrado"
            result["confidence"] = 90
            result["detail"] = "HTTP 404"
        else:
            result["status"] = "indeterminado"
            result["confidence"] = 30
            result["detail"] = f"HTTP {resp.status_code}"
        return result

    if v == "text_presence":
        text = resp.text
        for s in site.presence_strings:
            if s.lower() in text.lower():
                result["status"] = "encontrado"
                result["confidence"] = 90
                result["detail"] = f"Marcador encontrado: '{s[:40]}'"
                return result
        if resp.status_code == 404:
            result["status"] = "não encontrado"
            result["confidence"] = 90
            result["detail"] = "HTTP 404"
        else:
            result["status"] = "não encontrado"
            result["confidence"] = 75
            result["detail"] = "Marcador de existência ausente"
        return result

    if v == "json_field":
        try:
            data = resp.json()
        except Exception:
            result["status"] = "indeterminado"
            result["confidence"] = 10
            result["detail"] = "Resposta não-JSON"
            return result

        check = site.json_check or {}

        # Caso array_not_empty (ex: GitLab, Roblox)
        if check.get("array_not_empty"):
            # Pode ser lista direta ou dentro de campo
            arr = data
            if check.get("field"):
                arr = _deep_get(data, check["field"]) or []
            if isinstance(arr, list) and len(arr) > 0:
                result["status"] = "encontrado"
                result["confidence"] = 95
                result["detail"] = f"{len(arr)} item(ns)"
            else:
                result["status"] = "não encontrado"
                result["confidence"] = 90
                result["detail"] = "Array vazio"
            return result

        # Caso campo específico
        if check.get("field"):
            val = _deep_get(data, check["field"])
            suspended = check.get("suspended_field")
            if suspended and _deep_get(data, suspended):
                result["status"] = "não encontrado"
                result["confidence"] = 90
                result["detail"] = "Conta suspensa"
                return result
            if val not in (None, "", [], {}):
                result["status"] = "encontrado"
                result["confidence"] = 95
                result["detail"] = f"{check['field']} = {str(val)[:50]}"
                return result
            result["status"] = "não encontrado"
            result["confidence"] = 85
            result["detail"] = f"Campo '{check['field']}' ausente"
            return result

        if check.get("not_null"):
            if data:
                result["status"] = "encontrado"
                result["confidence"] = 90
                result["detail"] = "JSON não-nulo"
            else:
                result["status"] = "não encontrado"
                result["confidence"] = 85
                result["detail"] = "JSON nulo"
            return result

    if v == "meta_tag":
        text = resp.text
        if "<meta" in text and ("og:title" in text or "twitter:title" in text):
            result["status"] = "encontrado"
            result["confidence"] = 75
            result["detail"] = "Meta tag presente"
        else:
            result["status"] = "não encontrado"
            result["confidence"] = 70
            result["detail"] = "Meta tag ausente"
        return result

    # fallback
    result["status"] = "indeterminado"
    result["detail"] = "Verificação não implementada"
    return result
