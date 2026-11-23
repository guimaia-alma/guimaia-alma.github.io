#!/usr/bin/env python3
"""Gera o site estático da Alma (home + Caderno) pronto para Google e IAs.

Uso: python3 build.py            -> publica só os textos cuja data/hora já chegou
     python3 build.py --todos    -> gera tudo (para conferir)
Saída em ./dist. Endereço do site em config.json (SITE_URL).
"""
import json, os, re, shutil, sys, html
from datetime import datetime, timezone, timedelta

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from posts import POSTS

CFG = json.load(open(os.path.join(AQUI, "config.json")))
SITE = CFG["SITE_URL"].rstrip("/")
BRT = timezone(timedelta(hours=-3))
AGORA = datetime.now(BRT)
TODOS = "--todos" in sys.argv
DIST = os.path.join(AQUI, "dist")

ORG = {
    "@type": "InsuranceAgency", "@id": SITE + "/#org",
    "name": "Alma Corretora de Seguros e Legado Familiar Ltda",
    "alternateName": "Alma Seguros e Legado Familiar",
    "url": SITE + "/", "logo": SITE + "/logo.png", "taxID": "64.154.117/0001-02",
    "description": "Corretora consultiva de seguro de vida, proteção familiar, sucessão patrimonial e proteção empresarial em Belo Horizonte, com atendimento em todo o Brasil.",
    "areaServed": ["Belo Horizonte", "Minas Gerais", "Brasil"],
    "address": {"@type": "PostalAddress", "addressLocality": "Belo Horizonte", "addressRegion": "MG", "addressCountry": "BR"},
    "email": CFG["EMAIL"],
    "sameAs": CFG["REDES"],
    "founder": {"@type": "Person", "name": "Guilherme Pinheiro Maia", "jobTitle": "Corretor de seguros (SUSEP 251175815)"},
    "identifier": [{"@type": "PropertyValue", "propertyID": "SUSEP", "value": "252176186"}],
}

def quando(p):
    return datetime.fromisoformat(f'{p["date"]}T{p["time"]}:00').replace(tzinfo=BRT)

def e(t):
    return html.escape(t, quote=True)

def fmt_data(d):
    meses = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
    y, m, dd = d.split("-")
    return f"{int(dd)} de {meses[int(m)-1]} de {y}"

def blocos(body):
    out = []
    for t, c in body:
        if t == "h2": out.append(f"<h2>{e(c)}</h2>")
        elif t == "q": out.append(f"<blockquote>{e(c)}</blockquote>")
        elif t == "ul": out.append("<ul>" + "".join(f"<li>{e(x)}</li>" for x in c) + "</ul>")
        else: out.append(f"<p>{e(c)}</p>")
    return "\n".join(out)

CSS = """:root{--paper:#efe7d8;--ink:#16264d;--wash:#2c4479;--sepia:#6b5a45;--gold:#b0854a;--serif:'Cormorant Garamond',Georgia,serif;--sans:Montserrat,Arial,sans-serif}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--serif)}
a{color:inherit}header{display:flex;justify-content:space-between;align-items:center;padding:22px clamp(18px,4vw,48px)}
header .logo{width:120px;color:var(--ink);display:block}nav a{font-family:var(--sans);font-size:11px;letter-spacing:.14em;text-transform:uppercase;text-decoration:none;margin-left:24px}
main{max-width:700px;margin:0 auto;padding:40px 24px 10vh}
.meta{font-family:var(--sans);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--sepia)}
h1{font-weight:400;font-size:clamp(38px,5.4vw,60px);line-height:1.04;margin:14px 0 22px}
.lead{font-style:italic;font-size:23px;line-height:1.5;color:var(--sepia)}
p,li{font-size:21px;line-height:1.65}h2{font-weight:400;font-size:clamp(27px,3.2vw,34px);line-height:1.12;margin:44px 0 14px}
h3{font-family:var(--sans);font-size:15px;margin:24px 0 6px}ul{padding-left:22px}
blockquote{margin:36px 0;font-style:italic;font-size:30px;line-height:1.22;color:var(--wash)}
.cta{display:flex;flex-wrap:wrap;gap:12px;margin:46px 0 10px}.btn{font-family:var(--sans);font-size:12px;letter-spacing:.12em;text-transform:uppercase;text-decoration:none;padding:15px 22px;background:var(--ink);color:var(--paper)}
.btn.line{background:transparent;color:var(--ink);border:1px solid var(--ink)}
.lista a{display:block;padding:28px 0;border-top:1px solid #16264d30;text-decoration:none}.lista a:last-child{border-bottom:1px solid #16264d30}
.lista h2{margin:6px 0 4px}.lista p{margin:0;font-style:italic;color:var(--sepia)}
footer{background:var(--ink);color:#cfc6b4;padding:44px clamp(18px,4vw,48px);font-family:var(--sans);font-size:12px;line-height:1.7}
.aviso{font-size:13px;color:var(--sepia);font-family:var(--sans);margin-top:36px}"""

