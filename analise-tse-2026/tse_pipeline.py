#!/usr/bin/env python3
"""Extração e análise da votação para Presidente por seção (1º e 2º turno) — Brasil.

Fonte: Portal de Dados Abertos do TSE (cdn.tse.jus.br/estatistica/sead/odsele)
  - votacao_secao_{ANO}_BR.zip   -> votos por votável (candidato, 95=branco, 96=nulo) por seção
  - detalhe_votacao_secao_{ANO}.zip -> aptos, comparecimento, abstenção, brancos, nulos por seção

Uso:
  python3 -I tse_pipeline.py probe   --ano 2026
  python3 -I tse_pipeline.py baixar  --ano 2026 --dados DIR
  python3 -I tse_pipeline.py analisar --ano 2026 --dados DIR --saida DIR
"""
import argparse
import io
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import pandas as pd

BASE = "https://cdn.tse.jus.br/estatistica/sead/odsele"
UFS = ("AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO ZZ").split()
CD_PRESIDENTE = 1
BRANCO, NULO = 95, 96
CHAVE = ["NR_TURNO", "SG_UF", "CD_MUNICIPIO", "NM_MUNICIPIO", "NR_ZONA", "NR_SECAO"]


def urls(ano):
    return {
        "votacao": [f"{BASE}/votacao_secao/votacao_secao_{ano}_BR.zip"]
        + [f"{BASE}/votacao_secao/votacao_secao_{ano}_{uf}.zip" for uf in UFS],
        "detalhe": [f"{BASE}/detalhe_votacao_secao/detalhe_votacao_secao_{ano}.zip"],
    }


def curl(args):
    return subprocess.run(["curl", "-sS", "-L", "--retry", "4", "--retry-delay", "2", *args],
                          capture_output=True, text=True)


RESULTADOS = "https://resultados.tse.jus.br/oficial"


def _json(url):
    r = curl(["-f", "-m", "60", url])
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout else None


def oficial(ano):
    """Totais oficiais de Presidente por turno, da API de resultados (para validar e achar nulos técnicos)."""
    cfg = _json(f"{RESULTADOS}/comum/config/ele-c.json")
    if not cfg:
        return {}
    out = {}
    for pl in cfg.get("pl", []):
        if pl.get("c") != f"ele{ano}":
            continue
        for e in pl.get("e", []):
            if not any(cp.get("cd") == str(CD_PRESIDENTE) for a in e.get("abr", []) for cp in a.get("cp", [])):
                continue
            cd = e["cd"]
            d = _json(f"{RESULTADOS}/ele{ano}/{cd}/dados/br/br-c{CD_PRESIDENTE:04d}-e{int(cd):06d}-u.json")
            if not d:
                continue
            cands = {}

            def walk(o):
                if isinstance(o, dict):
                    if "sqcand" in o and "vap" in o:
                        cands[int(o["n"])] = {"nome": o.get("nmu") or o.get("nm"), "votos": int(o["vap"]),
                                              "situacao": o.get("dvt")}
                    for v in o.values():
                        walk(v)
                elif isinstance(o, list):
                    for v in o:
                        walk(v)
            walk(d)
            v, el = d.get("v", {}), d.get("e", {})
            out[int(e["t"])] = {"cd_eleicao": cd, "gerado": f"{d.get('dg')} {d.get('hg')}", "candidatos": cands,
                                "validos": int(v.get("vv", 0)), "brancos": int(v.get("vb", 0)),
                                "nulos": int(v.get("tvn", 0)), "nulos_tecnicos": int(v.get("vnt", 0)),
                                "comparecimento": int(el.get("c", 0)), "abstencoes": int(el.get("a", 0)),
                                "aptos": int(el.get("esi", 0) or 0), "secoes": int(d.get("s", {}).get("si", 0))}
    return out


def probe(ano):
    for tipo, lista in urls(ano).items():
        for u in lista[:2]:
            r = curl(["-I", "-m", "30", "-o", "/dev/null", "-w", "%{http_code} %{size_download}", u])
            print(f"{tipo:8} {r.stdout or r.stderr.strip()}  {u}")


def baixar(ano, dados):
    dados.mkdir(parents=True, exist_ok=True)
    u = urls(ano)
    # votação: tenta o arquivo BR único; se não existir, baixa por UF
    alvo_br = dados / Path(u["votacao"][0]).name
    if _baixa(u["votacao"][0], alvo_br):
        print("votacao BR ok")
    else:
        for url in u["votacao"][1:]:
            _baixa(url, dados / Path(url).name)
    _baixa(u["detalhe"][0], dados / Path(u["detalhe"][0]).name)


