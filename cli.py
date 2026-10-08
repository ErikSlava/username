#!/usr/bin/env python3
"""Modo CLI — reutiliza o core de busca."""
import argparse
import asyncio
import json
import sys

from core.searcher import Searcher
from core.utils import valid_username
from core.exporters import to_markdown


async def main_async(args):
    if not valid_username(args.username):
        print("❌ Username inválido", file=sys.stderr)
        sys.exit(1)

    searcher = Searcher(concurrency=args.concurrency)

    def on_result(r):
        icon = {"encontrado": "✅", "não encontrado": "❌",
                "erro": "⚠️", "rate-limited": "🚫", "indeterminado": "❓"}.get(r["status"], "•")
        print(f"{icon} {r['site']:<28} {r['status']:<18} {r['confidence']}%  {r['elapsed_ms']}ms")
        return asyncio.sleep(0)

    print(f"🔍 Buscando '{args.username}' em várias plataformas...\n")
    results = await searcher.search(args.username, on_result=None)
    # reimprime organizado
    found = [r for r in results if r["status"] == "encontrado"]
    print(f"\n✅ {len(found)} encontrados de {len(results)} verificados.\n")
    for r in found:
        print(f"  • {r['site']:<25} {r['url']}")

    if args.output:
        summary = {
            "username": args.username, "total": len(results),
            "found": len(found),
            "not_found": sum(1 for r in results if r["status"] == "não encontrado"),
            "errors": sum(1 for r in results if r["status"] == "erro"),
            "results": results,
        }
        if args.output.endswith(".json"):
            open(args.output, "w").write(json.dumps(summary, indent=2, ensure_ascii=False))
        else:
            open(args.output, "w").write(to_markdown(summary))
        print(f"\n💾 Salvo em {args.output}")


def main():
    p = argparse.ArgumentParser(description="OSINT Username Finder CLI")
    p.add_argument("username", help="Username a investigar")
    p.add_argument("-c", "--concurrency", type=int, default=15)
    p.add_argument("-o", "--output", help="Arquivo de saída (.json ou .md)")
    args = p.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
