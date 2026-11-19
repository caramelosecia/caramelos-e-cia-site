#!/usr/bin/env python3
"""Gera o site estático da Caramelos e Cia a partir de conteudo.json.

Saída: index.html, blog/index.html, blog/<slug>/index.html, sitemap.xml, robots.txt.
Uso: python3 build.py
"""
import datetime
from zoneinfo import ZoneInfo
import html
import json
import os
import re

try:
    from PIL import Image
except ImportError:  # sem Pillow, o site sai sem as versões menores
    Image = None

SITE = "https://caramelosecia.com"
NOME = "Caramelos e Cia"
RAIZ = os.path.dirname(os.path.abspath(__file__))
FONTES = "https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Figtree:wght@400;500;600;700&display=swap"
with open(os.path.join(RAIZ, "assets", "site.css"), encoding="utf-8") as _f:
    CSS = re.sub(r"\s*\n\s*", "", _f.read())
PINTEREST = '<meta name="p:domain_verify" content="e2b6eca343b0e595d32aaa3747913422"/>'
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]
REDES = [
    ("Instagram", "https://www.instagram.com/caramelosecia"),
    ("TikTok", "https://www.tiktok.com/@carameloscia"),
    ("X", "https://x.com/caramelosecia"),
    ("YouTube", "https://www.youtube.com/@carameloscia"),
    ("Pinterest", "https://br.pinterest.com/carameloscia"),
]

esc = lambda s: html.escape(str(s or ""), quote=True)


def img_url(caminho):
    if not caminho:
        return ""
    return caminho if caminho.startswith(("http", "/")) else "/" + caminho


LARGURAS = (480, 800, 1200)


def variantes(caminho, larguras=LARGURAS):
    """Cria versões .webp menores de uma imagem (em img/r/) e devolve (srcset, largura, altura)."""
    rel = img_url(caminho).lstrip("/")
    orig = os.path.join(RAIZ, rel)
    if not Image or not os.path.exists(orig):
        return "", None, None
    with Image.open(orig) as im:
        w, h = im.size
        itens = []
        base = os.path.splitext(os.path.basename(rel))[0]
        for lw in larguras:
            if lw >= w:
                continue
            destino = os.path.join(RAIZ, "img", "r", f"{base}-{lw}.webp")
            if not os.path.exists(destino) or os.path.getmtime(destino) < os.path.getmtime(orig):
                os.makedirs(os.path.dirname(destino), exist_ok=True)
                im2 = im.convert("RGB").resize((lw, round(h * lw / w)), Image.LANCZOS)
                im2.save(destino, "WEBP", quality=78, method=6)
            itens.append(f"/img/r/{base}-{lw}.webp {lw}w")
        itens.append(f"{img_url(caminho)} {w}w")
    return ", ".join(itens), w, h


def tag_img(caminho, sizes, alt="", lazy=True, larguras=LARGURAS, extra=""):
    srcset, w, h = variantes(caminho, larguras)
    attrs = f'src="{esc(img_url(caminho))}" alt="{esc(alt)}"'
    if w:
        attrs += f' width="{w}" height="{h}"'
    if srcset:
        attrs += f' srcset="{srcset}" sizes="{sizes}"'
    attrs += ' loading="lazy" decoding="async"' if lazy else ' fetchpriority="high" decoding="async"'
    return f"<img {attrs}{extra}>"


def fmt_data(d):
    try:
        a, m, dia = map(int, d.split("-"))
        return f"{dia:02d} de {MESES[m - 1]} de {a}"
    except Exception:
        return esc(d)


def tempo_leitura(t):
    return f"{max(1, round(len((t or '').split()) / 200))} min de leitura"


def inline(s):
    s = esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
               r'<a href="\2" target="_blank" rel="noopener">\1</a>', s)
    s = re.sub(r"\[([^\]]+)\]\((/[^)\s]*)\)", r'<a href="\2">\1</a>', s)
    return s


ICO_SACOLA = ('<svg viewBox="0 0 24 24" fill="none" stroke="#121212" stroke-width="2" stroke-linecap="round" '
              'stroke-linejoin="round" aria-hidden="true"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/>'
              '<path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>')


