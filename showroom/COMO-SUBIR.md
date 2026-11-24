# Como publicar o Showroom em lidianefranca.com.br/showroom

O arquivo `index.html` desta pasta é **autossuficiente** (tudo embutido; só as fontes vêm do Google).
Basta colocá-lo dentro do domínio. Resultado final: **https://lidianefranca.com.br/showroom/**

## Opção A — Hospedagem com painel (cPanel / Hostinger / Registro.br / etc.)
1. Entre no painel da hospedagem do domínio.
2. Abra o **Gerenciador de Arquivos** e vá até a pasta pública (geralmente `public_html`).
3. Crie uma pasta chamada `showroom`.
4. Faça **upload** do arquivo `index.html` (desta pasta) para dentro de `public_html/showroom/`.
5. Acesse **https://lidianefranca.com.br/showroom/** — pronto.

## Opção B — FTP (FileZilla)
1. Conecte com host/usuário/senha de FTP do domínio.
2. Entre em `public_html` (ou `www`), crie a pasta `showroom`.
3. Arraste o `index.html` para dentro dela.

## Opção C — Link público em segundos (sem mexer no domínio)
- Acesse **app.netlify.com/drop** e arraste o `index.html` (ou a pasta `showroom`).
- A Netlify devolve uma URL na hora, ex.: `https://algo.netlify.app` — pronto para enviar à Dra. Lidiane.
- (Depois dá para apontar um subdomínio, ex.: `showroom.lidianefranca.com.br`, se quiser.)

## Observações
- Se a hospedagem exigir HTTPS/SSL, normalmente já vem ativo no domínio.
- Para trocar/atualizar, é só substituir o `index.html`.
- O site principal (editorial) está em `../index.html` — pode subir na raiz (`public_html/index.html`)
  para virar a home oficial, e o showroom fica em `/showroom/` como apresentação.
