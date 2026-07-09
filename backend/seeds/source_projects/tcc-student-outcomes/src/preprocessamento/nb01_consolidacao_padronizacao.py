import hashlib
import os
import re
import unicodedata
from pathlib import Path

import pandas as pd

PROJETO_ROOT = Path(__file__).resolve().parent.parent.parent
FONTES = PROJETO_ROOT / "data" / "raw"
SAIDA = PROJETO_ROOT / "data" / "preprocessamento"
SAIDA.mkdir(parents=True, exist_ok=True)

SEED = 42
SALT_ANONIMIZACAO = "tcc_ufu_2026_dxavier"

arquivos = {
    "ADM_Integral": FONTES / "ADM_Integral" / "Registros_ADM_Integral.xlsx",
    "ADM_Noturno":  FONTES / "ADM_Noturno"  / "Registros_ADM_Noturno.xlsx",
    "GI":           FONTES / "GI"           / "Registros_GI.xlsx",
}

dfs_brutos = {}
for curso, caminho in arquivos.items():
    df = pd.read_excel(caminho)
    df["curso_origem"] = curso
    dfs_brutos[curso] = df
    print(f"{curso}: {df.shape[0]:,} linhas, {df['matricula'].nunique():,} alunos, {len(df.columns)} colunas")

COLUNAS_LEAKAGE = [
    "data_diploma",
    "formado",
    "tem_data_diploma",
    "nota_valida",
    "ch_total_integralizada",
    "dilacao_semestres",
    "enade_status",
]

for curso, df in dfs_brutos.items():
    presentes = [c for c in COLUNAS_LEAKAGE if c in df.columns]
    dfs_brutos[curso] = df.drop(columns=presentes)
    print(f"{curso}: removidas {len(presentes)} colunas de leakage: {presentes}")

df_unificado = pd.concat(dfs_brutos.values(), ignore_index=True)
print(f"Base unificada: {df_unificado.shape[0]:,} linhas, {df_unificado['matricula'].nunique():,} matriculas")
print(f"Colunas: {list(df_unificado.columns)}")

def anonimizar_matricula(matricula, salt):
    valor = f"{salt}_{str(matricula).strip()}"
    return hashlib.sha256(valor.encode("utf-8")).hexdigest()[:16]

df_unificado["id_aluno"] = df_unificado["matricula"].astype(str).apply(
    lambda m: anonimizar_matricula(m, SALT_ANONIMIZACAO)
)

n_matriculas = df_unificado["matricula"].nunique()
n_hashes = df_unificado["id_aluno"].nunique()
assert n_matriculas == n_hashes, f"COLISAO DE HASH: {n_matriculas} matriculas -> {n_hashes} hashes"
print(f"Anonimizacao OK: {n_matriculas} matriculas -> {n_hashes} hashes unicos (0 colisoes)")

df_unificado = df_unificado.drop(columns=["matricula", "nome"])
print(f"Colunas 'matricula' e 'nome' removidas. Identificador anonimo: 'id_aluno'")

FONTE_CADASTRAL = FONTES / "11.02.02.80.04_Alunos-Evadidos_Curso-Ano_(ADM-Int-Not_GI)_1965-2025.xlsx"

def _fix_encoding(valor):
    if pd.isna(valor):
        return valor
    try:
        return str(valor).encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return str(valor)

cad = pd.read_excel(FONTE_CADASTRAL, sheet_name="relatorio")
for _col in ["SEXO", "FORMA_INGRESSO", "MODALIDADE_INGRESSO", "NATURALIDADE"]:
    cad[_col] = cad[_col].apply(_fix_encoding)

cad["id_aluno"] = cad["ALUNO_MATRICULA"].astype(str).apply(
    lambda m: anonimizar_matricula(m, SALT_ANONIMIZACAO)
)

cad["sexo"] = cad["SEXO"].map({"Masculino": "M", "Feminino": "F"})

cad["ALUNO_NASCIMENTO"] = pd.to_datetime(cad["ALUNO_NASCIMENTO"], errors="coerce")
cad["INGRESSO_DATA"] = pd.to_datetime(cad["INGRESSO_DATA"], errors="coerce")
cad["idade_ingresso"] = ((cad["INGRESSO_DATA"] - cad["ALUNO_NASCIMENTO"]).dt.days / 365.25).round(1)
cad.loc[(cad["idade_ingresso"] < 15) | (cad["idade_ingresso"] > 70), "idade_ingresso"] = pd.NA

