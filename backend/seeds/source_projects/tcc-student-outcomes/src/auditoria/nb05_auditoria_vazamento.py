from pathlib import Path
import pandas as pd
import numpy as np

PROJETO = Path(__file__).resolve().parent.parent.parent
DADOS = PROJETO / "data" / "preprocessamento"
SAIDA = Path(__file__).resolve().parent
SAIDA.mkdir(parents=True, exist_ok=True)

print("""
======================================================================
          DOCUMENTO FORMAL DO DESENHO PREDITIVO
          TCC - Modelagem Preditiva da Evasao Academica
======================================================================

1. UNIDADE DE OBSERVACAO
   - Uma linha por ALUNO (nao por disciplina, nao por semestre).
   - Cada aluno aparece uma unica vez no dataset.

2. VARIAVEL ALVO (y)
   - y = 0: aluno se formou (desfecho terminal = Formado)
   - y = 1: aluno evadiu (desfecho terminal em {Abandono, Desistente,
             Jubilamento, Desligamento})
   - Trata-se de evasao FINAL no curso, nao evasao no semestre seguinte
     nem em horizonte temporal especifico.
   - NOTA: a base contem apenas alunos com desfecho terminal. Alunos
     ainda em curso nao aparecem. Taxas sao condicionais ao desfecho.

3. INSTANTE DE CORTE DE INFORMACAO
   - Janela p2: modelo usa APENAS dados dos 2 primeiros periodos.
   - Janela p4: modelo usa APENAS dados dos 4 primeiros periodos.
   - NENHUMA variavel pode conter informacao posterior ao corte.
   - Pergunta-chave: "Se eu fosse um coordenador de curso e o aluno
     acabou de terminar o 2o (ou 4o) semestre, essa informacao ja
     estaria disponivel para mim?"

4. SPLIT TEMPORAL (CONGELADO)
   - Treino:    ano_ingresso <= 2015
   - Validacao:  ano_ingresso em {2016, 2017}
   - Teste:     ano_ingresso em {2018, 2019}
   - Excluidos: ano_ingresso >= 2020 (vies de observacao + COVID-19)
   - O split e por TEMPO DE INGRESSO, nao aleatorio.
   - Nenhum aluno aparece em mais de um conjunto.
   - O teste simula uso prospectivo real.

5. REGRAS DE INTEGRIDADE
   - Fit de preprocessamento (imputacao, encoding, scaling) APENAS no treino.
   - Hiperparametros otimizados APENAS com treino + validacao.
   - Threshold definido APENAS na validacao.
   - Teste tocado UMA UNICA VEZ, apos tudo congelado.
""")

ml_p2 = pd.read_parquet(DADOS / "ml_p2.parquet")
print(f"ml_p2: {ml_p2.shape[0]} alunos, {ml_p2.shape[1]} colunas")
print(f"Colunas: {list(ml_p2.columns)}")

