#!/usr/bin/env python3
"""radar-pautas — as pautas de IA em alta nas últimas horas, com fonte conferida.

Uso:
  python3 radar.py                      # coleta, agrupa, dá nota, confere links → 6 pautas
  python3 radar.py --dry                # o mesmo, só imprime (não grava)
  python3 radar.py --angulos            # + ângulo PT para r7ex/explicavideo/carrossel (claude -p, assinatura)
  python3 radar.py --horas 48 --n 8     # janela e quantidade
  python3 radar.py --sem-github         # sem os repositórios em alta do GitHub

Saída: ~/projetos/output/radar-pautas/<AAAA-MM-DD>/pautas.json, pautas.md e radar.html
Só lê páginas públicas (RSS) e o GitHub pelo `gh`. Nenhuma chave de API.
"""
import argparse
import concurrent.futures as cf
import email.utils
import html
import json
import os
import re
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
UA = {"User-Agent": "Mozilla/5.0 (radar-pautas; +https://github.com/inematds/radar-pautas)"}
PRODUCOES = Path.home() / "projetos/wifi/PRODUCOES-VIDEO.md"
SAIDA = Path(os.environ.get("RADAR_SAIDA", Path.home() / "projetos/output/radar-pautas"))
PARADAS = set("""a o as os de da do das dos e em no na nos nas um uma uns umas para por com sem que se ao à é the a an of to in on for and or with by from at is are was be as it its this that new how why what you your
we our their after over into than about just now will can more most first says say said vs via up out
""".split())


# ---------- coleta ----------
def baixar(url, limite=3_000_000, timeout=20, tentativas=2):
    """Reddit e alguns sites devolvem 429 quando pedimos seguido: espera e tenta mais uma vez."""
    import time
    for k in range(tentativas):
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)
            return r.read(limite)
        except urllib.error.HTTPError as e:
            if e.code != 429 or k == tentativas - 1:
                raise
            time.sleep(8)


def texto(el, *nomes):
    for n in nomes:
        for f in el:
            if f.tag.split("}")[-1] == n:
                if n == "link" and f.get("href"):
                    return f.get("href")
                if (f.text or "").strip():
                    return f.text.strip()
    return ""


def quando(s):
    if not s:
        return None
    try:
        d = email.utils.parsedate_to_datetime(s)
    except Exception:
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def limpa(s):
    s = re.sub(r"<[^>]+>", " ", html.unescape(s or ""))
    return re.sub(r"\s+", " ", s).strip()


def ler_feed(fonte):
    try:
        raiz = ET.fromstring(baixar(fonte["url"]))
    except Exception as e:
        return fonte["nome"], [], str(e)[:80]
    itens = []
    for el in raiz.iter():
        if el.tag.split("}")[-1] not in ("item", "entry"):
            continue
        titulo = limpa(texto(el, "title"))
        link = texto(el, "link", "guid", "id")
        data = quando(texto(el, "pubDate", "published", "updated", "date"))
        resumo = limpa(texto(el, "description", "summary", "content"))[:400]
        if titulo and link.startswith("http"):
            itens.append({"titulo": titulo, "link": link, "data": data, "resumo": resumo,
                          "fonte": fonte["nome"], "tipo": fonte["tipo"], "peso": fonte["peso"], "lingua": fonte["lingua"]})
    return fonte["nome"], itens, ""


def github_em_alta(dias=7, n=10):
    """Repositórios novos com mais estrelas. O `gh search` não aceita OR: uma busca por termo, sem repetir."""
    desde = (datetime.now(timezone.utc) - timedelta(days=dias)).strftime("%Y-%m-%d")
    vistos, repos = set(), []
    for termo in ("llm", "agent", "ai"):
        try:
            out = subprocess.run(["gh", "search", "repos", termo, "--created", f">={desde}", "--sort", "stars", "--order", "desc",
                                  "--limit", str(n), "--json", "fullName,description,stargazersCount,url,createdAt"],
                                 capture_output=True, text=True, timeout=60)
            for r in json.loads(out.stdout or "[]"):
                if r["fullName"] not in vistos:
                    vistos.add(r["fullName"])
                    repos.append(r)
        except Exception:
            continue
    return [{"titulo": f"{r['fullName']} — {r.get('description') or ''}"[:200], "link": r["url"], "data": quando(r["createdAt"]),
             "resumo": f"{r['stargazersCount']} estrelas em até {dias} dias", "fonte": "GitHub em alta", "tipo": "comunidade",
             "peso": 0.8, "lingua": "en", "estrelas": r["stargazersCount"], "fresco": True}
            for r in repos if r.get("stargazersCount", 0) >= 300]


