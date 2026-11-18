# Site Caramelos e Cia — caramelosecia.com

Site estático publicado na Hostinger (deploy automático a partir do ramo `main`).

## Como publicar ou editar um artigo

1. Edite `conteudo.json` (lista `posts`): `slug`, `titulo`, `resumo`, `categoria`, `data` (AAAA-MM-DD), `capa` (`img/arquivo.jpg`), `afiliado` (true/false) e `corpo`.
2. Coloque as imagens em `img/`.
3. Rode `python3 build.py`: ele gera `index.html`, `blog/index.html`, `blog/<slug>/index.html`, `sitemap.xml` e `robots.txt`.
4. Faça commit de tudo e envie para o `main`.

## Formato do `corpo`

- `## Título` e `### Subtítulo`
- `- item` (lista) e `1. item` (lista numerada)
- `> texto` (destaque)
- `**negrito**`, `*itálico*`, `[texto](https://link)`
- `![descrição](img/foto.jpg)` (imagem no meio do texto)
- `@produto Nome | descrição | https://link-afiliado | img/foto.jpg | preço (opcional)` (card de produto)

Os estilos ficam em `assets/site.css`. Não edite os arquivos `.html` direto: eles são gerados pelo `build.py`.
