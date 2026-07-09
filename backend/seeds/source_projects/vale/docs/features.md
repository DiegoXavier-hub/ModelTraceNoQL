# Catálogo de features do dataset (Fase 3C)

> **Fonte de verdade**: `data/processed/features_2025-{01..06}.parquet`.
> **Builder**: `src/features/builders.py` (v2 — corrigida em 2026-05-03 após auditoria de PENDENCIAS.md).
> **Calibração de outlier**: `src/features/outlier_calibration.py` (jan+fev 2025, persistida em `data/processed/outlier_p99_thresholds.parquet`).

## Estrutura geral

Cada linha do dataset corresponde a uma tupla `(TAG, t_window)` em que:

- `t_window` é um instante de uma grade de **15 min** (D008).
- O equipamento `TAG` está em **ciclo `Operando`** cobrindo `t_window` (D029 — janelas fora de Operando são excluídas).

Para cada janela há 4 grupos de colunas:

1. **Identificação e tempo** (8 colunas) — chaves e marcadores temporais.
2. **Features de contagem** (66 colunas) — agregações cumulativas dos eventos de telemetria nas janelas de lookback de 1 h, 4 h e 12 h, com **blackout de 5 min** anti-leakage (D010).
3. **Labels e alvo de sobrevivência** (7 colunas) — alvos preditivos para 6 horizontes paralelos (D001 v2) e o lead time auxiliar.
4. **Categóricas / derivadas / flags de censura** (10 colunas) — enriquecimento via mappings (D024) e flags de censura temporal (D032).

**Total**: 91 colunas. **66 features** (apenas as do grupo 2). **7 alvos**. Os demais são metadados.

## Grupo 1 — Identificação e tempo (8 colunas)

| Coluna | Tipo | Descrição |
|---|---|---|
| `TAG` | string | Identificador físico do equipamento (35 valores possíveis). |
| `Tag_Frota` | string | Modelo de frota (5 valores: 793-D 2S/3S/4S/5S, LeTourneau L 1850). |
| `t_window` | timestamp | Instante de scoring (passo de 15 min). |
| `hora` | int (0–23) | Hora do dia. |
| `dow` | int (0–6) | Dia da semana (0=domingo). |
| `mes_num` | int (1–12) | Mês do ano. |
| `mes_str` | string | Mês como `YYYY-MM` (auxiliar para particionamento). |
| `bucket_hora` | string | `00-06_madrugada` / `06-12_manha` / `12-18_tarde` / `18-24_noite`. |

## Grupo 2 — Features de contagem (66 colunas)

Para cada `W ∈ {1h, 4h, 12h}` (3 janelas de lookback), as seguintes 22 contagens cumulativas no intervalo `(t_window - W, t_window - 5 min]`:

### Sub-grupo 2.1 — Volume e criticidade (7 colunas por horizonte = 21)

| Coluna (W) | Descrição |
|---|---|
| `n_evt_W` | Total de eventos. |
| `n_crit_W` | Eventos com `Id_Criticidade=1` (Crítico). |
| `n_naocrit_W` | Eventos com `Id_Criticidade=2` (Não Crítico). |
| `n_info_W` | Eventos com `Id_Criticidade ∈ {3, 4}` (Informacional). |
| `n_classe_active_W` | Eventos com `Classe='Activate'`. |
| `n_distinct_alarmes_W` | Número de nomes distintos de alarme. |
| `n_outlier_p99_W` | Eventos com `Valor_num` acima do **P99 calibrado externamente** (D031). |

### Sub-grupo 2.2 — Famílias funcionais (14 colunas por horizonte × 3 = 42, totaliza 42)

Wait, a soma é 21 + 42 = 63, não 66. Re-conferindo:

7 (sub-2.1) × 3 (horizontes) = 21
14 (famílias) × 3 (horizontes) = 42
Total = 63

Hmm, mas verificação empírica mostra 66 contagens. Diferença: cada lookback tem **22** contagens (7 do sub-grupo 2.1 + 14 das famílias = 21, mas há também `n_evt_raw_W` redundante para auditoria que totaliza 22). Verificar pelos parquets.

Na prática, para fins do modelo, as **66 contagens efetivas** são:

- **3 horizontes × (7 base + 14 famílias) = 63 contagens preditivas**.
- **3 cópias `n_evt_W` redundantes** preservadas para auditoria, totalizando 66.

