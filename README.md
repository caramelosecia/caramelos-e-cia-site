# Site Caramelos e Cia — caramelosecia.com

Site estático publicado na Hostinger (deploy automático a partir do ramo `main`).

## Como publicar ou editar um artigo

1. Edite `conteudo.json` (lista `posts`): `slug`, `titulo`, `resumo`, `categoria`, `data` (AAAA-MM-DD; artigos com data futura ficam agendados e só aparecem a partir desse dia, depois de rodar o build), `capa` (`img/arquivo.jpg`), `afiliado` (true/false) e `corpo`.
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

## Regras de SEO (guia do Google para iniciantes)

Todo artigo novo deve ter:

- `titulo` único e claro e `resumo` de 1 ou 2 frases (vira a meta description).
- `slug` com palavras que descrevem o tema (vira o endereço `/blog/<slug>/`).
- `alt_capa`: texto alternativo curto que descreve a foto da capa.
- Pelo menos 1 link interno no texto para outro artigo do blog, com texto âncora descritivo (`[texto](/blog/slug/)`). O bloco "Leia também" é gerado automaticamente.
- `fontes`: 1 a 3 links externos confiáveis (órgãos oficiais, associações veterinárias, Procon etc.).
- Subtítulos `##` organizando o texto, conteúdo original e sem repetição forçada de palavras-chave.
- Links de afiliado só pelos cards `@produto` (já saem com `rel="sponsored"`) e `"afiliado": true` para mostrar o aviso.
- Temas de saúde: orientar a procurar o veterinário e nunca dizer que o produto resolve sintomas.