# ---------- agrupar e pontuar ----------
def palavras(t):
    return {w for w in re.findall(r"[a-zà-ú0-9][a-zà-ú0-9.+-]{2,}", t.lower()) if w not in PARADAS}


def achar_entidades(t, entidades):
    # "deepseek-ai/..." também conta como DeepSeek: depois do nome pode vir hífen, barra ou fim
    return [e for e in entidades if re.search(rf"(?<![a-z0-9]){re.escape(e)}(?![a-z0-9])", t, re.I)]


def agrupar(itens, entidades):
    grupos = []
    for it in sorted(itens, key=lambda x: x["data"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True):
        pw = palavras(it["titulo"])
        ents = set(achar_entidades(it["titulo"] + " " + it["resumo"][:160], entidades))
        melhor, sim = None, 0.0
        for g in grupos:
            j = len(pw & g["palavras"]) / max(1, len(pw | g["palavras"]))
            comum = ents & g["entidades"]
            s = j + (0.25 if comum and j > 0.12 else 0)
            if s > sim:
                melhor, sim = g, s
        if melhor and sim >= 0.34:
            melhor["itens"].append(it)
            melhor["palavras"] |= pw
            melhor["entidades"] |= ents
        else:
            grupos.append({"itens": [it], "palavras": set(pw), "entidades": set(ents)})
    return grupos


def nota(g, agora, horas):
    fontes = {i["fonte"] for i in g["itens"]}
    oficial = any(i["tipo"] == "oficial" for i in g["itens"])
    datas = [i["data"] for i in g["itens"] if i["data"]]
    idade = (agora - max(datas)).total_seconds() / 3600 if datas else horas
    janela = 168 if any(i.get("fresco") for i in g["itens"]) else horas
    recencia = max(0.0, 1 - idade / janela)
    peso = max(i["peso"] for i in g["itens"])
    estrelas = max((i.get("estrelas", 0) for i in g["itens"]), default=0)
    s = 3.0 * (len(fontes) - 1) + 2.0 * recencia + (1.5 if oficial else 0) + (0.8 if g["entidades"] else 0)
    s += min(1.5, estrelas / 2000)
    return round(s * peso, 2)


def ja_fizemos(g):
    """Linha recente do PRODUCOES-VIDEO.md que cita a mesma entidade + palavra do título."""
    if not PRODUCOES.exists() or not g["entidades"]:
        return ""
    linhas = PRODUCOES.read_text(errors="ignore").splitlines()[-200:]
    genericas = {"agent", "agente", "agentes", "skill", "skills", "model", "modelo", "models", "claude", "openai", "google", "release"}
    chave = {w for w in g["palavras"] if len(w) > 5 and w not in genericas}
    for l in reversed(linhas):
        ll = l.lower()
        if any(e.lower() in ll for e in g["entidades"]) and sum(1 for w in chave if re.search(rf"\b{re.escape(w)}\b", ll)) >= 2:
            return l.strip()[:160]
    return ""


def link_ok(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15)
        return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


# ---------- ângulo (opcional, claude -p pela assinatura) ----------
def angulos(pautas):
    lista = "\n".join(f"{k}. {p['titulo']} | fontes: {', '.join(p['fontes'])} | {p['resumo'][:240]}" for k, p in enumerate(pautas, 1))
    pedido = f"""Você é o pauteiro do INEMA (canal brasileiro que ensina IA na prática, de graça, para gente comum, sem hype).
Para cada pauta abaixo, responda em português do Brasil. Use SÓ o que está na pauta; não invente número nem fato.
Devolva APENAS um JSON (lista, mesma ordem) com objetos:
{{"titulo_pt": "manchete em PT, até 70 caracteres", "por_que_importa": "1 frase para quem não é técnico",
 "gancho": "frase de abertura de reel, até 12 palavras", "formato": "r7ex" | "explicavideo" | "carrossel",
 "palavra": "palavra para o comentário, 3 a 14 letras"}}

{lista}
"""
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}  # assinatura, nunca API
    env["PATH"] = f"{Path.home()}/.local/bin:{Path.home()}/.npm-global/bin:" + env.get("PATH", "")
    try:
        out = subprocess.run(["claude", "-p", "--allowedTools", ""], input=pedido, capture_output=True, text=True, timeout=300, env=env).stdout
        m = re.search(r"\[.*\]", out, re.S)
        dados = json.loads(m.group(0)) if m else []
    except Exception as e:
        print("aviso: ângulos não gerados:", str(e)[:100], file=sys.stderr)
        return
    for p, d in zip(pautas, dados):
        p["angulo"] = d


