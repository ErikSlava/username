"""Exportação de resultados em JSON, CSV, Markdown, HTML."""
import csv
import io
import json
from datetime import datetime


def to_json(results: dict) -> str:
    return json.dumps(results, indent=2, ensure_ascii=False)


def to_csv(results: dict) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Site", "Categoria", "Status", "Confiança", "URL", "HTTP", "Detalhe", "ms"])
    for r in results.get("results", []):
        w.writerow([
            r.get("site"), r.get("category"), r.get("status"),
            r.get("confidence"), r.get("url"), r.get("http_status"),
            r.get("detail", ""), r.get("elapsed_ms", ""),
        ])
    return buf.getvalue()


def to_markdown(results: dict) -> str:
    lines = [
        f"# Relatório OSINT — `{results.get('username')}`",
        f"\n_Gerado em {datetime.utcnow().isoformat()}Z_",
        f"\n**Total verificado:** {results.get('total', 0)}  ",
        f"**Encontrados:** {results.get('found', 0)}  ",
        f"**Não encontrados:** {results.get('not_found', 0)}  ",
        f"**Erros:** {results.get('errors', 0)}  ",
        "\n## Resultados\n",
        "| Site | Categoria | Status | Confiança | Link |",
        "|---|---|---|---|---|",
    ]
    for r in results.get("results", []):
        link = f"[{r['url']}]({r['url']})" if r.get("status") == "encontrado" else "-"
        lines.append(f"| {r.get('site')} | {r.get('category')} | {r.get('status')} | {r.get('confidence')} | {link} |")
    lines.append("\n---\n_Gerado por OSINT Username Finder — uso ético apenas._")
    return "\n".join(lines)


def to_html(results: dict) -> str:
    """HTML autocontido (CSS inline) para download."""
    rows = []
    for r in results.get("results", []):
        color = {"encontrado": "#22c55e", "não encontrado": "#6b7280",
                 "erro": "#ef4444", "rate-limited": "#eab308",
                 "indeterminado": "#a855f7"}.get(r.get("status"), "#888")
        link = f'<a href="{r["url"]}" target="_blank">{r["url"]}</a>' if r.get("status") == "encontrado" else "—"
        rows.append(f"""<tr>
            <td>{r.get('icon','')} {r.get('site')}</td>
            <td>{r.get('category')}</td>
            <td style="color:{color};font-weight:600">{r.get('status')}</td>
            <td>{r.get('confidence')}%</td>
            <td>{r.get('elapsed_ms','')} ms</td>
            <td>{link}</td>
        </tr>""")

    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>Relatório OSINT - {results.get('username')}</title>
<style>
body{{background:#0f172a;color:#e2e8f0;font-family:system-ui,sans-serif;padding:24px}}
h1{{color:#60a5fa}}
table{{width:100%;border-collapse:collapse;margin-top:16px}}
th,td{{padding:8px 12px;border-bottom:1px solid #1e293b;text-align:left;font-size:14px}}
th{{background:#1e293b;color:#94a3b8;text-transform:uppercase;font-size:12px}}
a{{color:#38bdf8;text-decoration:none}}
.summary{{display:flex;gap:24px;margin:16px 0}}
.summary div{{background:#1e293b;padding:12px 20px;border-radius:8px}}
.summary b{{display:block;font-size:24px;color:#60a5fa}}
footer{{margin-top:32px;color:#64748b;font-size:12px}}
</style></head><body>
<h1>🔍 Relatório OSINT — <code>{results.get('username')}</code></h1>
<div class="summary">
  <div><b>{results.get('total',0)}</b>Verificados</div>
  <div><b style="color:#22c55e">{results.get('found',0)}</b>Encontrados</div>
  <div><b style="color:#ef4444">{results.get('errors',0)}</b>Erros</div>
</div>
<table><thead><tr><th>Site</th><th>Categoria</th><th>Status</th><th>Confiança</th><th>Tempo</th><th>Link</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<footer>Gerado em {datetime.utcnow().isoformat()}Z — Uso ético e legal apenas.</footer>
</body></html>"""
