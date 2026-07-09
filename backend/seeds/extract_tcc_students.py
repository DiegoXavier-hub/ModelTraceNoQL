"""Adapted TCC extraction pipeline applied to `D:\\alunos-vinculo-GI.xlsx`.

The notebook pipeline of the original TCC (nb01 -> nb02 -> nb03) was reused with
the necessary column renames for this raw export. The original TCC source under
`backend/seeds/source_projects/tcc-student-outcomes/` is **not modified**; this
script reads the raw spreadsheet at `D:\\alunos-vinculo-GI.xlsx` and writes a
JSON manifest at `backend/seeds/tcc_students_extracted.json` that the main seed
loads into the TCC project of the ModelTrace document store.

Mapping (alunos-vinculo-GI.xlsx -> TCC pipeline column names):
    MATR_ALUNO         -> matricula           (anonymized to id_aluno)
    NOME_PESSOA        -> nome                (dropped after anonymization)
    SITUACAO           -> situacao_disciplina (Aprovado, Reprovado, Dispensado, ...)
    FORMA_EVASAO       -> situacao_aluno      (Aluno com Vinculo, Abandono, ...)
    MEDIA_FINAL        -> nota
    CH_TOTAL           -> carga_horaria
    NOME_ATIV_CURRIC   -> nome_disciplina
    COD_ATIV_CURRIC    -> codigo_disciplina
    DESCR_ESTRUTURA    -> categoria_disciplina
    ANO + PERIODO_ITEM -> ano_disciplina + num_semestre_disc
    ANO_INGRESSO       -> ano_ingresso
    PERIODO_INGRESSO   -> num_semestre_ingresso
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_XLSX = Path(r"D:\alunos-vinculo-GI.xlsx")
OUTPUT_PATH = REPO_ROOT / "backend" / "seeds" / "tcc_students_extracted.json"

# Same salt the original TCC used (preserves identifier stability if the user
# ever wants to cross-reference with previous parquets).
SALT = "tcc_ufu_2026_dxavier"


# ---------------------------------------------------------------------------
# Mappings copied from the TCC nb01 (encoded with non-ascii to match the
# raw spreadsheet bytes after the latin-1/utf-8 dance).
# ---------------------------------------------------------------------------

MAPA_SITUACAO_ALUNO = {
    "Aluno com Vinculo": "Vinculado",
    "Aluno com Vínculo": "Vinculado",
    "Aluno com Vínculo": "Vinculado",
    "Abandono": "Abandono",
    "Desistente Oficial": "Desistente",
    "Desistente": "Desistente",
    "Jubilamento": "Jubilamento",
    "Desligamento": "Desligamento",
    "Transferencia Interna": "_EXCLUIR_TRANSFERENCIA",
    "Transferência Interna": "_EXCLUIR_TRANSFERENCIA",
    "Transferido": "_EXCLUIR_TRANSFERENCIA",
    "Falecimento": "_EXCLUIR_FALECIMENTO",
    "Cancelamento por indeferimento de renda": "_EXCLUIR_CANCELAMENTO",
    "Cancelamento Convenio": "_EXCLUIR_CANCELAMENTO",
    "Cancelamento Convênio": "_EXCLUIR_CANCELAMENTO",
}

MAPA_SITUACAO_DISCIPLINA = {
    "Aprovado": "Aprovado",
    "Apr. s/nt": "Aprovado sem Nota",
    "C/Aprov.": "Aprovado",
    "Aprov.Freq": "Aprovado por Frequencia",
    "Reprovado": "Reprovado por Nota",
    "Repr. RM": "Reprovado por Nota",
    "Repr. s/nt": "Reprovado sem Nota",
    "Repr.Freq.": "Reprovado por Frequencia",
    "Infrequent": "Reprovado por Frequencia",
    "Dispensado": "Dispensado",
    "Eq.curric.": "Equivalencia",
    "Tr. Total": "Aproveitamento Total",
    "Tr.Parcial": "Aproveitamento Parcial",
    "S/Aprov.": "Sem Aproveitamento",
    "Sem nota": "Sem Nota",
    "Vínculo": "Vinculo",
    "Vinculo": "Vinculo",
    "Matrícula": "Matricula",
    "Matricula": "Matricula",
    "Cursando": "Cursando",
}

GRUPO_SITUACAO = {
    "Aprovado": "aprovado",
    "Aprovado sem Nota": "aprovado",
    "Aprovado por Frequencia": "aprovado",
    "Reprovado por Nota": "reprovado",
    "Reprovado sem Nota": "reprovado",
    "Reprovado por Frequencia": "reprovado",
    "Dispensado": "dispensa",
    "Equivalencia": "dispensa",
    "Aproveitamento Total": "dispensa",
    "Aproveitamento Parcial": "dispensa",
    "Sem Aproveitamento": "sem_resultado",
    "Sem Nota": "sem_resultado",
    "Vinculo": "sem_resultado",
    "Matricula": "sem_resultado",
    "Cursando": "sem_resultado",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def anonimizar(valor: str | int) -> str:
    seed = f"{SALT}_{str(valor).strip()}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def fix_encoding(valor):
    if pd.isna(valor):
        return valor
    text = str(valor)
    try:
        repaired = text.encode("latin-1").decode("utf-8")
        return repaired
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text


def normalizar_chave(valor):
    if pd.isna(valor):
        return valor
    text = str(valor).strip()
    text = unicodedata.normalize("NFC", text)
    text = " ".join(text.split())
    return text


def safe_int(value, default=None):
    try:
        if pd.isna(value):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=None):
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def load_raw() -> pd.DataFrame:
    df = pd.read_excel(SOURCE_XLSX, sheet_name="relatorio")
    print(f"[extract] raw rows={len(df):,} students={df['MATR_ALUNO'].nunique():,}")

    # Repair latin-1 -> utf-8 mojibake for textual columns.
    text_cols = [
        "NOME_PESSOA",
        "NOME_UNIDADE",
        "SITUACAO_ITEM",
        "SITUACAO",
        "PERIODO",
        "NOME_ATIV_CURRIC",
        "DESCR_ESTRUTURA",
        "FORMA_EVASAO",
        "NOME_CURSO_DIPLOMA",
        "PERIODO_INGRESSO",
    ]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].apply(fix_encoding)
    return df


def to_canonical(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["id_aluno"] = df["MATR_ALUNO"].astype(str).apply(anonimizar)

    # Map status of the student (FORMA_EVASAO -> situacao_aluno).
    df["situacao_aluno_raw"] = df["FORMA_EVASAO"].apply(normalizar_chave)
    df["situacao_aluno"] = df["situacao_aluno_raw"].map(MAPA_SITUACAO_ALUNO)

    not_mapped = set(df["situacao_aluno_raw"].dropna().unique()) - set(MAPA_SITUACAO_ALUNO.keys())
    if not_mapped:
        print(f"[extract] WARNING: unmapped situacao_aluno values, treating as Vinculado: {not_mapped}")
    df["situacao_aluno"] = df["situacao_aluno"].fillna("Vinculado")

    # Excluded categories (transfer, deceased, cancellation): drop those students entirely.
    excluded = df[df["situacao_aluno"].str.startswith("_EXCLUIR_")]["id_aluno"].unique()
    before = df["id_aluno"].nunique()
    df = df[~df["id_aluno"].isin(excluded)].copy()
    print(f"[extract] excluded {len(excluded)} students "
          f"(transferencia/falecimento/cancelamento); remaining {df['id_aluno'].nunique()}/{before}")

    # Map disciplina status.
    df["situacao_disciplina_raw"] = df["SITUACAO"].apply(normalizar_chave)
    df["situacao_disciplina"] = df["situacao_disciplina_raw"].map(MAPA_SITUACAO_DISCIPLINA)
    df["grupo_situacao_disc"] = df["situacao_disciplina"].map(GRUPO_SITUACAO).fillna("sem_resultado")

    # Numerical fields.
    df["nota"] = pd.to_numeric(df["MEDIA_FINAL"], errors="coerce")
    df["carga_horaria"] = pd.to_numeric(df["CH_TOTAL"], errors="coerce")

    # Disciplina semester parsing.
    df["ano_disciplina"] = pd.to_numeric(df["ANO"], errors="coerce")

    def _periodo_to_num(value):
        if pd.isna(value):
            return None
        s = str(value)
        match = re.search(r"(\d)", s)
        return int(match.group(1)) if match else None

    df["num_semestre_disc"] = df["PERIODO_ITEM"].apply(
        lambda v: _periodo_to_num(v) if not isinstance(v, (int, float)) else int(v) if not pd.isna(v) else None
    )
    # PERIODO_ITEM in this export uses codes like 101/102/201/202. Map to semester number.
    def _decode_periodo_item(v):
        if pd.isna(v):
            return None
        s = str(v).strip()
        if s.isdigit():
            num = int(s)
            return num % 10 if num > 9 else num
        match = re.search(r"(\d)", s)
        return int(match.group(1)) if match else None

    df["num_semestre_disc"] = df["PERIODO_ITEM"].apply(_decode_periodo_item)

    df["num_semestre_ingresso"] = df["PERIODO_INGRESSO"].apply(_periodo_to_num)
    df["ano_ingresso"] = pd.to_numeric(df["ANO_INGRESSO"], errors="coerce")

    # Categoria (DESCR_ESTRUTURA repaired & title-cased).
    df["categoria_disciplina"] = df["DESCR_ESTRUTURA"].apply(normalizar_chave)

    # Periodo sequencial per student (used by TCC for janela P1/P2/P4 eligibility).
    df_seq = (
        df[["id_aluno", "ano_disciplina", "num_semestre_disc"]]
        .dropna()
        .drop_duplicates()
        .sort_values(["id_aluno", "ano_disciplina", "num_semestre_disc"])
    )
    df_seq["periodo_sequencial"] = df_seq.groupby("id_aluno").cumcount() + 1
    df = df.merge(
        df_seq[["id_aluno", "ano_disciplina", "num_semestre_disc", "periodo_sequencial"]],
        on=["id_aluno", "ano_disciplina", "num_semestre_disc"],
        how="left",
    )

    return df


def aggregate_per_student(df: pd.DataFrame) -> pd.DataFrame:
    """Reproduces the per-student feature engineering of TCC nb03."""
    df = df.copy()
    df["is_aprovado"] = (df["grupo_situacao_disc"] == "aprovado").astype(int)
    df["is_reprovado"] = (df["grupo_situacao_disc"] == "reprovado").astype(int)
    df["is_dispensa"] = (df["grupo_situacao_disc"] == "dispensa").astype(int)
    df["is_sem_resultado"] = (df["grupo_situacao_disc"] == "sem_resultado").astype(int)
    df["is_reprov_nota"] = (df["situacao_disciplina"] == "Reprovado por Nota").astype(int)
    df["is_reprov_freq"] = (df["situacao_disciplina"] == "Reprovado por Frequencia").astype(int)

    grouped = df.groupby("id_aluno", sort=False)

    # Notas restritas a disciplinas com nota valida (Aprovado/Reprovado com nota).
    notas_validas = df[df["nota"].notna()].groupby("id_aluno")["nota"]
    nota_media = notas_validas.mean()
    nota_mediana = notas_validas.median()
    nota_desvio = notas_validas.std().fillna(0.0)
    nota_min = notas_validas.min()
    nota_max = notas_validas.max()

    qtd_aprovacoes = grouped["is_aprovado"].sum()
    qtd_reprovacoes = grouped["is_reprovado"].sum()
    qtd_dispensas = grouped["is_dispensa"].sum()
    qtd_sem_resultado = grouped["is_sem_resultado"].sum()
    qtd_reprov_nota = grouped["is_reprov_nota"].sum()
    qtd_reprov_freq = grouped["is_reprov_freq"].sum()
    qtd_disciplinas_total = grouped.size()

    taxa_aprovacao = (qtd_aprovacoes / qtd_disciplinas_total.replace(0, pd.NA)).astype(float)
    max_periodo = grouped["periodo_sequencial"].max()
    media_disc_por_periodo = (
        qtd_disciplinas_total / max_periodo.replace(0, pd.NA)
    ).astype(float)
    ch_acumulada = (
        df[df["is_aprovado"] == 1].groupby("id_aluno")["carga_horaria"].sum()
    )
    ch_acumulada = ch_acumulada.reindex(qtd_disciplinas_total.index, fill_value=0.0)
    pct_ch_concluida = (ch_acumulada / 2950.0).clip(upper=1.0)

    # P1-specific features: only first sequential period.
    df_p1 = df[df["periodo_sequencial"] == 1]
    nota_p1_series = df_p1[df_p1["nota"].notna()].groupby("id_aluno")["nota"].mean()
    nota_p1 = nota_p1_series.reindex(qtd_disciplinas_total.index)
    reprov_p1 = df_p1.groupby("id_aluno")["is_reprovado"].sum().reindex(qtd_disciplinas_total.index, fill_value=0)
    disc_p1 = df_p1.groupby("id_aluno").size().reindex(qtd_disciplinas_total.index, fill_value=0)
    delta_nota = (nota_media - nota_p1).reindex(qtd_disciplinas_total.index)

    situacao_aluno = grouped["situacao_aluno"].first()
    ano_ingresso = grouped["ano_ingresso"].first()
    num_semestre_ingresso = grouped["num_semestre_ingresso"].first()
    categoria_aleatoria = grouped["categoria_disciplina"].first()

    out = pd.DataFrame({
        "id_aluno": qtd_disciplinas_total.index,
        "situacao_aluno": situacao_aluno.values,
        "ano_ingresso": ano_ingresso.values,
        "num_semestre_ingresso": num_semestre_ingresso.values,
        "max_periodo": max_periodo.values,
        "nota_media": nota_media.reindex(qtd_disciplinas_total.index).values,
        "nota_mediana": nota_mediana.reindex(qtd_disciplinas_total.index).values,
        "nota_desvio": nota_desvio.reindex(qtd_disciplinas_total.index).values,
        "nota_min": nota_min.reindex(qtd_disciplinas_total.index).values,
        "nota_max": nota_max.reindex(qtd_disciplinas_total.index).values,
        "qtd_aprovacoes": qtd_aprovacoes.values,
        "qtd_reprovacoes": qtd_reprovacoes.values,
        "qtd_dispensas": qtd_dispensas.values,
        "qtd_sem_resultado": qtd_sem_resultado.values,
        "qtd_reprov_nota": qtd_reprov_nota.values,
        "qtd_reprov_freq": qtd_reprov_freq.values,
        "taxa_aprovacao": taxa_aprovacao.values,
        "qtd_disciplinas_total": qtd_disciplinas_total.values,
        "media_disc_por_periodo": media_disc_por_periodo.values,
        "ch_acumulada": ch_acumulada.values,
        "nota_p1": nota_p1.values,
        "delta_nota": delta_nota.values,
        "reprov_p1": reprov_p1.values,
        "disc_p1": disc_p1.values,
        "pct_ch_concluida": pct_ch_concluida.values,
        "primeira_categoria": categoria_aleatoria.values,
    })
    return out


def derive_target(situacao_aluno: str) -> int | None:
    """y=1 evadiu, y=0 ativo/formado, None desconhecido."""
    if situacao_aluno in {"Abandono", "Desistente", "Jubilamento", "Desligamento"}:
        return 1
    if situacao_aluno in {"Vinculado"}:
        return None  # outcome not yet known
    return None


def main() -> None:
    if not SOURCE_XLSX.exists():
        raise SystemExit(f"Arquivo nao encontrado: {SOURCE_XLSX}")

    print(f"[extract] reading {SOURCE_XLSX}")
    raw = load_raw()
    canonical = to_canonical(raw)
    features = aggregate_per_student(canonical)
    features["y"] = features["situacao_aluno"].apply(derive_target)

    # Cast numpy types -> python primitives for JSON serialization.
    records = []
    for row in features.to_dict(orient="records"):
        rec = {}
        for key, value in row.items():
            if value is None or (isinstance(value, float) and pd.isna(value)):
                rec[key] = None
                continue
            if hasattr(value, "item"):
                rec[key] = value.item()
            else:
                rec[key] = value
        records.append(rec)

    by_status: dict[str, int] = {}
    by_target: dict[str, int] = {"evaded": 0, "active": 0, "unknown": 0}
    for rec in records:
        by_status[rec["situacao_aluno"]] = by_status.get(rec["situacao_aluno"], 0) + 1
        if rec["y"] == 1:
            by_target["evaded"] += 1
        elif rec["y"] == 0:
            by_target["active"] += 1
        else:
            by_target["unknown"] += 1

    manifest = {
        "source_xlsx": str(SOURCE_XLSX),
        "source_pdf": r"D:\alunos-vinculo-GI.pdf",
        "pipeline_origin": "Adapted from TCC notebooks nb01/nb02/nb03 (copied under "
                           "backend/seeds/source_projects/tcc-student-outcomes/).",
        "salt": SALT,
        "student_count": len(records),
        "status_distribution": dict(sorted(by_status.items(), key=lambda kv: -kv[1])),
        "target_distribution": by_target,
        "students": records,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"[extract] wrote {OUTPUT_PATH} ({size_kb:.1f} KB)")
    print(f"[extract] students={len(records)} | status={by_status} | target={by_target}")


if __name__ == "__main__":
    main()