# ---------- saída ----------
def escreve(pautas, meta, pasta):
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "pautas.json").write_text(json.dumps({"meta": meta, "pautas": pautas}, ensure_ascii=False, indent=2, default=str))
    md = [f"# Radar de pautas — {meta['quando']}", "",
          f"{meta['itens']} notícias de {meta['fontes_ok']} fontes nas últimas {meta['horas']} h. Fora do ar: {', '.join(meta['fontes_falha']) or 'nenhuma'}.", ""]
    for k, p in enumerate(pautas, 1):
        a = p.get("angulo", {})
        md += [f"## {k}. {a.get('titulo_pt') or p['titulo']}", "",
               f"- **Nota** {p['nota']} · **fontes** ({len(p['fontes'])}): {', '.join(p['fontes'])} · {p['idade_h']} h atrás",
               f"- **Link** ({p['link_status']}): {p['link']}"]
        if p["outros_links"]:
            md.append("- Outras fontes: " + " · ".join(p["outros_links"][:4]))
        if a:
            md += [f"- **Por que importa:** {a.get('por_que_importa', '')}", f"- **Gancho:** {a.get('gancho', '')}",
                   f"- **Formato:** {a.get('formato', '')} · **palavra:** {a.get('palavra', '')}"]
        if p["ja_fizemos"]:
            md.append(f"- ⚠ Já fizemos algo parecido: {p['ja_fizemos']}")
        md.append("")
    (pasta / "pautas.md").write_text("\n".join(md))
    (pasta / "radar.html").write_text(pagina(pautas, meta))