def produto(txt):
    partes = [x.strip() for x in txt.split("|")] + [""] * 5
    nome, desc, url, img, preco = partes[:5]
    if not re.match(r"^https?://", url):
        return ""
    foto = tag_img(img, "110px", alt=nome, larguras=(240,)) if img else ICO_SACOLA
    p = f'<span class="preco">{esc(preco)}</span>' if preco else ""
    return (f'<div class="produto"><div class="pimg">{foto}</div>'
            f'<div class="pinfo"><strong>{esc(nome)}</strong><span>{esc(desc)}</span>{p}</div>'
            f'<a class="btn" href="{esc(url)}" target="_blank" rel="sponsored noopener">Ver oferta</a></div>')


def md(txt):
    out, lista = [], None

    def fecha():
        nonlocal lista
        if lista:
            out.append(f"</{lista}>")
            lista = None

    for linha in (txt or "").split("\n"):
        t = linha.strip()
        if not t:
            fecha(); continue
        if m := re.match(r"^###\s+(.*)", t):
            fecha(); out.append(f"<h3>{inline(m[1])}</h3>")
        elif m := re.match(r"^##\s+(.*)", t):
            fecha(); out.append(f"<h2>{inline(m[1])}</h2>")
        elif m := re.match(r"^>\s?(.*)", t):
            fecha(); out.append(f"<blockquote>{inline(m[1])}</blockquote>")
        elif m := re.match(r"^@produto\s+(.*)", t):
            fecha(); out.append(produto(m[1]))
        elif m := re.match(r"^[-*]\s+(.*)", t):
            if lista != "ul":
                fecha(); out.append("<ul>"); lista = "ul"
            out.append(f"<li>{inline(m[1])}</li>")
        elif m := re.match(r"^\d+[.)]\s+(.*)", t):
            if lista != "ol":
                fecha(); out.append("<ol>"); lista = "ol"
            out.append(f"<li>{inline(m[1])}</li>")
        elif m := re.match(r"^!\[([^\]]*)\]\(([^)\s]+)\)", t):
            fecha(); out.append(f'<figure class="capa-art">{tag_img(m[2], "(max-width: 800px) 100vw, 716px", alt=m[1])}</figure>')
        else:
            fecha(); out.append(f"<p>{inline(t)}</p>")
    fecha()
    return "\n".join(out)


def link_ofertas(cfg):
    u = (cfg.get("ofertas_url") or "").strip()
    return (f'href="{esc(u)}" target="_blank" rel="noopener"') if u else 'href="/#ofertas"'


def pagina(cfg, *, titulo, descricao, caminho, corpo, ativo="", imagem="", tipo="website", extra_head="", scripts=""):
    url = SITE + caminho
    img = SITE + img_url(imagem) if imagem else SITE + "/img/logo.png"
    of = link_ofertas(cfg)
    nav = lambda nome, href, chave: f'<a href="{href}"{" class=ativo" if ativo == chave else ""}>{nome}</a>'
    redes = "\n      ".join(f'<a href="{u}" target="_blank" rel="noopener">{n}</a>' for n, u in REDES)
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{PINTEREST}
<title>{esc(titulo)}</title>
<meta name="description" content="{esc(descricao)}">
<link rel="canonical" href="{url}">
<meta property="og:site_name" content="{NOME}">
<meta property="og:type" content="{tipo}">
<meta property="og:title" content="{esc(titulo)}">
<meta property="og:description" content="{esc(descricao)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{img}">
<meta property="og:locale" content="pt_BR">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/img/icone.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preload" as="style" href="{FONTES}" onload="this.onload=null;this.rel='stylesheet'">
<noscript><link rel="stylesheet" href="{FONTES}"></noscript>
<style>{CSS}</style>
{extra_head}
</head>
<body>
<header>
  <div class="wrap nav">
    <a class="marca" href="/" aria-label="Caramelos e Cia: página inicial"><img src="/img/icone.png" alt="" width="46" height="46"><span>Caramelos &amp; Cia</span></a>
    <nav class="menu">
      {nav("Início", "/", "inicio")}
      {nav("Blog", "/blog/", "blog")}
      <a class="btn" {of}>Grupo de ofertas</a>
    </nav>
  </div>
</header>
<main>
{corpo}
</main>
<footer>
  <div class="wrap rodape">
    <a class="marca" href="/" aria-label="Caramelos e Cia: página inicial"><img src="/img/icone.png" alt="" width="46" height="46"><span>Caramelos &amp; Cia</span></a>
    <div style="display:flex;gap:18px;align-items:center;flex-wrap:wrap">
      <a href="/blog/" style="text-decoration:none">Blog</a>
      <a {of} style="text-decoration:none">Grupo de ofertas</a>
    </div>
    <nav class="redes" aria-label="Redes sociais">
      {redes}
    </nav>
    <small>© {datetime.date.today().year} Caramelos e Cia • Conteúdo informativo. Em caso de dúvida sobre a saúde do seu pet, consulte um médico-veterinário.</small>
  </div>
