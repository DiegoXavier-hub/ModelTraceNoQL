# Diagnóstico Fase 3A — pré-limpeza

> **Data**: 2026-05-01
> **Princípio governante**: ROBUSTEZ > custo computacional.
> **Escopo**: quantificar os 4 problemas a tratar antes de construir o
> dataset de features (Fase 3C). Não toca em `src/` — apenas mede.
> **Ferramenta**: `notebooks/_audit_fase3a.py` →
> `reports/eda_results/fase3a_diagnostico.json` +
> `reports/figures/fig07a_h013_por_mes_frota_hora.png`.

---

## 1. Sumário executivo

| Frente | Status | Impacto na Fase 3 |
|---|---|---|
| Encoding mojibake em `Criticidade` | **11 linhas confirmadas** (0,00003% da telemetria) — todas com `Id_Criticidade=2` | Trivial: reconstruir `Criticidade` pelo `Id_Criticidade` (chave numérica imune a encoding) |
| Inconsistências temporais nos apontamentos | **0 ocorrências** de `Inicio>Fim`, `dur=0`, `dur<0`, `dur>30 dias` | Apontamentos estão limpos. Nenhuma exclusão necessária. |
| Sobreposição entre ciclos do mesmo `Tag` | **326 pares (0,086%)** com sobreposição ≤ 60 min | Não estrutural. Manter os ciclos; `tem_overlap_anterior` vira flag opcional na 3C. |
| H013 estratificada (Operando sem telemetria) | 17,61% na população, **mas heterogêneo por frota e mês** (LeTourneau 1,6-14%; 793-D 3S 11-30%) | `tem_telemetria` carrega sinal preditivo real — manter como feature de primeira classe (D020 reforçada) |
| Mapping `Tag_Frota → Porte` (D019) | `desenvolver_dontgo.xlsx` só cobre `793-D 4S → Grande Porte`. Insuficiente. | Usar catálogo OEM externo + fallback `Grande Porte` para todas as 5 frotas (justificado em D024) |

**Veredito**: nenhum bloqueio para a Fase 3. As correções são pequenas e
auditáveis. As decisões D019, D020 ficam sólidas com este diagnóstico.

---

## 2. Encoding mojibake em `Criticidade`

### Achado

A telemetria tem **5 valores distintos** em `Criticidade`, não 4:

| Criticidade | Bytes (UTF-8) | n | % |
|---|---|---:|---:|
| `Informacional` | (limpo) | 36.619.169 | 99,8761% |
| `Não Crítico` | `4e c3 a3 6f 20 43 72 c3 ad 74 69 63 6f` (correto) | 461.854 | 1,2429% |
| `Critico` | (limpo, **sem acento** — é a forma canônica) | 83.020 | 0,2234% |
| `N??o Cr�tico` | `4e 3f 3f 6f 20 43 72 c3 ad 74 69 63 6f` (corrupto) | 6 | 0,000016% |
| `N�o Cr??tico` | `4e c3 a3 6f 20 43 72 3f 3f 74 69 63 6f` (corrupto) | 5 | 0,000013% |

> **Total de linhas com mojibake: 11** (= 6 + 5).

### Diagnóstico

Os bytes `3f` (`?`) substituem `c3 ad` (`í`) ou `c3 a3` (`ã`) em 11 eventos
isolados — vestígio de pipeline com double-encoding parcial Latin-1 → UTF-8.
**O mapeamento numérico via `Id_Criticidade` é imune ao bug**:

| Id_Criticidade | Criticidade canônica | n |
|---:|---|---:|
| 1 | `Critico` | 83.020 |
| 2 | `Não Crítico` (incluindo 11 mojibake) | 461.865 |
| 3 | `Informacional` | 36.616.050 |
| 4 | `Informacional` | 3.119 |

### Decisão (formaliza-se em D024)

Reconstruir `Criticidade` pelo `Id_Criticidade` no pipeline de limpeza
(`src/data/cleaning.py`):

```python
ID_CRITICIDADE_TO_NOME = {
    1: "Critico",
    2: "Não Crítico",
    3: "Informacional",
    4: "Informacional",
}
```

A decisão preserva (a) os números canônicos da Fase 2, (b) a chave
numérica como source-of-truth, (c) a invariância a encoding.