def _map_forma(valor):
    if pd.isna(valor):
        return "Outros"
    s = str(valor)
    if "Vestibular" in s:
        return "Vestibular"
    if "SISU" in s:
        return "SISU"
    if "PAIES" in s or "PAAES" in s:
        return "PAIES_PAAES"
    if "Transfer" in s:
        return "Transferencia"
    if "Dipl" in s:
        return "Portador_Diploma"
    return "Outros"
cad["forma_ingresso_grp"] = cad["FORMA_INGRESSO"].apply(_map_forma)

def _map_cotista(valor):
    if pd.isna(valor):
        return pd.NA
    s = str(valor)
    if "Ampla" in s or "Não se aplica" in s or s.strip() == "AC":
        return 0
    if "Modalidade" in s or s.startswith("LI") or s.startswith("LB"):
        return 1
    return pd.NA
cad["cotista"] = cad["MODALIDADE_INGRESSO"].apply(_map_cotista).astype("Int64")

def _map_natural(valor):
    if pd.isna(valor):
        return pd.NA
    s = str(valor).strip().lower()
    return 1 if ("uberlândia" in s or "uberlandia" in s) else 0
cad["natural_uberlandia"] = cad["NATURALIDADE"].apply(_map_natural).astype("Int64")

cad_aluno = (
    cad[["id_aluno", "sexo", "idade_ingresso", "forma_ingresso_grp",
         "cotista", "natural_uberlandia"]]
    .drop_duplicates("id_aluno", keep="last")
)

n_antes_merge = df_unificado["id_aluno"].nunique()
df_unificado = df_unificado.merge(cad_aluno, on="id_aluno", how="left")
n_match = df_unificado.loc[df_unificado["sexo"].notna(), "id_aluno"].nunique()
print(f"Enriquecimento cadastral: {n_match:,}/{n_antes_merge:,} alunos com dados")
print(f"  sexo nulos: {df_unificado.drop_duplicates('id_aluno')['sexo'].isna().sum()}")
print(f"  idade_ingresso nulos: {df_unificado.drop_duplicates('id_aluno')['idade_ingresso'].isna().sum()}")
print(f"  cotista nulos: {df_unificado.drop_duplicates('id_aluno')['cotista'].isna().sum()}")

MAPA_SITUACAO_ALUNO = {
    "Formado":                                       "Formado",
    "Formado - Mandado de Seguran\u00e7a":           "Formado",
    "Abandono":                                      "Abandono",
    "Desistente Oficial":                            "Desistente",
    "Desistente":                                    "Desistente",
    "Jubilamento":                                   "Jubilamento",
    "Desligamento":                                  "Desligamento",
    "Desligamento Decis\u00e3o Judicial":            "Desligamento",
    "Transfer\u00eancia Interna":                    "_EXCLUIR_TRANSFERENCIA",
    "Transfer\u00eancia Interna - Migra\u00e7\u00e3o": "_EXCLUIR_TRANSFERENCIA",
    "Transferido":                                   "_EXCLUIR_TRANSFERENCIA",
    "Falecimento":                                   "_EXCLUIR_FALECIMENTO",
    "Cancelamento Conv\u00eanio":                    "_EXCLUIR_CANCELAMENTO",
    "Desligamento Conv\u00eanio":                    "_EXCLUIR_CANCELAMENTO",
    "Cancelamento de Matr\u00edcula - Mandado Seguran\u00e7a": "_EXCLUIR_CANCELAMENTO",
    "Cancelamento por indeferimento de renda":       "_EXCLUIR_CANCELAMENTO",
    "Ingressante/N\u00e3o Compareceu":               "_EXCLUIR_NAO_COMPARECEU",
}