</footer>
{scripts}
</body>
</html>
"""


def card(p):
    capa = (tag_img(p["capa"], "(max-width: 700px) calc(100vw - 44px), 360px", alt=p.get("alt_capa") or p["titulo"]) if p.get("capa")
            else '<img class="sem" src="/img/icone.png" alt="" width="160" height="160" loading="lazy">')
    busca = esc((p["titulo"] + " " + p.get("resumo", "") + " " + p.get("corpo", "")).lower())
    return f"""<a class="card" href="/blog/{esc(p['slug'])}/" data-cat="{esc(p.get('categoria') or 'Dicas')}" data-busca="{busca}">
  <div class="capa">{capa}</div>
  <div class="corpo">
    <div class="meta"><span class="cat">{esc(p.get('categoria') or 'Dicas')}</span><span>{fmt_data(p.get('data'))}</span></div>
    <h3>{esc(p['titulo'])}</h3>
    <p>{esc(p.get('resumo'))}</p>
    <span class="leia">Ler artigo →</span>
  </div></a>"""


VAZIO = '<div class="vazio">Novos artigos chegando em breve 🐾</div>'


def home(cfg, posts):
    ult = "\n".join(card(p) for p in posts[:3]) or VAZIO
    of = link_ofertas(cfg)
    plataforma = cfg.get("ofertas_plataforma")
    nota = (f"Grupo no {esc(plataforma)}. É grátis e você sai quando quiser." if plataforma else
            "É grátis e você sai quando quiser.") if cfg.get("ofertas_url") else "O link do grupo será liberado em breve!"
    slugs = json.dumps([p["slug"] for p in posts])
    corpo = f"""<section class="hero">
  <span class="pata" style="top:20px;left:4%">🐾</span>
  <span class="pata" style="bottom:-10px;right:6%;transform:rotate(25deg)">🐾</span>
  <div class="wrap">
    <div class="hero-card">
      <div>
        <span class="tag">Dicas • Curiosidades • Cuidados</span>
        <h1>Para quem ama cães, gatos e cia.</h1>
        <p class="lead">{esc(cfg.get('slogan') or 'Informação, dicas e curiosidades para quem ama bicho.')}</p>
        <div class="acoes">
          <a class="btn" {of}>Entrar no grupo de ofertas</a>
          <a class="btn preto" href="/blog/">Ler o blog</a>
        </div>
      </div>
      <img class="hero-logo" src="/img/logo.png" alt="Logo Caramelos e Cia" width="480" height="480" fetchpriority="high" decoding="async">
    </div>
  </div>
</section>

<section class="bloco ofertas" id="ofertas">
  <div class="wrap ofertas-grid">
    <div class="ofertas-cta">
      <span class="tag">Grupo de ofertas</span>
      <h2>Economize no que o seu pet mais usa.</h2>
      <p>Promoções selecionadas de ração, petiscos, areia, antipulgas e brinquedos, direto no seu celular. Entre no grupo e receba as melhores ofertas primeiro.</p>
      <a class="btn" {of}>Quero entrar no grupo</a>
      <p class="nota">{nota}</p>
    </div>
    <div class="beneficios">
      <div class="ben"><div class="ico"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#121212" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17 10c.7-.7 1.69 0 2.5 0a2.5 2.5 0 1 0 0-5 .5.5 0 0 1-.5-.5 2.5 2.5 0 1 0-5 0c0 .81.7 1.8 0 2.5l-7 7c-.7.7-1.69 0-2.5 0a2.5 2.5 0 0 0 0 5c.28 0 .5.22.5.5a2.5 2.5 0 1 0 5 0c0-.81-.7-1.8 0-2.5Z"/></svg></div><div><h3>Ofertas garimpadas</h3><p>Só promoção que vale a pena, com preço conferido.</p></div></div>
      <div class="ben"><div class="ico"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#121212" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12.6 2.6A2 2 0 0 0 11.2 2H4a2 2 0 0 0-2 2v7.2a2 2 0 0 0 .6 1.4l8.7 8.7a2.4 2.4 0 0 0 3.4 0l6.6-6.6a2.4 2.4 0 0 0 0-3.4z"/><circle cx="7.5" cy="7.5" r="1.5" fill="#121212"/></svg></div><div><h3>Cupons exclusivos</h3><p>Descontos extras de lojas e pet shops parceiros.</p></div></div>
      <div class="ben"><div class="ico"><svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#121212" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M13 2 4 14h7l-1 8 9-12h-7z"/></svg></div><div><h3>Alertas relâmpago</h3><p>Black Friday, datas especiais e baixas de preço avisadas na hora.</p></div></div>
    </div>
  </div>
