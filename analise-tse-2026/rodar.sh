#!/usr/bin/env bash
# Extração completa Presidente (1º e 2º turno), Brasil. Uso: ./rodar.sh [ANO]
set -euo pipefail
ANO="${1:-2026}"; DIR="$(cd "$(dirname "$0")" && pwd)"
python3 -I "$DIR/tse_pipeline.py" probe   --ano "$ANO"
python3 -I "$DIR/tse_pipeline.py" baixar  --ano "$ANO" --dados "$DIR/dados_$ANO"
python3 -I "$DIR/tse_pipeline.py" analisar --ano "$ANO" --dados "$DIR/dados_$ANO" --saida "$DIR/saida_$ANO"
python3 -I "$DIR/gerar_painel.py" "$DIR/saida_$ANO"
