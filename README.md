# Site — Dra. Lidiane França Dias (lidianefranca.com.br)

Site profissional single-page, responsivo, acessível (WCAG AA) e otimizado para SEO,
com a identidade DLF (ouro · onix · mármore; Cormorant Garamond + Montserrat).

## Arquivos
- **`index.html`** — site completo **self-contained** (CSS/JS/imagens embutidos em base64).
  Basta subir este arquivo na raiz do domínio. Funciona em qualquer hospedagem estática.
- `artifact.html` — mesma página em versão "corpo" (usada no preview do Claude Artifacts).
- `assets/` — mármores e marca em arquivo separado (para versão otimizada com assets externos).
- `../build/build_site.py` — gerador do site. `../build/site_assets.py` — gerador dos assets.

## Como editar / regerar
```bash
cd build
python site_assets.py   # regenera mármores + marca (se mudar a identidade)
python build_site.py    # reconstrói index.html e artifact.html
```
Conteúdo (áreas, FAQ, textos, contatos) está em `build/build_site.py` (listas AREAS, DIF, FAQ e blocos HTML).

## Seções
Hero · Sobre · Áreas de atuação (6) · Diferenciais (6) · Perguntas frequentes · Contato (canais + formulário → WhatsApp) · Rodapé.

## Técnico
- **SEO:** `<title>`, meta description/keywords, canonical, Open Graph, Twitter Card, **JSON-LD** `Attorney` (endereço, telefone, horário, áreas, grupo).
- **Acessibilidade:** HTML semântico, skip-link, landmarks, `aria-*`, foco visível, acordeão acessível, `prefers-reduced-motion`, contraste AA.
- **Performance:** single-file, fontes Google com `display=swap`, imagens leves (mármore ~60 KB), JS mínimo sem dependências.
- **Conformidade OAB:** tom informativo e sóbrio, sem promessa de resultados; aviso do Provimento 205/2021 no rodapé.

## Pendências para produção (recomendado)
1. **Imagem OG real:** hoje o `og:image` aponta para `/assets/marca.png` — suba `assets/marca.png` na raiz para o preview em redes sociais funcionar.
2. **Foto da Dra. Lidiane** (opcional) na seção "Sobre" para humanizar.
3. **Domínio/SSL** e `sitemap.xml` + `robots.txt`.
4. Conferir **dados** (endereço/CEP, horário real) e ajustar textos se desejado.

## Contatos usados
Tel/WhatsApp (31) 99632-0110 · lidianefranca@lidianefranca.com.br · Av. José Sérvulo Soalheiro, 688A · São Pedro · Sete Lagoas/MG · OAB/MG 207.054