auditoria = [
    {"coluna": "id_aluno",
     "origem": "SHA-256 da matricula (nb01)",
     "disponivel_no_corte": "Sim",
     "tipo": "identificador",
     "decisao": "EXCLUIR (nao e feature, e identificador)",
     "justificativa": "Hash anonimizado. Nao carrega informacao preditiva."},

    {"coluna": "y",
     "origem": "Derivado de situacao_aluno (nb02)",
     "disponivel_no_corte": "NAO",
     "tipo": "alvo",
     "decisao": "ALVO (nao e feature)",
     "justificativa": "E a variavel que queremos prever. Disponivel apenas apos o desfecho."},

    {"coluna": "situacao_aluno",
     "origem": "SIGAA  -- situacao final do aluno",
     "disponivel_no_corte": "NAO",
     "tipo": "leakage",
     "decisao": "EXCLUIR",
     "justificativa": "E o proprio desfecho do aluno (Formado, Abandono, etc.). "
                      "Codifica diretamente y. Leakage fatal."},

    {"coluna": "max_periodo",
     "origem": "max(periodo_sequencial) do aluno em TODA a trajetoria",
     "disponivel_no_corte": "NAO",
     "tipo": "leakage",
     "decisao": "EXCLUIR",
     "justificativa": "Conta quantos periodos o aluno cursou no total (ate 30). "
                      "Alunos formados tem max_periodo alto, evadidos precoces tem baixo. "
                      "Isso REVELA o desfecho. Em ml_p2, 97% tem max_periodo > 2  -- "
                      "informacao que nao existe no momento da previsao."},

    {"coluna": "curso_origem",
     "origem": "Curso de matricula (SIGAA)",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_categorica",
     "decisao": "INCLUIR",
     "justificativa": "Informacao de matricula. Disponivel desde o ingresso."},

    {"coluna": "tipo_ingresso",
     "origem": "Modalidade de ingresso (SIGAA)",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_categorica",
     "decisao": "INCLUIR",
     "justificativa": "Informacao de matricula. Disponivel desde o ingresso."},

    {"coluna": "ano_ingresso",
     "origem": "Ano de ingresso (SIGAA)",
     "disponivel_no_corte": "Sim",
     "tipo": "metadata_split",
     "decisao": "EXCLUIR (usado para split, nao como feature)",
     "justificativa": "Disponivel no ingresso, mas usado para definir treino/val/teste. "
                      "Incluir como feature seria redundante com o split temporal e "
                      "poderia criar dependencia espuria."},

    {"coluna": "num_semestre_ingresso",
     "origem": "Semestre de ingresso (1 ou 2) (SIGAA)",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_categorica",
     "decisao": "AVALIAR",
     "justificativa": "Informacao de matricula. Pode ter valor preditivo (ingressantes "
                      "no 2o semestre podem ter perfil diferente). Incluir como feature."},

    {"coluna": "versao",
     "origem": "Codigo do curriculo (SIGAA)",
     "disponivel_no_corte": "Sim",
     "tipo": "metadata",
     "decisao": "EXCLUIR (informacao de curriculo, nao preditiva diretamente)",
     "justificativa": "Constante por aluno, definido na matricula. Tem muitas categorias (25) "
                      "com poucos exemplos cada. A informacao util ja esta em ch_total_exigida "
                      "e curso_origem."},

    {"coluna": "ch_total_exigida",
     "origem": "CH total do curriculo (derivada de versao)",
     "disponivel_no_corte": "Sim",
     "tipo": "metadata",
     "decisao": "EXCLUIR (usada apenas para calcular pct_ch_concluida)",
     "justificativa": "Informacao de matricula (derivada do curriculo). Ja capturada "
                      "indiretamente via pct_ch_concluida. Incluir diretamente seria "
                      "redundante e confundiria o modelo com informacao de curriculo "
                      "em vez de desempenho academico."},

    {"coluna": "nota_media",
     "origem": "Media das notas nas disciplinas (periodos 1-p)",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_numerica",
     "decisao": "INCLUIR",
     "justificativa": "Calculada a partir dos registros de disciplina dentro da janela."},

    {"coluna": "nota_mediana",
     "origem": "Mediana das notas (periodos 1-p)",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_numerica",
     "decisao": "INCLUIR",
     "justificativa": "Calculada dentro da janela. Alta correlacao com nota_media (r=0.94) "
                      " -- modelos de arvore lidam bem com redundancia; LR usara regularizacao."},

    {"coluna": "nota_desvio",
     "origem": "Desvio padrao das notas (periodos 1-p)",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_numerica",
     "decisao": "INCLUIR",
     "justificativa": "Mede consistencia do desempenho. Calculada dentro da janela."},

    {"coluna": "nota_min",
     "origem": "Nota minima nas disciplinas (periodos 1-p)",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_numerica",
     "decisao": "INCLUIR",
     "justificativa": "Calculada dentro da janela. Captura a pior performance."},

    {"coluna": "nota_max",
     "origem": "Nota maxima nas disciplinas (periodos 1-p)",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_numerica",
     "decisao": "INCLUIR",
     "justificativa": "Calculada dentro da janela. Captura a melhor performance."},

    {"coluna": "qtd_aprovacoes",
     "origem": "Total de aprovacoes (periodos 1-p)",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_numerica",
     "decisao": "INCLUIR",
     "justificativa": "Contagem de disciplinas aprovadas dentro da janela."},

    {"coluna": "qtd_reprovacoes",
     "origem": "Total de reprovacoes (periodos 1-p)",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_numerica",
     "decisao": "INCLUIR",
     "justificativa": "Contagem de disciplinas reprovadas dentro da janela."},

    {"coluna": "qtd_dispensas",
     "origem": "Total de dispensas (periodos 1-p)",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_numerica",
     "decisao": "INCLUIR",
     "justificativa": "Contagem de dispensas dentro da janela."},

    {"coluna": "qtd_sem_resultado",
     "origem": "Disciplinas sem resultado (periodos 1-p)",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_numerica",
     "decisao": "INCLUIR",
     "justificativa": "Contagem dentro da janela. Valores baixos (media ~0.01)."},

    {"coluna": "qtd_reprov_nota",
     "origem": "Reprovacoes por nota (periodos 1-p)",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_numerica",
     "decisao": "INCLUIR",
     "justificativa": "Subconjunto de qtd_reprovacoes. Calculada dentro da janela."},

    {"coluna": "qtd_reprov_freq",
     "origem": "Reprovacoes por frequencia (periodos 1-p)",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_numerica",
     "decisao": "INCLUIR",
     "justificativa": "Subconjunto de qtd_reprovacoes. Forte sinal de desengajamento. "
                      "Calculada dentro da janela."},

    {"coluna": "taxa_aprovacao",
     "origem": "aprovacoes / (aprovacoes + reprovacoes) (periodos 1-p)",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_numerica",
     "decisao": "INCLUIR",
     "justificativa": "Razao calculada dentro da janela. Feature mais discriminativa (r_pb=-0.53)."},

    {"coluna": "qtd_disciplinas_total",
     "origem": "Total de disciplinas cursadas (periodos 1-p)",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_numerica",
     "decisao": "INCLUIR",
     "justificativa": "Contagem dentro da janela. Correlacao perfeita (r=1.0) com "
                      "media_disc_por_periodo  -- uma delas e redundante, mas modelos "
                      "de arvore lidam bem com isso."},

    {"coluna": "media_disc_por_periodo",
     "origem": "Media de disciplinas por periodo (periodos 1-p)",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_numerica",
     "decisao": "INCLUIR",
     "justificativa": "Derivada de qtd_disciplinas_total / numero de periodos na janela. "
                      "Correlacao perfeita com qtd_disciplinas_total."},

    {"coluna": "ch_acumulada",
     "origem": "CH acumulada em aprovacoes + dispensas (periodos 1-p)",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_numerica",
     "decisao": "INCLUIR",
     "justificativa": "CH de disciplinas aprovadas/dispensadas DENTRO da janela. "
                      "Verificado: ch_p2 <= ch_p4 para todos os alunos."},

    {"coluna": "nota_p1",
     "origem": "Media de notas no 1o periodo",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_numerica",
     "decisao": "INCLUIR",
     "justificativa": "Primeiro periodo esta sempre dentro da janela (p2 e p4)."},

    {"coluna": "delta_nota",
     "origem": "nota_ultimo_periodo - nota_p1 (dentro da janela)",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_numerica",
     "decisao": "INCLUIR",
     "justificativa": "Tendencia de nota entre primeiro e ultimo periodo da janela. "
                      "Em p2, e a diferenca entre 2o e 1o periodo."},

    {"coluna": "reprov_p1",
     "origem": "Reprovacoes no 1o periodo",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_numerica",
     "decisao": "INCLUIR",
     "justificativa": "Primeiro periodo esta dentro da janela. Forte sinal precoce."},

    {"coluna": "disc_p1",
     "origem": "Disciplinas cursadas no 1o periodo",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_numerica",
     "decisao": "INCLUIR",
     "justificativa": "Primeiro periodo esta dentro da janela."},

    {"coluna": "pct_ch_concluida",
     "origem": "ch_acumulada / ch_total_exigida",
     "disponivel_no_corte": "Sim",
     "tipo": "feature_numerica",
     "decisao": "INCLUIR",
     "justificativa": "Numerador (ch_acumulada) e calculado dentro da janela. "
                      "Denominador (ch_total_exigida) e informacao de matricula. Sem leakage."},
]

