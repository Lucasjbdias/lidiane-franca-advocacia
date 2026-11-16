# Apuração Presidente 2026: análise por seção eleitoral

Extração completa da votação para Presidente (1º turno em 04/10/2026, 2º turno em 25/10/2026) em todo o Brasil e no exterior (ZZ), seção por seção, a partir dos dados públicos do TSE.

**Painel interativo:** https://claude.ai/artifact/7KRiDzi85R77NkFSQFQnCf (o mesmo arquivo está em `saida_2026/painel.html` e abre em qualquer navegador).

## Fontes

- Portal de Dados Abertos do TSE (`cdn.tse.jus.br/estatistica/sead/odsele`)
  - `votacao_secao_2026_BR.zip`: votos por votável em cada seção (95 = branco, 96 = nulo)
  - `detalhe_votacao_secao_2026.zip` (arquivo `_BR.csv`): aptos, comparecimento e abstenção por seção
- API de resultados do TSE (`resultados.tse.jus.br`): totais oficiais usados para conferência e lista de candidatos válidos

## Conferência

A soma das 499.207 seções instaladas bate exatamente com o total oficial do TSE nos dois turnos, item por item: votos válidos, brancos, nulos, comparecimento, aptos, abstenções e votos de cada candidato. Os 5.246 votos do nº 28 no 1º turno são nulos técnicos (candidato fora da lista oficial de válidos) e entram como nulos, como na totalização oficial.

## Arquivos em `saida_2026/`

| Arquivo | Conteúdo |
|---|---|
| `uf_1t.csv`, `uf_2t.csv` | Totais e percentuais por UF |
| `municipios_1t.csv`, `municipios_2t.csv` | Totais e percentuais por município |
| `comparativo_municipios.csv` | 1º × 2º turno por município: variação em pontos percentuais, ganho de votos, viradas |
| `anomalias_{turno}_*.csv` | Seções fora do padrão do próprio município (3 desvios-padrão em nulos, brancos ou abstenção) e seções com 95% ou mais dos válidos para um candidato |
| `resumo.json` | Dados do painel |
| `painel.html` | Painel interativo (offline) |

Os arquivos por seção (`secoes_1t.csv.gz`, `secoes_2t.csv.gz`, `comparativo_secoes.csv.gz`, de 26 a 70 MB) não vão para o Git. Para gerá-los, rode o pipeline.

## Como rodar

Requer Python 3 com pandas e acesso a `cdn.tse.jus.br` e `resultados.tse.jus.br`.

```bash
./rodar.sh 2026      # baixa cerca de 480 MB, processa em cerca de 2 min e gera saida_2026/
```

Etapas avulsas: `python3 tse_pipeline.py probe|baixar|analisar --ano 2026 --dados DIR --saida DIR` e `python3 gerar_painel.py saida_2026`.