valores_existentes = set(df_unificado["situacao_aluno"].dropna().unique())
valores_mapeados = set(MAPA_SITUACAO_ALUNO.keys())
nao_mapeados = valores_existentes - valores_mapeados
if nao_mapeados:
    print(f"ATENCAO - valores nao mapeados: {nao_mapeados}")
    for v in list(nao_mapeados):
        v_norm = unicodedata.normalize("NFC", v)
        if v_norm in MAPA_SITUACAO_ALUNO:
            MAPA_SITUACAO_ALUNO[v] = MAPA_SITUACAO_ALUNO[v_norm]
            nao_mapeados.discard(v)
        else:
            v_nfkd = unicodedata.normalize("NFKD", v)
            for k in MAPA_SITUACAO_ALUNO:
                if unicodedata.normalize("NFKD", k) == v_nfkd:
                    MAPA_SITUACAO_ALUNO[v] = MAPA_SITUACAO_ALUNO[k]
                    nao_mapeados.discard(v)
                    break

assert len(nao_mapeados) == 0, f"VALORES NAO MAPEADOS: {nao_mapeados}"
print("Todos os valores de situacao_aluno estao mapeados.")

df_unificado["situacao_aluno_padrao"] = df_unificado["situacao_aluno"].map(MAPA_SITUACAO_ALUNO)

alunos_antes = df_unificado["id_aluno"].nunique()
excluir_mask = df_unificado["situacao_aluno_padrao"].str.startswith("_EXCLUIR_")
alunos_excluidos = df_unificado.loc[excluir_mask, "id_aluno"].nunique()

print(f"\n--- Relatorio de exclusao por situacao_aluno ---")
for motivo in sorted(df_unificado.loc[excluir_mask, "situacao_aluno_padrao"].unique()):
    n = df_unificado.loc[df_unificado["situacao_aluno_padrao"] == motivo, "id_aluno"].nunique()
    originais = df_unificado.loc[df_unificado["situacao_aluno_padrao"] == motivo, "situacao_aluno"].unique()
    print(f"  {motivo}: {n} alunos (originais: {list(originais)})")

print(f"\nTotal de alunos ANTES: {alunos_antes}")
print(f"Total EXCLUIDOS: {alunos_excluidos}")
print(f"Total APOS exclusao: {alunos_antes - alunos_excluidos}")

df_unificado = df_unificado[~excluir_mask].copy()
df_unificado = df_unificado.drop(columns=["situacao_aluno"])
df_unificado = df_unificado.rename(columns={"situacao_aluno_padrao": "situacao_aluno"})

print(f"\nDistribuicao final (por aluno):")
dist = df_unificado.drop_duplicates("id_aluno")["situacao_aluno"].value_counts()
for sit, cnt in dist.items():
    print(f"  {sit}: {cnt} ({cnt/dist.sum()*100:.1f}%)")