df_auditoria = pd.DataFrame(auditoria)

print("\n" + "=" * 100)
print("AUDITORIA DE VAZAMENTO  -- TABELA COMPLETA (30 colunas)")
print("=" * 100)

for _, row in df_auditoria.iterrows():
    disponivel = "[SIM]" if row["disponivel_no_corte"] == "Sim" else "[NAO]"
    print(f"\n  {row['coluna']}")
    print(f"    Origem: {row['origem']}")
    print(f"    Disponivel no corte: {disponivel}")
    print(f"    Tipo: {row['tipo']}")
    print(f"    Decisao: {row['decisao']}")
    print(f"    Justificativa: {row['justificativa']}")

print("\n" + "=" * 80)
print("RESUMO DA AUDITORIA")
print("=" * 80)

decisoes = df_auditoria["decisao"].apply(lambda x: x.split(" ")[0]).value_counts()
for dec, cnt in decisoes.items():
    cols = df_auditoria[df_auditoria["decisao"].str.startswith(dec)]["coluna"].tolist()
    print(f"\n  {dec}: {cnt} colunas")
    for c in cols:
        print(f"    - {c}")

leakage_cols = df_auditoria[df_auditoria["tipo"] == "leakage"]["coluna"].tolist()
print(f"\n[!] COLUNAS DE LEAKAGE CONFIRMADAS: {leakage_cols}")