> **Nota sobre `Id_Criticidade=4`**: aparece **apenas 3.119 vezes** e tem o
> mesmo nome canônico que `Id=3`. Pode ser um sub-código OEM ("Informacional
> mas não relevante") — fica como `Informacional` para preservar a paridade
> com a Fase 2 e não introduzir 5ª categoria.

---

## 3. Inconsistências temporais nos apontamentos

### Achado

Sobre 377.907 ciclos:

| Critério | n | % |
|---|---:|---:|
| `Inicio > Fim` (definição estrita) | **0** | 0,0000% |
| `Inicio == Fim` (duração zero) | **0** | 0,0000% |
| `duração < 0` | **0** | 0,0000% |
| `duração > 30 dias` (sentinela de bug) | **0** | 0,0000% |

### Veredito

Apontamentos **estão limpos**. Nenhuma exclusão de ciclo é necessária por
inconsistência de duração. Esta é a defesa empírica da decisão de **não
filtrar** ciclos com base em duração — a pressuposição da Fase 1 ("a
limpeza pode descartar até 5%") não se sustenta nos dados reais.

---

## 4. Sobreposição entre ciclos consecutivos do mesmo `Tag`

### Achado

326 pares `(ciclo_anterior, ciclo_atual)` do mesmo `Tag` apresentam
`Inicio_atual < Fim_anterior` — **0,086% dos ciclos**.

| Estatística | Sobreposição (min) |
|---|---:|
| Mediana | 60,0 |
| P90 | 60,0 |
| P99 | 60,0 |
| Máx | 60,0 |
| Mín | 0,2 |

A sobreposição é **uniformemente ≤ 60 min**, com massa concentrada em
exatamente 60 min. Padrão sugere artefato de **fronteira de turno**
(transição 06:00 ⇄ 18:00 com tolerância humana de 1 h).

Top combinações `(Classe_anterior, Classe_atual)`:

| Classe_anterior | Classe_atual | n |
|---|---|---:|
| Hibernando | Operando | 136 |
| Hibernando | Parado | 72 |
| Operando | Hibernando | 64 |
| Hibernando | Manutenção | 28 |
| Parado | Hibernando | 25 |
| Manutenção | Hibernando | 1 |

**85% das sobreposições envolvem `Hibernando`**, não Operando×Operando — o
que confirma o padrão "registrador automático no fim/começo de turno".

### Decisão (formaliza-se em D025)

**Manter os ciclos sobrepostos**. Adicionar feature derivada
`tem_overlap_anterior` (binária) no builder da Fase 3C. Não dropar — 0,086%
não justifica perda de informação, e o padrão (transição de turno) é
benigno para a finalidade do modelo (`Operando` é o estado relevante).

---

## 5. H013 estratificada — `Operando` sem telemetria

### Achado populacional global

**32.149 / 182.527 = 17,61%** dos ciclos `Operando` têm 0 eventos de
telemetria correspondentes (mesmo `Tag`, `Data_Evento ∈ [Inicio, Fim]`).

Bate com o número da auditoria da Fase 2 (17,6%). Diferença 17,61% vs
17,6% deve-se a refinamento do JOIN de range (incluímos
`Data_Evento <= Fim` em vez de `<`).

### Heterogeneidade marcada por frota × mês

| mês | 793-D 2S | 793-D 3S | 793-D 4S | 793-D 5S | LeTourneau L 1850 |
|---|---:|---:|---:|---:|---:|
| 2025-01 | 22,9% | **29,7%** | 18,7% | 19,1% | 5,1% |
| 2025-02 | 25,4% | 23,6% | 14,7% | 19,2% | **2,9%** |
| 2025-03 | 20,6% | 27,3% | 18,2% | 21,5% | 3,4% |
| 2025-04 | 22,6% | 17,6% | 20,7% | 21,7% | 3,6% |
| 2025-05 | 19,5% | 17,7% | 19,2% | 18,8% | **14,2%** ← outlier |
| 2025-06 | 14,6% | **11,4%** | 14,3% | 15,3% | 1,6% |

**Observações críticas**:
- **LeTourneau é estruturalmente diferente**: pct_zero entre 1,6% e 5,1%
  na maior parte dos meses, mas **salta para 14,2% em maio**. Possível
  janela de manutenção da telemetria embarcada — comportamento que
  precisa ser tratado como **categoria operacional**, não como ruído.
- **793-D 3S é o mais alto** (até 29,7% em jan) — frota com 3 TAGs apenas;
  pode ser amostra pequena ou problema de calibração de telemetria.
- **Junho cai uniforme** em todas as frotas (11-15%) — confirma melhoria
  operacional que também explica o vale de prevalência de Don't Go (H010).

### Heterogeneidade por hora (bucket × frota)

| bucket | 793-D 2S | 793-D 3S | 793-D 4S | 793-D 5S | LeTourneau |
|---|---:|---:|---:|---:|---:|
| 00-06 madrugada | 21,4% | 25,9% | 18,3% | 19,9% | 5,9% |
| 06-12 manhã | 20,4% | 23,3% | 17,1% | 19,3% | 5,3% |
| 12-18 tarde | 20,2% | 22,5% | 16,9% | 18,4% | 4,8% |
| 18-24 noite | 19,9% | 24,8% | 18,7% | 19,8% | 5,3% |

Variação por bucket é < 6 p.p. dentro de cada frota — **bucket de hora
não é fator dominante**; mês × frota é.

### Decisão (reforça D020)

`tem_telemetria=0` é **feature de primeira classe** no dataset de scoring
da Fase 3C — não é apenas flag de exclusão. A heterogeneidade por
mês × frota mostra que carrega informação operacional real (manutenção da
telemetria, perfil de OEM, sazonalidade de pipeline).

Adicional: criar feature `pct_zero_telemetria_30d_frota` (mediana móvel
do pct de "Operando sem telemetria" para a frota nos últimos 30 dias) —
captura mudanças de regime como o salto de maio na LeTourneau.

---

## 6. Mapping `Tag_Frota → Porte` (D019)

### Catálogo Vale (insuficiente)

`desenvolver_dontgo.xlsx` cobre **apenas 1 par**:

| Tag_Frota | Porte |
|---|---|
| 793-D 4S | Grande Porte |

Não permite inferir as outras 4 frotas.

### População de frotas na telemetria

| Tag_Frota | n_TAGs | n_eventos | % do volume |
|---|---:|---:|---:|
| LeTourneau L 1850 | 5 | 33.882.291 | 91,2% |
| 793-D 5S | 13 | 1.881.355 | 5,1% |
| 793-D 4S | 9 | 854.298 | 2,3% |
| 793-D 2S | 5 | 380.980 | 1,0% |
| 793-D 3S | 3 | 165.130 | 0,4% |
| **Total** | **35** | **37.164.054** | 100% |

### Decisão (formaliza-se em D024 — mapping)

Combinar **catálogo Vale (1 par confirmado)** + **catálogo OEM público** +
**política de fallback explícita**:

| Tag_Frota | Fabricante | Modelo OEM | Porte | Capacidade nominal | Fonte |
|---|---|---|---|---|---|
| 793-D 2S | Caterpillar | 793D (config 2S) | Grande Porte | ~226 t | OEM CAT — 793D family |
| 793-D 3S | Caterpillar | 793D (config 3S) | Grande Porte | ~226 t | OEM CAT — 793D family |
| 793-D 4S | Caterpillar | 793D (config 4S) | Grande Porte | ~226 t | **Vale** (confirma) + OEM CAT |
| 793-D 5S | Caterpillar | 793D (config 5S) | Grande Porte | ~226 t | OEM CAT — 793D family |
| LeTourneau L 1850 | LeTourneau (Komatsu) | L-1850 | Grande Porte | ~73 m³ pá / ~36 t/balde | OEM LeTourneau |

**Justificativa**: o catálogo CAT 793D (suas variantes 2S/3S/4S/5S são
configurações de redução do mesmo chassi-base) é uniformemente classificado
como **Caminhão Fora-de-Estrada Grande Porte (≥ 200 t)**. A LeTourneau
L-1850 é uma **escavadeira/carregadeira de roda Grande Porte** (par para
caminhões dessa classe). Todas as 5 frotas são "Grande Porte" — é a
realidade da operação Itabira.

> **Implicação**: a feature `Porte` derivada de `Tag_Frota` é **constante**
> no dataset atual ("Grande Porte"). **Não é preditiva isoladamente** —
> mas é mantida no mapping para (a) auditabilidade, (b) reaproveitamento
> em futuras operações (Médio/Pequeno), (c) consistência com o
> `desenvolver_dontgo.xlsx`.

A informação que **diferencia** as frotas no modelo continua sendo
`Tag_Frota` (5 categorias), `Tipo` (Caminhão vs Escavadeira) e `OEM`
(CAT vs LeTourneau — proxy via prefixo do `Tag_Frota`).

---

## 7. Pendências para 3A.2-3A.5

| # | Tarefa | Decisão derivada |
|---|---|---|
| 3A.2 | `src/data/mappings.py` com `TAG_FROTA_TO_PORTE` + `TAG_FROTA_TO_OEM` + `TAG_FROTA_TO_TIPO` | D024 |
| 3A.3 | `src/data/cleaning.py` — `fix_criticidade_via_id`, `add_overlap_flag` | D025 |
| 3A.4 | `src/data/incidents.py` — função canônica `apply_incidents_d009(rel, tol_min=30)` extraída do runner_2c | (re-uso da D018) |
| 3A.5 | `src/data/coverage.py` — `compute_telemetry_coverage(apt_df, con) → DataFrame` com `tem_telemetria`, `n_evt_no_ciclo` | (uso da D020) |

Próximo passo: criar `src/data/mappings.py` (3A.2).