</section>

<section class="bloco">
  <div class="wrap">
    <div class="titulo-sec">
      <div><span class="tag">Blog</span><h2>Últimos artigos</h2></div>
      <a class="btn preto" href="/blog/">Ver todos</a>
    </div>
    <div class="grid-posts">
{ult}
    </div>
  </div>
</section>"""
    # links antigos (#slug, #blog) continuam funcionando
    script = f"""<script>
(function(){{var h=decodeURIComponent((location.hash||"").slice(1));var s={slugs};
if(h==="blog")location.replace("/blog/");else if(s.indexOf(h)>-1)location.replace("/blog/"+h+"/");}})();
</script>"""
    return pagina(cfg, titulo=f"{NOME} | Dicas, cuidados e ofertas para pets",
                  descricao=cfg.get("slogan") or "Informação, dicas e curiosidades para quem ama bicho.",
                  caminho="/", corpo=corpo, ativo="inicio", scripts=script)


def blog(cfg, posts):
    cats = ["Todas"] + sorted({p.get("categoria") or "Dicas" for p in posts})
    filtros = "".join(f'<button class="{"on" if c == "Todas" else ""}" data-cat="{esc(c)}">{esc(c)}</button>'
                      for c in cats) if len(cats) > 2 else ""
    cards = "\n".join(card(p) for p in posts) or VAZIO
    corpo = f"""<section class="bloco">
  <div class="wrap">
    <div class="titulo-sec">
      <div><span class="tag">Blog Caramelos e Cia</span><h1 style="font-size:clamp(1.9rem,3.6vw,2.7rem)">Dicas, cuidados e curiosidades</h1></div>
      <input class="busca" id="busca" type="search" placeholder="Buscar artigo..." aria-label="Buscar artigo">
    </div>
    <div class="filtros" id="filtros">{filtros}</div>
    <div class="grid-posts" id="todos">
{cards}
    </div>
    <div class="vazio" id="nada" style="display:none">Nenhum artigo encontrado.</div>
  </div>
</section>"""
    script = """<script>
(function(){var cat="Todas",cards=[].slice.call(document.querySelectorAll("#todos .card")),busca=document.getElementById("busca");
function f(){var q=(busca.value||"").toLowerCase(),n=0;cards.forEach(function(c){var ok=(cat==="Todas"||c.dataset.cat===cat)&&(!q||c.dataset.busca.indexOf(q)>-1);c.style.display=ok?"":"none";if(ok)n++});document.getElementById("nada").style.display=n?"none":"";}
document.getElementById("filtros").addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;cat=b.dataset.cat;[].forEach.call(this.children,function(x){x.classList.toggle("on",x===b)});f();});
busca.addEventListener("input",f);})();
</script>"""
    return pagina(cfg, titulo=f"Blog | {NOME}",
                  descricao="Dicas, cuidados e curiosidades sobre cães, gatos e outros pets.",
                  caminho="/blog/", corpo=corpo, ativo="blog", scripts=script)


def relacionados(p, posts, n=3):
    outros = [x for x in posts if x["slug"] != p["slug"]]
    mesma = [x for x in outros if (x.get("categoria") or "") == (p.get("categoria") or "")]
    resto = [x for x in outros if x not in mesma]
    return (mesma + resto)[:n]


def artigo(cfg, p, posts):
    of = link_ofertas(cfg)
    caminho = f"/blog/{p['slug']}/"
    aviso = ('<p class="aviso-afiliado">Este artigo contém links de afiliado. Se você comprar por eles, a Caramelos e Cia '
             'pode receber uma pequena comissão, sem nenhum custo extra para você. Os preços e as condições podem mudar '
             'a qualquer momento: confira sempre na loja.</p>') if p.get("afiliado") else ""
    capa = f'<div class="capa-art">{tag_img(p["capa"], "(max-width: 800px) 100vw, 716px", alt=p.get("alt_capa") or p["titulo"], lazy=False)}</div>' if p.get("capa") else ""
    fontes = p.get("fontes") or []
    fontes_html = ("<section class=\"fontes\"><h2>Fontes e leitura recomendada</h2><ul>" + "".join(
        f'<li><a href="{esc(f["url"])}" target="_blank" rel="noopener">{esc(f["titulo"])}</a></li>' for f in fontes)
        + "</ul></section>") if fontes else ""
    rel = relacionados(p, posts)
    leia_html = ("<section class=\"leia-tambem\"><h2>Leia também</h2><ul>" + "".join(
        f'<li><a href="/blog/{esc(x["slug"])}/">{esc(x["titulo"])}</a></li>' for x in rel)
        + "</ul></section>") if rel else ""
    corpo = f"""<article class="artigo">
  <a class="voltar" href="/blog/">← Voltar para o blog</a><br>
  <span class="tag">{esc(p.get('categoria') or 'Dicas')}</span>
  <h1>{esc(p['titulo'])}</h1>
  <p class="sub">{esc(p.get('resumo'))}</p>
  <p class="meta-art">{fmt_data(p.get('data'))} • {tempo_leitura(p.get('corpo'))}</p>
  {capa}
  {aviso}
  <div class="texto">
{md(p.get('corpo'))}
  </div>
  {fontes_html}
  {leia_html}
  <div class="cta-art"><div><h3>Curtiu? Economize com o seu pet também.</h3><p>Entre no nosso grupo de ofertas.</p></div>
  <a class="btn preto" {of}>Entrar no grupo</a></div>
