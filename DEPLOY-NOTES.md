# Notas de publicação — lidianefranca.com.br (GitHub Pages)

## Hospedagem (descoberto pela zona DNS)
- **GitHub Pages**, conta **lucasjbdias**.
- DNS no Registro.br já correto:
  - `A  lidianefranca.com.br → 185.199.108.153 / .109.153 / .110.153 / .111.153` (IPs do GitHub Pages)
  - `CNAME  www.lidianefranca.com.br → lucasjbdias.github.io`
- Repositório do site: provavelmente `lucasjbdias.github.io` (ou o repo que contém o arquivo `CNAME` com `lidianefranca.com.br`). **Não apagar o CNAME.**

## PENDENTE — erro de SSL (ERR_CERT_COMMON_NAME_INVALID)
Certificado HTTPS do domínio personalizado ainda não emitido. Fix:
1. Repo → **Settings → Pages**.
2. **Custom domain** = `lidianefranca.com.br` → **Save** (dispara emissão do certificado).
3. Esperar "DNS check successful" + emissão (minutos até ~1h).
4. Marcar **Enforce HTTPS**.
5. Se travar: remover o custom domain, Save, esperar 1 min, re-adicionar, Save (força reemissão).
- Não mexer no Registro.br (DNS já está certo).

## Como publicar showroom + site editorial
Subir no repositório (via github.com → Add file → Upload files, arrastando):
- `index.html`  → raiz do repo  (home editorial)  [arquivo: Site/index.html]
- `showroom/index.html` → apresentação dos 58 modelos  [pasta: Site/showroom/]
- `CNAME` → raiz (garante o domínio custom)  [arquivo: Site/CNAME]
- `assets/marca.png` → para o og:image do site funcionar (opcional)
Resultado: home em `/`, apresentação em `/showroom/`.