def _baixa(url, destino):
    if destino.exists() and zipfile.is_zipfile(destino):
        return True
    tmp = destino.with_suffix(".part")
    r = curl(["-f", "-C", "-", "-o", str(tmp), url])
    if r.returncode != 0 or not zipfile.is_zipfile(tmp):
        print(f"falhou: {url} {r.stderr.strip()}", file=sys.stderr)
        tmp.unlink(missing_ok=True)
        return False
    tmp.rename(destino)
    print(f"baixado: {destino.name} ({destino.stat().st_size/1e6:.0f} MB)")
    return True


NUMERICAS = {"NR_TURNO", "CD_MUNICIPIO", "NR_ZONA", "NR_SECAO", "CD_CARGO", "NR_VOTAVEL", "QT_VOTOS",
             "NR_LOCAL_VOTACAO", "QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES", "QT_VOTOS_NOMINAIS",
             "QT_VOTOS_BRANCOS", "QT_VOTOS_NULOS", "QT_VOTOS_ANULADOS_APU_SEP"}


def _ler_zip(caminho, colunas, apenas=None):
    """Lê os CSVs de um zip em blocos, mantendo só linhas de Presidente.

    `apenas` restringe aos arquivos com esse sufixo: no detalhe_votacao_secao a votação
    para Presidente fica só no *_BR.csv (os arquivos por UF trazem os cargos estaduais).
    """
    partes = []
    with zipfile.ZipFile(caminho) as z:
        nomes = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if apenas:
            nomes = [n for n in nomes if n.endswith(apenas)]
        for nome in nomes:
            with z.open(nome) as f:
                txt = io.TextIOWrapper(f, encoding="latin-1")
                for bloco in pd.read_csv(txt, sep=";", dtype=str, chunksize=2_000_000,
                                         usecols=lambda c: c in colunas):
                    bloco = bloco[bloco["CD_CARGO"] == str(CD_PRESIDENTE)]
                    for c in bloco.columns:
                        if c in NUMERICAS:
                            bloco[c] = pd.to_numeric(bloco[c], errors="coerce").fillna(-1).astype("int64")
                        else:
                            bloco[c] = bloco[c].astype("category")
                    if len(bloco):
                        partes.append(bloco)
    if not partes:
        return pd.DataFrame(columns=colunas)
    df = pd.concat(partes, ignore_index=True)
    for c in df.columns:
        if c not in NUMERICAS:
            df[c] = df[c].astype("category")
    return df


def carregar(dados, ano):
    zips_vot = sorted(dados.glob(f"votacao_secao_{ano}_*.zip"))
    br = [z for z in zips_vot if z.name.endswith("_BR.zip")]
    zips_vot = br or zips_vot
    cols_v = CHAVE + ["CD_CARGO", "NR_VOTAVEL", "NM_VOTAVEL", "QT_VOTOS"]
    vot = pd.concat([_ler_zip(z, cols_v) for z in zips_vot], ignore_index=True)
    cols_d = CHAVE + ["CD_CARGO", "QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES", "QT_VOTOS_NOMINAIS",
                      "QT_VOTOS_BRANCOS", "QT_VOTOS_NULOS", "QT_VOTOS_ANULADOS_APU_SEP", "ST_SECAO_INSTALADA"]
    det_zip = dados / f"detalhe_votacao_secao_{ano}.zip"
    det = None
    if det_zip.exists():
        det = _ler_zip(det_zip, cols_d, apenas="_BR.csv")
        if det.empty:  # formato antigo: Presidente espalhado nos arquivos por UF
            det = _ler_zip(det_zip, cols_d)
    return vot, det