</article>"""
    ld = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": p["titulo"], "description": p.get("resumo", ""),
        "datePublished": p.get("data"), "dateModified": p.get("atualizado") or p.get("data"),
        "mainEntityOfPage": SITE + caminho,
        "image": SITE + img_url(p["capa"]) if p.get("capa") else SITE + "/img/logo.png",
        "author": {"@type": "Organization", "name": NOME},
        "publisher": {"@type": "Organization", "name": NOME, "logo": {"@type": "ImageObject", "url": SITE + "/img/logo.png"}},
    }
    trilha = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Início", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Blog", "item": SITE + "/blog/"},
        {"@type": "ListItem", "position": 3, "name": p["titulo"], "item": SITE + caminho}]}
    extra = (f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
             f'<script type="application/ld+json">{json.dumps(trilha, ensure_ascii=False)}</script>')
    return pagina(cfg, titulo=f"{p['titulo']} | {NOME}", descricao=p.get("resumo", ""), caminho=caminho,
                  corpo=corpo, ativo="blog", imagem=p.get("capa"), tipo="article", extra_head=extra)


def salvar(rel, conteudo):
    caminho = os.path.join(RAIZ, rel)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(conteudo)


def main():
    with open(os.path.join(RAIZ, "conteudo.json"), encoding="utf-8") as f:
        dados = json.load(f)
    cfg = dados.get("config", {})
    hoje_br = datetime.datetime.now(ZoneInfo("America/Sao_Paulo")).date().isoformat()
    todos = dados.get("posts", [])
    agendados = [p["slug"] for p in todos if p.get("data", "") > hoje_br]
    # artigos com data futura ficam guardados e só entram no site a partir do dia marcado
    posts = sorted([p for p in todos if p.get("data", "") <= hoje_br], key=lambda p: p.get("data", ""), reverse=True)
    if agendados:
        print("Agendados (ainda não publicados):", ", ".join(agendados))

    salvar("index.html", home(cfg, posts))
    salvar("blog/index.html", blog(cfg, posts))
    for p in posts:
        salvar(f"blog/{p['slug']}/index.html", artigo(cfg, p, posts))

    hoje = hoje_br
    ult = posts[0].get("data", hoje) if posts else hoje
    urls = [(f"{SITE}/", ult, "weekly", "1.0"), (f"{SITE}/blog/", ult, "weekly", "0.8")]
    urls += [(f"{SITE}/blog/{p['slug']}/", p.get("atualizado") or p.get("data", hoje), "monthly", "0.7") for p in posts]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, mod, freq, pri in urls:
        sm.append(f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{mod}</lastmod>\n    <changefreq>{freq}</changefreq>\n    <priority>{pri}</priority>\n  </url>")
    sm.append("</urlset>\n")
    salvar("sitemap.xml", "\n".join(sm))
    salvar("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n")
    print(f"OK: {len(posts)} artigos, {len(urls)} URLs no sitemap")


if __name__ == "__main__":
    main()