def logo_svg(index_html):
    syms = re.findall(r'<symbol id="(?:mark|tag)".*?</symbol>', index_html, re.S)
    return ('<svg width="0" height="0" style="position:absolute" aria-hidden="true">' + "".join(syms) + '</svg>',
            '<svg class="logo" viewBox="0 0 1190 450" role="img" aria-label="Alma Seguros e Legado Familiar" fill="currentColor"><use href="#mark" width="1190" height="355"/><use href="#tag" y="370" width="1190" height="80"/></svg>')

def pagina(titulo, descricao, url, corpo, jsonld, defs, logo, og_tipo="website"):
    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(titulo)}</title><meta name="description" content="{e(descricao)}"><link rel="canonical" href="{url}">
<meta name="robots" content="index,follow,max-snippet:-1,max-image-preview:large">
<meta property="og:type" content="{og_tipo}"><meta property="og:title" content="{e(titulo)}"><meta property="og:description" content="{e(descricao)}"><meta property="og:url" content="{url}"><meta property="og:site_name" content="Alma Seguros e Legado Familiar"><meta property="og:locale" content="pt_BR"><meta property="og:image" content="{SITE}/og.jpg">
<meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#16264d">
<link rel="alternate" type="application/rss+xml" title="Caderno da Alma" href="{SITE}/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;1,400&family=Montserrat:wght@400;500&display=swap" rel="stylesheet">
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>
<style>{CSS}</style></head><body>{defs}
<header><a href="{SITE}/" aria-label="Alma, página inicial">{logo}</a><nav><a href="{SITE}/caderno/">Caderno</a><a href="{SITE}/#agendar">Agendar</a></nav></header>
{corpo}
<footer><p>Alma Corretora de Seguros e Legado Familiar Ltda · CNPJ 64.154.117/0001-02 · Registro SUSEP 252176186<br>Responsável técnico: Guilherme Pinheiro Maia · SUSEP 251175815 · Belo Horizonte, MG · atendimento em todo o Brasil<br>{e(CFG["EMAIL"])} · <a href="https://www.instagram.com/almaelegadofamiliar/">@almaelegadofamiliar</a></p>
<p>Conteúdo educativo; não constitui recomendação de investimento nem orientação jurídica ou tributária. A aceitação do seguro está sujeita à análise do risco.</p></footer>
</body></html>"""

def main():
    base = open(os.path.join(AQUI, "site.html")).read()
    defs, logo = logo_svg(base)
    pub = [p for p in POSTS if TODOS or quando(p) <= AGORA]
    pub.sort(key=quando, reverse=True)
    if os.path.exists(DIST): shutil.rmtree(DIST)
    os.makedirs(os.path.join(DIST, "caderno"))
    for f in ("logo.png", "og.jpg"):
        if os.path.exists(os.path.join(AQUI, f)): shutil.copy(os.path.join(AQUI, f), DIST)

    # Home: o site atual, com links reais para o Caderno (lidos por buscadores)
    home = base.replace('href="#caderno"', f'href="{SITE}/caderno/"')
    links = "".join(f'<li><a href="{SITE}/caderno/{p["slug"]}/">{e(p["title"])}</a></li>' for p in pub[:10])
    home = home.replace('<title>', f'<link rel="canonical" href="{SITE}/"><link rel="alternate" type="application/rss+xml" title="Caderno da Alma" href="{SITE}/feed.xml"><title>', 1)
    home = home.replace('</footer>', f'<nav aria-label="Textos recentes do Caderno" class="recentes"><p>Do caderno:</p><ul>{links}</ul></nav></footer>', 1)
    open(os.path.join(DIST, "index.html"), "w").write(home)

    # Lista do Caderno
    lista = "".join(f'<a href="{SITE}/caderno/{p["slug"]}/"><span class="meta">{fmt_data(p["date"])}</span><h2>{e(p["title"])}</h2><p>{e(p["lead"])}</p></a>' for p in pub)
    corpo = f'<main><h1>O <em>caderno</em> da Alma</h1><p class="lead">Textos curtos sobre família, sucessão patrimonial e empresa. Para ler com calma.</p><div class="lista">{lista}</div></main>'
    ld = {"@context": "https://schema.org", "@graph": [ORG, {"@type": "Blog", "name": "Caderno da Alma", "url": SITE + "/caderno/", "publisher": {"@id": SITE + "/#org"}, "inLanguage": "pt-BR"}]}
    open(os.path.join(DIST, "caderno", "index.html"), "w").write(pagina("Caderno da Alma | Família, sucessão e empresa", "Textos da Alma Seguros e Legado Familiar sobre proteção da família, sucessão patrimonial, ITCMD em Minas Gerais e continuidade de empresas.", SITE + "/caderno/", corpo, ld, defs, logo))

    # Cada texto
    for p in pub:
        url = f'{SITE}/caderno/{p["slug"]}/'
        faq = "".join(f"<h3>{e(q)}</h3><p>{e(a)}</p>" for q, a in p["faq"])
        corpo = (f'<main><article><a class="meta" href="{SITE}/caderno/">Voltar ao caderno</a><p class="meta"><time datetime="{quando(p).isoformat()}">{fmt_data(p["date"])}</time> · Guilherme Maia</p>'
                 f'<h1>{e(p["title"])}</h1><p class="lead">{e(p["lead"])}</p>{blocos(p["body"])}'
                 f'<h2>Perguntas frequentes</h2>{faq}'
                 f'<div class="cta"><a class="btn" href="{SITE}/#agendar">Agendar uma conversa</a><a class="btn line" href="{SITE}/#diagnostico">Fazer o diagnóstico</a></div>'
                 f'<p class="aviso">Conteúdo educativo, com base na legislação vigente na data de publicação. Regras tributárias podem mudar; confirme com seu advogado ou contador.</p></article></main>')
        ld = {"@context": "https://schema.org", "@graph": [ORG,
              {"@type": "BlogPosting", "headline": p["title"], "description": p["description"], "datePublished": quando(p).isoformat(), "dateModified": quando(p).isoformat(),
               "author": {"@type": "Person", "name": "Guilherme Pinheiro Maia", "jobTitle": "Corretor de seguros, fundador da Alma"}, "publisher": {"@id": SITE + "/#org"},
               "mainEntityOfPage": url, "inLanguage": "pt-BR", "keywords": ", ".join(p["tags"]), "image": SITE + "/og.jpg"},
              {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in p["faq"]]},
              {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": 1, "name": "Alma", "item": SITE + "/"}, {"@type": "ListItem", "position": 2, "name": "Caderno", "item": SITE + "/caderno/"}, {"@type": "ListItem", "position": 3, "name": p["title"], "item": url}]}]}
        os.makedirs(os.path.join(DIST, "caderno", p["slug"]))
        open(os.path.join(DIST, "caderno", p["slug"], "index.html"), "w").write(pagina(p["title"] + " | Alma", p["description"], url, corpo, ld, defs, logo, "article"))

    # sitemap, robots, llms.txt, RSS
    urls = [(SITE + "/", AGORA.date().isoformat()), (SITE + "/caderno/", AGORA.date().isoformat())] + [(f'{SITE}/caderno/{p["slug"]}/', p["date"]) for p in pub]
    open(os.path.join(DIST, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in urls) + "</urlset>\n")
    open(os.path.join(DIST, "robots.txt"), "w").write(
        "User-agent: *\nAllow: /\n\n# Assistentes de IA são bem-vindos\n" +
        "".join(f"User-agent: {b}\nAllow: /\n" for b in ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "Claude-User", "PerplexityBot", "Google-Extended", "Applebot-Extended", "Bingbot"]) +
        f"\nSitemap: {SITE}/sitemap.xml\n")
    llms = [f"# Alma Seguros e Legado Familiar", "",
            "> Corretora consultiva de seguros em Belo Horizonte (MG), com atendimento em todo o Brasil. Trabalha com proteção da renda e da família, sucessão patrimonial (liquidez para inventário e ITCMD) e continuidade de empresas (acordo de sócios, pessoa-chave).", "",
            "- Razão social: Alma Corretora de Seguros e Legado Familiar Ltda, CNPJ 64.154.117/0001-02, SUSEP 252176186",
            "- Responsável técnico: Guilherme Pinheiro Maia, SUSEP 251175815",
            f"- Contato: {CFG['EMAIL']} · Instagram @almaelegadofamiliar", f"- Agendar conversa e diagnóstico gratuito: {SITE}/", "",
            "## Caderno (textos educativos)", ""] + [f'- [{p["title"]}]({SITE}/caderno/{p["slug"]}/): {p["description"]}' for p in pub]
    open(os.path.join(DIST, "llms.txt"), "w").write("\n".join(llms) + "\n")
    itens = "".join(f'<item><title>{e(p["title"])}</title><link>{SITE}/caderno/{p["slug"]}/</link><guid>{SITE}/caderno/{p["slug"]}/</guid><pubDate>{quando(p).strftime("%a, %d %b %Y %H:%M:%S -0300")}</pubDate><description>{e(p["description"])}</description></item>' for p in pub)
    open(os.path.join(DIST, "feed.xml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Caderno da Alma</title><link>{SITE}/caderno/</link><description>Família, sucessão e empresa.</description><language>pt-BR</language>{itens}</channel></rss>\n')
    if CFG.get("GOOGLE_VERIFICACAO"):
        open(os.path.join(DIST, CFG["GOOGLE_VERIFICACAO"]), "w").write("google-site-verification: " + CFG["GOOGLE_VERIFICACAO"] + "\n")
    open(os.path.join(DIST, ".nojekyll"), "w").write("")
    print(f"{len(pub)} textos publicados em {DIST}")

if __name__ == "__main__":
    main()