excluir = df_auditoria[df_auditoria["decisao"].str.startswith("EXCLUIR") |
                        df_auditoria["decisao"].str.startswith("ALVO")]["coluna"].tolist()
print(f"\n[X] COLUNAS A EXCLUIR DO MODELO: {excluir}")

features = df_auditoria[df_auditoria["decisao"].str.startswith("INCLUIR") |
                         df_auditoria["decisao"].str.startswith("AVALIAR")]["coluna"].tolist()
print(f"\n[OK] FEATURES FINAIS PARA MODELAGEM ({len(features)}): {features}")

csv_path = SAIDA / "auditoria_vazamento.csv"
df_auditoria.to_csv(csv_path, index=False, encoding="utf-8-sig")
print(f"\nTabela salva em: {csv_path.name}")

print("\n" + "=" * 80)
print("CHECAGEM DESCRITIVA POR SPLIT")
print("=" * 80)

for janela in [2, 4]:
    print(f"\n{'='*60}")
    print(f"JANELA p{janela}")
    print(f"{'='*60}")

    splits = {}
    for nome in ["treino", "val", "teste"]:
        splits[nome] = pd.read_parquet(DADOS / f"{nome}_p{janela}.parquet")

    print(f"\n--- Tamanho e taxa de evasao ---")
    print(f"{'Split':<10} {'N':>6} {'Evasao':>8} {'Nao-ev':>8} {'Taxa':>8}")
    for nome, df in splits.items():
        n = len(df)
        ev = df["y"].sum()
        print(f"{nome:<10} {n:>6} {ev:>8} {n-ev:>8} {ev/n*100:>7.1f}%")

    print(f"\n--- Proporcao por curso ---")
    for nome, df in splits.items():
        dist = df["curso_origem"].value_counts(normalize=True).sort_index()
        partes = [f"{c}: {p*100:.1f}%" for c, p in dist.items()]
        print(f"  {nome:<10} {' | '.join(partes)}")

    print(f"\n--- Proporcao por tipo de ingresso ---")
    for nome, df in splits.items():
        dist = df["tipo_ingresso"].value_counts(normalize=True).sort_index()
        partes = [f"{c}: {p*100:.1f}%" for c, p in dist.items()]
        print(f"  {nome:<10} {' | '.join(partes)}")

    print(f"\n--- Missingness por split ---")
    features_num = [c for c in splits["treino"].columns
                    if c not in ["id_aluno", "y", "situacao_aluno", "max_periodo",
                                 "ano_ingresso", "num_semestre_ingresso", "versao",
                                 "ch_total_exigida", "curso_origem", "tipo_ingresso"]]
    for col in features_num:
        nulos = {nome: df[col].isna().sum() for nome, df in splits.items()}
        if any(v > 0 for v in nulos.values()):
            partes = [f"{nome}: {n} ({n/len(splits[nome])*100:.1f}%)"
                      for nome, n in nulos.items() if n > 0]
            print(f"  {col:<25} {' | '.join(partes)}")

    print(f"\n--- Medias de features-chave por split ---")
    features_chave = ["nota_media", "taxa_aprovacao", "qtd_reprovacoes",
                       "pct_ch_concluida", "nota_p1", "reprov_p1"]
    print(f"{'Feature':<25} {'Treino':>10} {'Val':>10} {'Teste':>10} {'Drift%':>10}")
    for col in features_chave:
        medias = {nome: df[col].mean() for nome, df in splits.items()}
        drift = ((medias["teste"] - medias["treino"]) / medias["treino"] * 100
                 if medias["treino"] != 0 else 0)
        print(f"{col:<25} {medias['treino']:>10.3f} {medias['val']:>10.3f} "
              f"{medias['teste']:>10.3f} {drift:>+9.1f}%")