def montar_secoes(vot, det, nulos_tecnicos=()):
    """`nulos_tecnicos`: números de votáveis cujos votos o TSE apura como nulos (registro não válido)."""
    vot = vot.copy()
    for c in ["SG_UF", "NM_MUNICIPIO"]:
        vot[c] = vot[c].astype(str)
    nomes = (vot[~vot["NR_VOTAVEL"].isin([BRANCO, NULO, 97, *nulos_tecnicos])]
             .groupby("NR_VOTAVEL", observed=True)["NM_VOTAVEL"].first().astype(str).to_dict())
    especiais = {BRANCO: "BRANCOS", NULO: "NULOS", 97: "ANULADOS", **{n: "NULOS_TECNICOS" for n in nulos_tecnicos}}
    vot["COL"] = vot["NR_VOTAVEL"].map({n: especiais.get(n, f"V_{n}") for n in vot["NR_VOTAVEL"].unique()})
    sec = vot.groupby(CHAVE + ["COL"])["QT_VOTOS"].sum().unstack("COL", fill_value=0).reset_index()
    sec.columns.name = None
    for c in ["BRANCOS", "NULOS", "NULOS_TECNICOS"]:
        if c not in sec:
            sec[c] = 0
    sec["NULOS"] += sec["NULOS_TECNICOS"]  # total de nulos, como o TSE divulga
    vcols = [c for c in sec.columns if c.startswith("V_")]
    sec["VALIDOS"] = sec[vcols].sum(axis=1)
    if det is not None and len(det):
        d = det.copy()
        for c in ["SG_UF", "NM_MUNICIPIO"]:
            d[c] = d[c].astype(str)
        num = ["QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES"]
        if "ST_SECAO_INSTALADA" in d:  # seções não instaladas não entram nos aptos oficiais
            d = d[d["ST_SECAO_INSTALADA"].astype(str).str.upper().str.startswith("S")]
        d = d.groupby(CHAVE, as_index=False)[num].sum()
        # outer: inclui seções instaladas sem nenhum voto (só existem no detalhe)
        sec = sec.merge(d, on=CHAVE, how="outer")
        votos = [c for c in sec.columns if c.startswith("V_")] + ["BRANCOS", "NULOS", "NULOS_TECNICOS", "VALIDOS"]
        votos += [c for c in ["ANULADOS"] if c in sec]
        sec[votos] = sec[votos].fillna(0).astype("int64")
        sec[num] = sec[num].fillna(0).astype("int64")
        sec = sec.rename(columns={"QT_APTOS": "APTOS", "QT_COMPARECIMENTO": "COMPARECIMENTO",
                                  "QT_ABSTENCOES": "ABSTENCOES"})
    else:
        sec["COMPARECIMENTO"] = sec["VALIDOS"] + sec["BRANCOS"] + sec["NULOS"]
        sec["APTOS"] = pd.NA
        sec["ABSTENCOES"] = pd.NA
    return sec, nomes


def taxas(df, vcols):
    df = df.copy()
    tot = df["VALIDOS"] + df["BRANCOS"] + df["NULOS"]
    df["PCT_VALIDOS"] = df["VALIDOS"] / tot * 100
    df["PCT_BRANCOS"] = df["BRANCOS"] / tot * 100
    df["PCT_NULOS"] = df["NULOS"] / tot * 100
    if "APTOS" in df and df["APTOS"].notna().any():
        df["PCT_ABSTENCAO"] = df["ABSTENCOES"] / df["APTOS"] * 100
    for c in vcols:
        df[f"PCT_{c}"] = df[c] / df["VALIDOS"].where(df["VALIDOS"] > 0) * 100
    df["VENCEDOR"] = df[vcols].idxmax(axis=1).where(df["VALIDOS"] > 0)
    return df


def agregar(sec, nivel, vcols):
    soma = vcols + ["VALIDOS", "BRANCOS", "NULOS", "APTOS", "COMPARECIMENTO", "ABSTENCOES"]
    soma = [c for c in soma if c in sec]
    g = sec.groupby(nivel, as_index=False)[soma].sum(min_count=1)
    g["N_SECOES"] = sec.groupby(nivel).size().values
    return taxas(g, vcols)