MAPA_SITUACAO_DISCIPLINA = {
    "Aprovado":     "Aprovado",
    "Apr. s/nt":    "Aprovado sem Nota",
    "C/Aprov.":     "Aprovado",
    "Aprov.Freq":   "Aprovado por Frequencia",
    "Reprovado":    "Reprovado por Nota",
    "Repr. RM":     "Reprovado por Nota",
    "Repr. s/nt":   "Reprovado sem Nota",
    "Repr.Freq.":   "Reprovado por Frequencia",
    "Infrequent":   "Reprovado por Frequencia",
    "Dispensado":   "Dispensado",
    "Eq.curric.":   "Equivalencia",
    "Tr. Total":    "Aproveitamento Total",
    "Tr.Parcial":   "Aproveitamento Parcial",
    "S/Aprov.":     "Sem Aproveitamento",
    "Sem nota":     "Sem Nota",
    "V\u00ednculo": "Vinculo",
    "Matr\u00edcula": "Matricula",
    "Cursando":     "Cursando",
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

valores_disc = set(df_unificado["situacao_disciplina"].dropna().unique())
for v in list(valores_disc):
    if v not in MAPA_SITUACAO_DISCIPLINA:
        v_norm = unicodedata.normalize("NFC", v)
        if v_norm in MAPA_SITUACAO_DISCIPLINA:
            MAPA_SITUACAO_DISCIPLINA[v] = MAPA_SITUACAO_DISCIPLINA[v_norm]
        else:
            for k in list(MAPA_SITUACAO_DISCIPLINA.keys()):
                if unicodedata.normalize("NFKD", k) == unicodedata.normalize("NFKD", v):
                    MAPA_SITUACAO_DISCIPLINA[v] = MAPA_SITUACAO_DISCIPLINA[k]
                    break

nao_mapeados_disc = set(df_unificado["situacao_disciplina"].dropna().unique()) - set(MAPA_SITUACAO_DISCIPLINA.keys())
assert len(nao_mapeados_disc) == 0, f"NAO MAPEADOS: {nao_mapeados_disc}"

df_unificado["situacao_disciplina_padrao"] = df_unificado["situacao_disciplina"].map(MAPA_SITUACAO_DISCIPLINA)
df_unificado["grupo_situacao_disc"] = df_unificado["situacao_disciplina_padrao"].map(GRUPO_SITUACAO)

print("Distribuicao situacao_disciplina (padronizada):")
print(df_unificado["situacao_disciplina_padrao"].value_counts().to_string())
print(f"\nGrupos:")
print(df_unificado["grupo_situacao_disc"].value_counts().to_string())

df_unificado = df_unificado.drop(columns=["situacao_disciplina"])
df_unificado = df_unificado.rename(columns={"situacao_disciplina_padrao": "situacao_disciplina"})

def normalizar_texto(valor):
    if pd.isna(valor):
        return valor
    texto = str(valor).strip()
    texto = unicodedata.normalize("NFC", texto)
    texto = " ".join(texto.split())
    return texto if texto else pd.NA

COLUNAS_TEXTO = [
    "curso", "versao", "tipo_ingresso", "classificacao",
    "semestre_ingresso", "semestre_disciplina",
    "categoria_disciplina", "codigo_disciplina", "nome_disciplina",
]

for col in COLUNAS_TEXTO:
    if col in df_unificado.columns:
        df_unificado[col] = df_unificado[col].apply(normalizar_texto)

if "categoria_disciplina" in df_unificado.columns:
    df_unificado["categoria_disciplina"] = df_unificado["categoria_disciplina"].str.strip().str.title()

print("Valores unicos de curso_origem:", sorted(df_unificado["curso_origem"].unique()))
print("Valores unicos de categoria_disciplina:", sorted(df_unificado["categoria_disciplina"].dropna().unique()))
print("Valores unicos de tipo_ingresso:", sorted(df_unificado["tipo_ingresso"].dropna().unique()))

COLUNAS_LOGICAS_DEDUP = [
    "id_aluno", "semestre_disciplina", "codigo_disciplina",
    "nome_disciplina", "carga_horaria", "nota", "situacao_disciplina"
]

n_antes = len(df_unificado)
df_unificado = df_unificado.drop_duplicates(subset=COLUNAS_LOGICAS_DEDUP, keep="first")
n_depois = len(df_unificado)
n_removidas = n_antes - n_depois

print(f"Duplicatas removidas: {n_removidas:,} linhas ({n_removidas/n_antes*100:.2f}%)")
print(f"Linhas antes: {n_antes:,} -> depois: {n_depois:,}")

def extrair_ano_semestre(valor):
    if pd.isna(valor):
        return pd.NA, pd.NA
    match = re.search(r"(\d)[\u00b0\u00ba°o]\s*Semestre\s+de\s+(\d{4})", str(valor))
    if match:
        return int(match.group(2)), int(match.group(1))
    return pd.NA, pd.NA

resultado = df_unificado["semestre_disciplina"].apply(extrair_ano_semestre)
df_unificado["ano_disciplina"] = resultado.apply(lambda x: x[0]).astype("Int64")
df_unificado["num_semestre_disc"] = resultado.apply(lambda x: x[1]).astype("Int64")

temp = df_unificado[["id_aluno", "ano_disciplina", "num_semestre_disc"]].drop_duplicates()
temp = temp.dropna(subset=["ano_disciplina", "num_semestre_disc"])
temp = temp.sort_values(["id_aluno", "ano_disciplina", "num_semestre_disc"])
temp["periodo_sequencial"] = temp.groupby("id_aluno").cumcount() + 1
df_unificado = df_unificado.merge(
    temp[["id_aluno", "ano_disciplina", "num_semestre_disc", "periodo_sequencial"]],
    on=["id_aluno", "ano_disciplina", "num_semestre_disc"],
    how="left"
)

print(f"Periodo sequencial calculado. Max: {df_unificado['periodo_sequencial'].max()}")
print(f"Distribuicao de periodos (primeiros 10):")
dist_per = df_unificado.drop_duplicates(["id_aluno", "periodo_sequencial"])
print(dist_per["periodo_sequencial"].value_counts().sort_index().head(10).to_string())

def extrair_num_semestre_ingresso(valor):
    if pd.isna(valor):
        return pd.NA
    match = re.search(r"(\d)", str(valor))
    return int(match.group(1)) if match else pd.NA

df_unificado["num_semestre_ingresso"] = df_unificado["semestre_ingresso"].apply(
    extrair_num_semestre_ingresso
).astype("Int64")

print("Distribuicao semestre_ingresso:")
print(df_unificado.drop_duplicates("id_aluno")["num_semestre_ingresso"].value_counts().sort_index().to_string())

print("=" * 60)
print("VERIFICACOES DE SANIDADE")
print("=" * 60)

n_alunos = df_unificado["id_aluno"].nunique()
n_linhas = len(df_unificado)
print(f"Total de alunos: {n_alunos:,}")
print(f"Total de linhas: {n_linhas:,}")

for col in ["id_aluno", "situacao_aluno", "ano_ingresso", "curso_origem"]:
    n_nulos = df_unificado[col].isna().sum()
    assert n_nulos == 0, f"NULOS em {col}: {n_nulos}"
    print(f"  {col}: 0 nulos OK")

sit_por_aluno = df_unificado.groupby("id_aluno")["situacao_aluno"].nunique()
conflitos = sit_por_aluno[sit_por_aluno > 1]
assert len(conflitos) == 0, f"Alunos com multiplas situacoes: {len(conflitos)}"
print(f"  Cada aluno tem 1 unica situacao_aluno OK")

curso_por_aluno = df_unificado.groupby("id_aluno")["curso_origem"].nunique()
multi_curso = curso_por_aluno[curso_por_aluno > 1]
print(f"  Alunos em multiplos cursos: {len(multi_curso)}")

notas_validas = df_unificado["nota"].dropna()
print(f"  Notas: min={notas_validas.min()}, max={notas_validas.max()}, nulos={df_unificado['nota'].isna().sum():,}")
assert notas_validas.min() >= 0, "Nota negativa!"
assert notas_validas.max() <= 100, "Nota > 100!"
print(f"  Notas no intervalo [0, 100] OK")

ch = df_unificado["carga_horaria"].dropna()
assert ch.min() >= 0, "CH negativa!"
print(f"  Carga horaria >= 0 OK")

print("=" * 60)
print("TODAS AS VERIFICACOES PASSARAM")
print("=" * 60)

COLUNAS_FINAIS = [
    "id_aluno",
    "curso_origem", "versao", "situacao_aluno",
    "tipo_ingresso", "classificacao",
    "ano_ingresso", "num_semestre_ingresso",
    "data_ingresso_ufu", "reingresso_periodo",
    "sexo", "idade_ingresso", "forma_ingresso_grp",
    "cotista", "natural_uberlandia",
    "periodo_sequencial", "semestre_disciplina",
    "ano_disciplina", "num_semestre_disc",
    "categoria_disciplina", "codigo_disciplina", "nome_disciplina",
    "carga_horaria", "nota",
    "situacao_disciplina", "grupo_situacao_disc",
    "ies_origem_dispensa", "outro_curriculo",
    "ch_total_exigida",
]

for col in COLUNAS_FINAIS:
    assert col in df_unificado.columns, f"Coluna {col} nao encontrada!"

df_final = df_unificado[COLUNAS_FINAIS].copy()
df_final = df_final.sort_values(["id_aluno", "ano_disciplina", "num_semestre_disc", "codigo_disciplina"])
df_final = df_final.reset_index(drop=True)

saida_path = SAIDA / "base_consolidada_granular.parquet"
df_final.to_parquet(saida_path, index=False)

print(f"Base salva em: {saida_path}")
print(f"Shape final: {df_final.shape}")
print(f"Alunos: {df_final['id_aluno'].nunique():,}")
print(f"Tamanho: {os.path.getsize(saida_path) / 1024 / 1024:.2f} MB")
print(f"\nColunas ({len(COLUNAS_FINAIS)}):")
for col in COLUNAS_FINAIS:
    dtype = df_final[col].dtype
    nulos = df_final[col].isna().sum()
    print(f"  {col}: {dtype} ({nulos:,} nulos)")

print("\nNotebook 01 concluido com sucesso.")