def pagina(pautas, meta):
    cards = []
    for k, p in enumerate(pautas, 1):
        a = p.get("angulo", {})
        cards.append(f"""<article><div class="n">{k}</div><div>
<h2>{html.escape(a.get('titulo_pt') or p['titulo'])}</h2>
{f'<p class="orig">{html.escape(p["titulo"])}</p>' if a.get('titulo_pt') else ''}
<p class="meta"><b>{p['nota']}</b> pontos · {len(p['fontes'])} fonte(s): {html.escape(', '.join(p['fontes']))} · {p['idade_h']} h atrás</p>
{f'<p>{html.escape(a.get("por_que_importa", ""))}</p><p class="gancho">“{html.escape(a.get("gancho", ""))}” · {html.escape(a.get("formato", ""))}</p>' if a else ''}
<p><a href="{html.escape(p['link'])}" target="_blank" rel="noopener">abrir a fonte ↗</a></p>
{f'<p class="ja">Já fizemos algo parecido: {html.escape(p["ja_fizemos"])}</p>' if p['ja_fizemos'] else ''}
</div></article>""")
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Radar de pautas — {meta['quando']}</title><style>
body{{margin:0;background:#0c0c10;color:#f5f5f7;font:16px/1.5 Inter,system-ui,sans-serif}}main{{max-width:880px;margin:0 auto;padding:32px 18px}}
h1{{font:800 2rem/1.1 Sora,system-ui,sans-serif;margin:0 0 6px}}h1 span{{color:#FACC15}}.top{{color:#aab4c3;margin-bottom:24px}}
article{{display:flex;gap:16px;border:1px solid #2a2a35;border-radius:14px;padding:18px;margin:14px 0;background:#15151c}}
.n{{font:800 2.2rem/1 Sora,system-ui;color:#FACC15;min-width:42px}}h2{{font:700 1.2rem/1.3 Sora,system-ui;margin:0 0 4px}}
.orig,.meta{{color:#aab4c3;font-size:.9rem;margin:2px 0}}.gancho{{color:#FACC15}}.ja{{color:#ff9b8f;font-size:.9rem}}a{{color:#FACC15}}
</style></head><body><main><h1>Radar de <span>pautas</span></h1>
<p class="top">{meta['quando']} · últimas {meta['horas']} h · {meta['itens']} notícias de {meta['fontes_ok']} fontes</p>
{''.join(cards)}</main></body></html>"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nicho", default="ia")
    ap.add_argument("--horas", type=int, default=24)
    ap.add_argument("--n", type=int, default=6)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--angulos", action="store_true")
    ap.add_argument("--sem-github", action="store_true")
    a = ap.parse_args()

    cfg = json.loads((RAIZ / "fontes.json").read_text())
    fontes, entidades, filtro = cfg[a.nicho], cfg["entidades"], cfg["filtro_ia"]
    agora = datetime.now(timezone.utc)
    corte = agora - timedelta(hours=a.horas)

    itens, ok, falha = [], [], []
    with cf.ThreadPoolExecutor(10) as ex:
        for (nome, its, erro), f in zip(ex.map(ler_feed, fontes), fontes):
            (falha if erro else ok).append(nome)
            for it in its:
                if not it["data"] or it["data"] < corte or it["data"] > agora + timedelta(hours=2):
                    continue
                if f.get("filtro") and not any(k in f" {it['titulo'].lower()} {it['resumo'][:200].lower()} " for k in filtro):
                    continue
                itens.append(it)
    if not a.sem_github:
        gh = github_em_alta()  # janela própria de 7 dias
        if gh:
            ok.append("GitHub em alta")
            itens += gh

    grupos = agrupar(itens, entidades)
    for g in grupos:
        g["nota"] = nota(g, agora, a.horas)
    grupos.sort(key=lambda g: g["nota"], reverse=True)

    pautas, por_entidade, por_fonte = [], {}, {}
    for g in grupos:
        if len(pautas) >= a.n:
            break
        principal = sorted(g["entidades"])[0] if g["entidades"] else None
        if principal and por_entidade.get(principal, 0) >= 2:  # variedade: no máximo 2 pautas da mesma empresa
            continue
        unica = g["itens"][0]["fonte"] if len({i["fonte"] for i in g["itens"]}) == 1 else None
        if unica and por_fonte.get(unica, 0) >= 2:  # e no máximo 2 vindas só do mesmo site
            continue
        ordem = sorted(g["itens"], key=lambda i: (i["tipo"] != "oficial", -i["peso"]))
        escolhido, status = None, 0
        for it in ordem[:4]:
            status = link_ok(it["link"])
            if status == 200:
                escolhido = it
                break
        if not escolhido:
            continue
        por_entidade[principal] = por_entidade.get(principal, 0) + 1
        if unica:
            por_fonte[unica] = por_fonte.get(unica, 0) + 1
        datas = [i["data"] for i in g["itens"] if i["data"]]
        pautas.append({
            "titulo": escolhido["titulo"], "link": escolhido["link"], "link_status": status,
            "fontes": sorted({i["fonte"] for i in g["itens"]}), "entidades": sorted(g["entidades"]),
            "nota": g["nota"], "idade_h": round((agora - max(datas)).total_seconds() / 3600, 1) if datas else None,
            "resumo": escolhido["resumo"], "outros_links": [i["link"] for i in g["itens"] if i is not escolhido],
            "ja_fizemos": ja_fizemos(g),
        })

    if a.angulos and pautas:
        angulos(pautas)
    meta = {"quando": datetime.now().strftime("%d/%m/%Y %H:%M"), "horas": a.horas, "itens": len(itens),
            "fontes_ok": len(ok), "fontes_falha": falha, "grupos": len(grupos)}

    for k, p in enumerate(pautas, 1):
        print(f"{k}. [{p['nota']}] {p['titulo'][:90]}\n   {len(p['fontes'])} fonte(s): {', '.join(p['fontes'])} · {p['idade_h']} h · {p['link_status']} {p['link']}")
        if p.get("angulo"):
            print(f"   → {p['angulo'].get('titulo_pt', '')} | {p['angulo'].get('formato', '')}")
        if p["ja_fizemos"]:
            print(f"   ⚠ já fizemos: {p['ja_fizemos'][:100]}")
    print(f"\n{len(itens)} notícias, {len(grupos)} assuntos, {len(ok)} fontes ok; fora do ar: {', '.join(falha) or 'nenhuma'}")
    if not a.dry:
        pasta = SAIDA / datetime.now().strftime("%Y-%m-%d")
        escreve(pautas, meta, pasta)
        print(f"gravado: {pasta}/pautas.md e radar.html")
    return 0 if len(pautas) >= min(a.n, 3) else 1


if __name__ == "__main__":
    sys.exit(main())