def analisar(ano, dados, saida):
    saida.mkdir(parents=True, exist_ok=True)
    vot, det = carregar(dados, ano)
    if vot.empty:
        sys.exit("sem dados de votação para Presidente — rode 'baixar' primeiro")
    of = oficial(ano)
    validos_of = {n for t in of.values() for n in t["candidatos"]}
    especiais = {BRANCO, NULO, 97}
    nt = sorted({int(n) for n in vot["NR_VOTAVEL"].unique()} - especiais - validos_of) if validos_of else []
    if nt:
        print(f"nulos técnicos (fora da lista oficial de válidos): {nt}")
    sec, nomes = montar_secoes(vot, det, nt)
    turnos = sorted(sec["NR_TURNO"].unique())
    res = {"ano": ano, "turnos": [int(t) for t in turnos], "candidatos": {}, "nacional": {}, "uf": {},
           "municipios": [], "anomalias": {}, "comparativo": {}, "nulos_tecnicos": nt,
           "oficial": {int(t): {k: v for k, v in o.items() if k != "candidatos"} for t, o in of.items()},
           "validacao": {}}

    por_turno = {}
    for t in turnos:
        s = sec[sec["NR_TURNO"] == t].copy()
        vcols = [c for c in s.columns if c.startswith("V_") and s[c].sum() > 0]
        s = s.drop(columns=[c for c in s.columns if c.startswith("V_") and c not in vcols])
        s = taxas(s, vcols)
        s.to_csv(saida / f"secoes_{t}t.csv.gz", index=False, compression="gzip")
        mun = agregar(s, ["SG_UF", "CD_MUNICIPIO", "NM_MUNICIPIO"], vcols)
        mun.to_csv(saida / f"municipios_{t}t.csv", index=False)
        uf = agregar(s, ["SG_UF"], vcols)
        uf.to_csv(saida / f"uf_{t}t.csv", index=False)
        s["_BR"] = "BR"
        br = agregar(s, ["_BR"], vcols).iloc[0]
        urna = {n: c["nome"] for o in of.values() for n, c in o["candidatos"].items()}  # nome de urna oficial
        res["candidatos"][int(t)] = {c: urna.get(int(c[2:])) or nomes.get(int(c[2:]), c) for c in vcols}
        res["nacional"][int(t)] = _limpa(br.drop("_BR").to_dict())
        res["uf"][int(t)] = [_limpa(r) for r in uf.to_dict("records")]
        res["anomalias"][int(t)] = anomalias(s, vcols, saida=saida)
        if int(t) in of:
            o = of[int(t)]
            chk = {"validos": (int(br["VALIDOS"]), o["validos"]), "brancos": (int(br["BRANCOS"]), o["brancos"]),
                   "nulos": (int(br["NULOS"]), o["nulos"]), "comparecimento": (int(br["COMPARECIMENTO"]), o["comparecimento"]),
                   "aptos": (int(br["APTOS"]), o["aptos"]), "abstencoes": (int(br["ABSTENCOES"]), o["abstencoes"]),
                   "secoes": (int(br["N_SECOES"]), o["secoes"])}
            chk.update({f"V_{n}": (int(br.get(f"V_{n}", 0)), c["votos"]) for n, c in o["candidatos"].items()})
            res["validacao"][int(t)] = {k: {"dados_abertos": a, "api_resultados": b, "diferenca": a - b}
                                        for k, (a, b) in chk.items()}
            dif = {k: a - b for k, (a, b) in chk.items() if a != b}
            print(f"turno {t}: validação vs API oficial -> {'idêntico' if not dif else dif}")
        por_turno[t] = (s, mun, vcols)

    if 1 in por_turno and 2 in por_turno:
        res["comparativo"] = comparar(por_turno[1], por_turno[2], saida)
        res["municipios"] = res["comparativo"].pop("_municipios")
    else:
        t = turnos[0]
        res["municipios"] = [_limpa(r) for r in por_turno[t][1].to_dict("records")]

    (saida / "resumo.json").write_text(json.dumps(res, ensure_ascii=False, default=str))
    print(f"ok: {len(sec):,} linhas seção×turno; saída em {saida}")
    return res


def anomalias(s, vcols, top=300, saida=None):
    """Seções fora do padrão do próprio município (z-score) e casos extremos.

    O painel recebe as `top` mais extremas de cada tipo; a lista completa vai para CSV.
    """
    s = s[(s["VALIDOS"] + s["BRANCOS"] + s["NULOS"]) >= 50].copy()
    grp = s.groupby(["SG_UF", "CD_MUNICIPIO"])
    listas = {}
    for col in ["PCT_NULOS", "PCT_BRANCOS"] + (["PCT_ABSTENCAO"] if "PCT_ABSTENCAO" in s else []):
        m, d = grp[col].transform("mean"), grp[col].transform("std")
        s[f"Z_{col}"] = (s[col] - m) / d.where(d > 0)
        fora = s[s[f"Z_{col}"] >= 3]  # 3 desvios-padrão acima da média do município
        listas[col] = (fora.sort_values(f"Z_{col}", ascending=False), col)
    mx = s[[f"PCT_{c}" for c in vcols]].max(axis=1)
    listas["concentracao_95"] = (s[mx >= 95].sort_values("VALIDOS", ascending=False), None)
    if "APTOS" in s and s["APTOS"].notna().any():
        listas["comparecimento_acima_aptos"] = (s[s["COMPARECIMENTO"] > s["APTOS"]], None)
    out = {k: _reg(df.head(top), vcols, col) for k, (df, col) in listas.items()}
    out["resumo"] = {k: int(len(df)) for k, (df, _) in listas.items()}
    if saida is not None:
        turno = int(s["NR_TURNO"].iloc[0])
        for k, (df, _) in listas.items():
            df.to_csv(saida / f"anomalias_{turno}t_{k.lower()}.csv", index=False)
    return out