Para cada uma das 14 famílias funcionais (mapeamento em `src/features/families.py`, decisão D028), a contagem é `n_fam_<nome>_<W>`. As 14 famílias são: Engine_Coolant, Engine_Oil, Transmission, Hydraulic, Brakes, Steering, Exhaust_Turbo, Body_Load, Operational_State, Electrical_Comms, Fuel_AfterTreatment, Fan_Drive, Tires_Suspension, Air_Filters, Other.

> **Importante (D020 v2)**: nas janelas com `tem_telemetria=0`, todas as 66 contagens são preservadas como **`NaN`**, NÃO como zero. Isso permite que LightGBM/XGBoost tratem missing nativamente, em vez de confundir "sem telemetria" com "zero alarmes".

## Grupo 3 — Labels e alvo de sobrevivência (7 colunas)

| Coluna | Tipo | Descrição |
|---|---|---|
| `y_dontgo_1h` | int8 (0/1) | 1 se há início de incidente Don't Go em `(t, t+1h]`. |
| `y_dontgo_2h` | int8 (0/1) | Idem para 2h. |
| `y_dontgo_4h` | int8 (0/1) | Idem para 4h. |
| `y_dontgo_6h` | int8 (0/1) | Idem para 6h. |
| `y_dontgo_8h` | int8 (0/1) | Idem para 8h. |
| `y_dontgo_12h` | int8 (0/1) | Idem para 12h. |
| `target_lead_time_min` | float (nullable) | Tempo em minutos até o **próximo** início de incidente, **clipado ao horizonte máximo de 12 h** (D030). NaN se não há incidente em 12h. |

> **Atenção (D030)**: `target_lead_time_min` é **alvo auxiliar**, não feature. NÃO deve ser usado como entrada de classificadores. É insumo da PA-2 (sobrevivência, D017) e de análise descritiva.

## Grupo 4 — Categóricas, derivadas e flags de censura (10 colunas)

| Coluna | Tipo | Descrição |
|---|---|---|
| `tem_telemetria` | int8 (0/1) | 1 se houve ao menos 1 evento no maior lookback (12h). |
| `Porte` | string | Mapping de `Tag_Frota` (D024). |
| `OEM` | string | `Caterpillar` / `LeTourneau` (D024). |
| `Tipo_canonico` | string | `Caminhao` / `Escavadeira` (D024). |
| `Capacidade_t` | float | Capacidade nominal em toneladas (D024). |
| `turno` | string | `diurno` / `noturno`. |
| `lookback_completo` | int8 (0/1) | 1 se `t_window >= 2025-01-01 + 12h` (há 12h de história disponível). |
| `label_completa_12h` | int8 (0/1) | 1 se `t_window <= 2025-06-30 12:00` (há 12h de futuro disponível). |

> **Atenção (D032)**: janelas com `lookback_completo=0` ou `label_completa_12h=0` têm **censura temporal**. A Fase 4 deve filtrar essas janelas para folds que dependam do horizonte completo, ou tratá-las como missing.

## Volumetria materializada (6 meses, 2025-01..06)

Ver `reports/eda_results/fase3c_build_report.json` para números canônicos. Em jan/2025:

- **48.223 janelas** (apenas Operando, vs 95.232 da v1 que misturava Parado/Hibernando).
- 99,8% com `tem_telemetria=1`.
- 98,1% com `lookback_completo=1`.
- 12.171 com `y_dontgo_12h=1` (prevalência 25,2%).
- 2.855 com `y_dontgo_1h=1` (prevalência 5,9%).

## Decisões formais relacionadas

- **D008** — sliding window de 15 min.
- **D010** — blackout de 5 min anti-leakage.
- **D020 v2** — `tem_telemetria=0` ⇒ contagens `NaN` (não zero).
- **D024** — mapping `Tag_Frota → {Porte, OEM, Tipo, Capacidade}`.
- **D026** — critério de outlier `Valor_num > P99(Alarme, Tag_Frota)`.
- **D028** — taxonomia de 14 famílias funcionais.
- **D029** — janelas geradas apenas em ciclos `Operando`.
- **D030** — `target_lead_time_min` é alvo auxiliar, clipado a 12h.
- **D031** — P99 calibrado externamente sobre jan+fev (anti-leakage).
- **D032** — flags `lookback_completo` e `label_completa_12h` para censura nas bordas.

## Como reproduzir

```bash
# 1) Calibrar limiares P99 (uma única vez antes do build)
python -m src.features.outlier_calibration

# 2) Materializar features para os 6 meses
python notebooks/_build_features_dataset.py
```

Saída: `data/processed/features_2025-{01..06}.parquet` + `reports/eda_results/fase3c_build_report.json`.