META_COLS = ["id_aluno", "y", "situacao_aluno", "max_periodo",
             "ano_ingresso", "num_semestre_ingresso", "versao", "ch_total_exigida"]

CAT_FEATURES = ["curso_origem", "tipo_ingresso"]

NUM_FEATURES = ["nota_media", "nota_mediana", "nota_desvio", "nota_min", "nota_max",
                "qtd_aprovacoes", "qtd_reprovacoes", "qtd_dispensas", "qtd_sem_resultado",
                "qtd_reprov_nota", "qtd_reprov_freq", "taxa_aprovacao",
                "qtd_disciplinas_total", "media_disc_por_periodo", "ch_acumulada",
                "nota_p1", "delta_nota", "reprov_p1", "disc_p1", "pct_ch_concluida"]

ALL_FEATURES = CAT_FEATURES + NUM_FEATURES

print(f"\n{'='*60}")
print("DEFINICAO FORMAL DAS FEATURES")
print(f"{'='*60}")
print(f"\nMetadata (excluidas do modelo): {len(META_COLS)} colunas")
for c in META_COLS:
    print(f"  - {c}")
print(f"\nFeatures categoricas: {len(CAT_FEATURES)} colunas")
for c in CAT_FEATURES:
    print(f"  - {c}")
print(f"\nFeatures numericas: {len(NUM_FEATURES)} colunas")
for c in NUM_FEATURES:
    print(f"  - {c}")
print(f"\nTotal de features para modelagem: {len(ALL_FEATURES)}")

for janela in [2, 4]:
    df = pd.read_parquet(DADOS / f"treino_p{janela}.parquet")
    for col in ALL_FEATURES:
        assert col in df.columns, f"ERRO: {col} nao encontrada em treino_p{janela}!"
    print(f"\n[OK] Todas as {len(ALL_FEATURES)} features encontradas em treino_p{janela}")

print(f"\n{'='*80}")
print("VERIFICACAO FINAL  -- INTEGRIDADE DO DESENHO PREDITIVO")
print(f"{'='*80}")

checks = []

for col in ["situacao_aluno", "max_periodo", "y"]:
    ok = col not in ALL_FEATURES
    checks.append(("Leakage/alvo nao esta nas features", col, ok))

for janela in [2, 4]:
    for split in ["treino", "val", "teste"]:
        df = pd.read_parquet(DADOS / f"{split}_p{janela}.parquet")
        for col in ALL_FEATURES:
            ok = col in df.columns
            checks.append((f"Feature existe em {split}_p{janela}", col, ok))

for janela in [2, 4]:
    treino = pd.read_parquet(DADOS / f"treino_p{janela}.parquet")
    val = pd.read_parquet(DADOS / f"val_p{janela}.parquet")
    teste = pd.read_parquet(DADOS / f"teste_p{janela}.parquet")

    overlap_tv = set(treino["id_aluno"]) & set(val["id_aluno"])
    overlap_tt = set(treino["id_aluno"]) & set(teste["id_aluno"])
    overlap_vt = set(val["id_aluno"]) & set(teste["id_aluno"])

    checks.append((f"Sem overlap treino-val p{janela}", f"{len(overlap_tv)} alunos", len(overlap_tv) == 0))
    checks.append((f"Sem overlap treino-teste p{janela}", f"{len(overlap_tt)} alunos", len(overlap_tt) == 0))
    checks.append((f"Sem overlap val-teste p{janela}", f"{len(overlap_vt)} alunos", len(overlap_vt) == 0))

for janela in [2, 4]:
    treino = pd.read_parquet(DADOS / f"treino_p{janela}.parquet")
    pct_acima = (treino["max_periodo"] > janela).mean() * 100
    checks.append((f"max_periodo > {janela} no treino p{janela} (confirma leakage)",
                    f"{pct_acima:.1f}% dos alunos", pct_acima > 50))

n_ok = sum(1 for _, _, ok in checks if ok)
n_total = len(checks)

for desc, detalhe, ok in checks:
    status = "[OK]" if ok else "[FALHA]"
    print(f"  {status} {desc}: {detalhe}")

print(f"\n{'='*40}")
print(f"RESULTADO: {n_ok}/{n_total} verificacoes OK")
if n_ok == n_total:
    print("[OK] AUDITORIA APROVADA -- pode prosseguir para modelagem")
else:
    print("[FALHA] AUDITORIA REPROVADA -- corrigir problemas antes de modelar")

print("\nNotebook 05 concluido.")