def _reg(df, vcols, col):
    keep = CHAVE + ["VALIDOS", "BRANCOS", "NULOS", "PCT_NULOS", "PCT_BRANCOS"] + [f"PCT_{c}" for c in vcols]
    keep += [c for c in ["APTOS", "COMPARECIMENTO", "PCT_ABSTENCAO", f"Z_{col}" if col else None] if c and c in df]
    return [_limpa(r) for r in df[keep].to_dict("records")]


def comparar(t1, t2, saida):
    s1, m1, v1 = t1
    s2, m2, v2 = t2
    comuns = [c for c in v2 if c in v1]  # finalistas presentes nos dois turnos
    k = ["SG_UF", "CD_MUNICIPIO", "NM_MUNICIPIO"]
    m = m1.merge(m2, on=k, suffixes=("_1T", "_2T"))
    for c in ["PCT_NULOS", "PCT_BRANCOS", "PCT_ABSTENCAO"]:
        if f"{c}_1T" in m:
            m[f"DELTA_{c}"] = m[f"{c}_2T"] - m[f"{c}_1T"]
    m["VIROU"] = m["VENCEDOR_1T"] != m["VENCEDOR_2T"]
    for c in comuns:
        m[f"GANHO_{c}"] = m[f"{c}_2T"] - m[f"{c}_1T"]
        m[f"DELTA_PCT_{c}"] = m[f"PCT_{c}_2T"] - m[f"PCT_{c}_1T"]
    m.to_csv(saida / "comparativo_municipios.csv", index=False)

    ks = CHAVE[1:]
    sc = s1.merge(s2, on=ks, suffixes=("_1T", "_2T"))
    sc["VIROU"] = sc["VENCEDOR_1T"] != sc["VENCEDOR_2T"]
    sc["DELTA_PCT_NULOS"] = sc["PCT_NULOS_2T"] - sc["PCT_NULOS_1T"]
    sc.to_csv(saida / "comparativo_secoes.csv.gz", index=False, compression="gzip")

    # quanto cada finalista cresceu vs. votos "liberados" (eliminados + variação de brancos/nulos/abstenção)
    elim = [c for c in v1 if c not in comuns]
    nac = {
        "finalistas": comuns,
        "eliminados_votos_1T": int(s1[elim].sum().sum()) if elim else 0,
        "ganho_finalistas": {c: int(s2[c].sum() - s1[c].sum()) for c in comuns},
        "delta_brancos": int(s2["BRANCOS"].sum() - s1["BRANCOS"].sum()),
        "delta_nulos": int(s2["NULOS"].sum() - s1["NULOS"].sum()),
        "delta_comparecimento": int(s2["COMPARECIMENTO"].sum() - s1["COMPARECIMENTO"].sum()),
        "municipios_viraram": int(m["VIROU"].sum()),
        "secoes_viraram": int(sc["VIROU"].sum()),
        "secoes_comparadas": int(len(sc)),
    }
    cols = k + ["VIROU", "N_SECOES_2T", "APTOS_2T", "VENCEDOR_1T", "VENCEDOR_2T"]
    cols += [c for c in m.columns if c.startswith(("PCT_", "DELTA_", "GANHO_"))]
    cols = [c for c in dict.fromkeys(cols) if c in m]
    nac["_municipios"] = [_limpa(r) for r in m[cols].to_dict("records")]
    return nac


def _limpa(d):
    out = {}
    for k, v in d.items():
        if v is None or (isinstance(v, float) and v != v) or v is pd.NA:
            out[k] = None
        elif hasattr(v, "item"):
            v = v.item()
            out[k] = round(v, 3) if isinstance(v, float) else v
        else:
            out[k] = round(v, 3) if isinstance(v, float) else v
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("acao", choices=["probe", "baixar", "analisar"])
    p.add_argument("--ano", type=int, default=2026)
    p.add_argument("--dados", type=Path, default=Path("dados"))
    p.add_argument("--saida", type=Path, default=Path("saida"))
    a = p.parse_args()
    if a.acao == "probe":
        probe(a.ano)
    elif a.acao == "baixar":
        baixar(a.ano, a.dados)
    else:
        analisar(a.ano, a.dados, a.saida)
