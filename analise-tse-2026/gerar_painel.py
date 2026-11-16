#!/usr/bin/env python3
"""Gera o painel HTML a partir de saida/resumo.json.

Uso: python3 -I gerar_painel.py SAIDA_DIR [--exemplo]
"""
import json
import sys
from pathlib import Path

TEMPLATE = Path(__file__).with_name("painel_template.html")


def main():
    saida = Path(sys.argv[1])
    exemplo = "--exemplo" in sys.argv
    dados = json.loads((saida / "resumo.json").read_text())
    dados["exemplo"] = exemplo
    js = json.dumps(dados, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    cab = '<!DOCTYPE html>\n<html lang="pt-BR"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    html = cab + TEMPLATE.read_text().replace("__DADOS__", js).replace("__ANO__", str(dados["ano"]))
    destino = saida / "painel.html"
    destino.write_text(html)
    print(f"painel: {destino} ({destino.stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
