# Auto-revisão metodológica — Pós-Fase 1

> Data: 2026-04-28 · Revisor: o próprio sistema atuando como revisor externo da banca.
> Objetivo: identificar erros metodológicos, ambiguidades e fragilidades nos artefatos produzidos
> até agora (`business_understanding.md`, `decisions.md`, `hypotheses.md`, `MEMORY.md`),
> **antes** de avançar para a Fase 2.
>
> Escopo da revisão: rigor estatístico, definições operacionais, riscos de data leakage,
> consistência entre documentos e completude da contextualização.

---

## Princípio governante (atualizado em 2026-04-28)

> **Robustez > custo computacional.** O autor explicitamente preferiu sempre a alternativa
> mais robusta, mesmo a um custo computacional maior. Toda decisão metodológica abaixo é
> calibrada para essa preferência.

---

## Tier 1 — Erros / lacunas que **bloqueiam** o avanço para a Fase 2

### T1.1 ❌ Unidade de predição não está definida

**Problema**: o documento diz "probabilidade de Don't Go nas próximas 4 h", mas **não especifica quando o modelo emite uma predição**. Existem ao menos quatro alternativas operacionalmente diferentes:

| Alternativa | Frequência de scoring | Prós | Contras |
|---|---|---|---|
| (a) Por evento de telemetria | a cada uma das 37M linhas | usa toda a granularidade | gera 37M predições; bias de eventos repetidos |
| (b) Por janela fixa (5/15/30 min) | a cada 5 min/equipamento ativo | mimetiza dispatcher real | precisa interpolar features no tempo |
| (c) Por ciclo de apontamento | em cada `Inicio` de ciclo | naturalmente agendado | granularidade fica grossa |
| (d) Por turno | 2× ao dia | muito grossa | não atende cenário operacional |

**Por que importa**: a definição da unidade fixa **as features** (estado no instante de scoring), o **alvo** (qualquer Don't Go em [t, t+4h]?), o **balanceamento de classes** e a **avaliação** (lead time é medido a partir de qual predição?).

**Correção proposta**:
- **Adotar (b) sliding window de 15 min** por equipamento ativo como unidade primária.
- Justificativa: mimetiza o ciclo de atualização de painel (dispatcher), gera dataset gerenciável (≈1.000 equip × 96 janelas/dia × 180 dias = 17M linhas ≈ ordem da telemetria, mas com features agregadas), e é **comparável entre janelas de 1h/2h/4h/6h/8h/12h**.
- Registrar como **D008** em `decisions.md`.

---

### T1.2 ❌ "Evento Don't Go" vs. "Incidente Don't Go" não está definido

**Problema**: a flag `Is_Dont_Go=1` é por **evento** (linha de telemetria). Mas um único incidente físico pode gerar várias linhas em sequência (o equipamento continua disparando enquanto o operador não para). Sem deduplicação, o **Recall e o Lead time são distorcidos**:

- Modelo prediz positivo às 02:00, primeiro `Is_Dont_Go=1` às 02:03, mais 4 `Is_Dont_Go=1` às 02:04–02:08.
- Naive: 5 verdadeiros positivos, lead time = média {3, 4, 5, 6, 7, 8 min}.
- Correto: 1 incidente prevenível, lead time = 3 min (ao primeiro disparo).

**Correção proposta**:
- Definir **"incidente Don't Go"** = sequência maximal de `Is_Dont_Go=1` do mesmo equipamento separada por ≤ 30 min de tolerância. Ao primeiro evento da sequência atribui-se `is_incident_start=1`; os subsequentes ficam `is_incident_start=0`.
- **Avaliação** usa apenas eventos com `is_incident_start=1`. **Treinamento** pode usar a flag por evento (mais sinal positivo) — decidir na Fase 3 com ablation.
- Tolerância de 30 min é palpite; refinar com EDA (distribuição empírica de espaçamento entre Don't Gos do mesmo equipamento).
- Registrar como **D009**.

---

### T1.3 ❌ Risco de data leakage não foi explicitado

**Problema**: a flag `Is_Dont_Go` é a melhor preditora possível dela mesma. Sem proibição explícita, é tentador construir features como "contagem de `Is_Dont_Go` nas últimas 4h" — o que **vaza** o futuro próximo no presente.

Existem **três fontes de leakage** específicas a este projeto:

1. **Auto-leak da label**: usar `Is_Dont_Go` (ou qualquer função sua) como feature.
2. **Leak via `Id_Criticidade`**: a Criticidade=1 (Crítico) é um dos componentes que a regra usa para acender o flag. Usar Criticidade brutamente captura o disparo da regra, não o estado do equipamento.
3. **Leak via padrão sequencial óbvio**: contar "5 alarmes do mesmo nome nos últimos 6 minutos" reproduz literalmente uma das regras do CMA. O modelo "prediz" a regra, não a falha.

**Correção proposta**:
- **Regra de ouro**: `Is_Dont_Go` **só** é usado como `y` (label). Nunca como feature, nunca em agregação histórica.
- **Suite de features auditadas**: documentar em `docs/features.md` quais features podem ser construídas e quais estão proibidas. Toda agregação de eventos deve **excluir** a janela [t−Δblackout, t] onde Δblackout é definido (sugestão: 5 min) para impedir que features como "alarmes recentes" coincidam com a janela exata da regra.
- **Análise estratificada por lead time**: reportar performance separadamente em buckets de lead time (0–15 min, 15–60 min, 1–4 h). Modelo que só prevê 0–15 min antes está "predizendo a regra"; modelo com sinal forte em 1–4 h está predizendo **risco real**.
- Registrar como **D010**.

---

### T1.4 ❌ Estratégia temporal de split não comprometida concretamente

**Problema**: "TimeSeriesSplit / walk-forward" é genérico demais. Cada implementação tem armadilhas:

- **Single hold-out** (ex: jan-mai treino, jun teste) é fácil, mas só dá **uma medida** — vulnerável a particularidades do mês de teste.
- **Walk-forward expanding** mostra estabilidade ao longo do tempo, mas multiplica custo de treino.
- **Sliding-window walk-forward** captura concept drift, mas o tamanho da janela é hiperparâmetro.

**Correção proposta** (alinhada com "robustez > custo"):
- **Estratégia primária**: walk-forward expanding com 4 folds:
  - Fold 1: treino jan, val fev, teste mar
  - Fold 2: treino jan-fev, val mar, teste abr
  - Fold 3: treino jan-mar, val abr, teste mai
  - Fold 4: treino jan-abr, val mai, teste jun
- **Resultado primário**: média ± desvio das 4 métricas de teste — reportado com IC bootstrap por fold.
- **Modelo final** ("para deploy"): treinado em jan-mai, avaliado uma única vez em jun ("teste final intocado").
- **Buffer de gap entre treino e val/teste**: ≥ 4 horas (= janela máxima de predição) para impedir leakage por features que olham 4h pra frente.
- Registrar como **D011**.

---

### T1.5 ❌ "Predizer Don't Go" pode ser confundido com "predizer o trigger da regra"

**Problema** (filosófico mas relevante): se a regra é "5 alarmes em 6 min", basta detectar "estamos no 4" para "predizer" o Don't Go com 100% de antecedência. Isso **não é predição de risco** — é **antecipação determinística** da regra que o próprio sistema vai disparar em segundos. Banca pode (com razão) questionar: "o modelo prevê falha, ou prevê o algoritmo de detecção da falha?"

**Correção proposta**:
- Adicionar à seção 3.1 do `business_understanding.md` um **disclaimer honesto** distinguindo "predição da regra" vs "predição do risco subjacente".
- A análise por **lead time bucket** (T1.3) é **a evidência primária** dessa distinção: se o modelo só funciona no bucket 0–15 min, está prevendo a regra; se mantém sinal em 1–4 h, está prevendo risco.
- Adicionar à seção de Limitações (3.6).

---

## Tier 2 — Decisões a fechar antes da Fase 4 (Modelagem)

### T2.1 ⚠️ AUC-PR depende da prevalência — comparações precisam de normalização

**Problema**: AUC-PR baseline (modelo aleatório) ≈ prevalência. Modelo com AUC-PR=0,3 e prevalência 0,001 é **300× melhor que aleatório**; outro com AUC-PR=0,3 e prevalência 0,1 é apenas 3× melhor. Reportar só AUC-PR sem prevalência **engana**.

**Correção**: reportar simultaneamente:
- AUC-PR (absoluta)
- **Lift** = AUC-PR / prevalência
- AUC-ROC (padrão de comparação, mesmo não sendo primária)
- **Brier Score** (para calibração)
- **Expected Calibration Error (ECE)**

Registrar como **D012**.

### T2.2 ⚠️ Definição operacional do "lead time" e regra de pareamento

**Problema**: lead time precisa de definição **inambígua** sobre qual predição "conta" para um dado incidente.

**Correção** (definição formal):

> Para cada incidente `I` ocorrido no instante `t_I` (= `Data_Evento` do primeiro `Is_Dont_Go=1` da sequência),
> seja `P(I) = {p_1, p_2, ...}` o conjunto de predições positivas (score ≥ limiar) emitidas pelo
> modelo no equipamento de `I` durante a janela `[t_I − 4h, t_I]`.
>
> - Se `P(I) = ∅`: incidente é **FN** (recall conta como 0).
> - Senão: incidente é **TP** com **lead_time(I) = t_I − min(P(I))** (em minutos).
>
> Falsos positivos: predições positivas em janelas que não contêm um incidente nas próximas 4 h.

Registrar como **D013**.

### T2.3 ⚠️ Calibração — método não especificado

**Correção**: usar **Platt scaling** (sigmoid) e **Isotonic Regression**, comparar via Brier e ECE no fold de validação, reportar o melhor. Para LightGBM/XGBoost com classes raras e muitos dados, **Isotonic geralmente vence**. Registrar **D014**.

### T2.4 ⚠️ Estratégia para classe rara — proibições e permissões

**Correção**:
- ✅ Permitido: `scale_pos_weight` (LGBM/XGB), `class_weight='balanced'` (sklearn), focal loss em redes neurais.
- ⚠️ Cuidado: undersampling do majoritário até 1:10 ou 1:50 — testar mas **avaliar sempre na distribuição real**.
- ❌ **Proibido**: SMOTE / sintéticos sobre features temporais — viola estrutura sequencial e gera "amostras impossíveis".
- ❌ Proibido: oversample do minoritário **dentro de cada fold sem time-aware** — vaza informação entre janelas.

Registrar **D015**.

### T2.5 ⚠️ Operador: estratégia de join Apontamentos × Telemetria

**Problema**: parquet de apontamentos não tem `Nome_Operador_Anon`, mas telemetria tem. Para testar H005, precisamos juntar.

**Correção**:
- Para cada ciclo de apontamento `(Tag, Inicio, Fim)`, **operador atribuído** = moda (mais frequente) de `Nome_Operador_Anon` em telemetria com `TAG=Tag` e `Data_Evento ∈ [Inicio, Fim]`.
- Validação: % de ciclos com operador único na janela vs múltiplos.
- Se moda < 80% dos eventos: marcar `operador_inferido=False`. Senão `True`. Reportar fração.

Registrar **D016**.

### T2.6 ⚠️ Survival censoring e definição de "tempo até evento"

**Correção** (para PA-2):
- Para cada equipamento `e` no fold de teste, definir uma **série de instantes de scoring** `s_1, s_2, ...` (ex: cada hora).
- Para cada `s_k`: tempo observado `T_k = min(t_próximo_incidente − s_k, fim_período − s_k)`; censura `δ_k = 1 [t_próximo_incidente − s_k ≤ fim_período − s_k]`.
- Modelos: Cox PH (com teste de proporcional hazards via Schoenfeld) e Weibull AFT como alternativa robusta caso PH falhe.

Registrar **D017**.

---

## Tier 3 — Ajustes finos (notar agora, executar depois)

### T3.1 ⚠️ Erro factual no business_understanding.md §2.5

**Onde**: seção "Padrão sequencial precursor — evidência empírica", afirmação:
> "**5 disparos do mesmo alarme `Engine Coolant Level - Active`** nos 3 minutos imediatamente antes do Don't Go final"

**Verificar**: a inspeção mostrou apenas as últimas 6 linhas (141–146). O alarme `Engine Coolant Level - Active` aparece nas linhas 142, 144 e 146 (Active) — só **3 disparos do mesmo alarme** nos 3 min finais (não 5).

**Correção**: re-rodar o conteúdo do exemplo e reescrever com números exatos. Adicionar como subitem do CM 1.1 do .tex apenas após verificação.

### T3.2 ⚠️ "Apenas Itabira" como afirmação

**Onde**: §1, §2.1 e §3.6 do `business_understanding.md`. **Problema**: vimos `Localidade='Itabira'` apenas na amostra inicial dos parquets. Não auditamos os 6 meses inteiros.

**Correção**: substituir "**Apenas Itabira**" por "**A amostra inicial sugere Itabira; a Fase 2 confirmará** se há outras localidades". A Fase 2 deve verificar formalmente — se houver outras, reabrir D005.

### T3.3 ⚠️ Custos hipotéticos sem fundamentação

**Onde**: §3.3.4 do `business_understanding.md`, parâmetros `ΔP` e `0,3·ΔP`.

**Correção**: substituir por **análise de sensibilidade** parametrizada — calcular horas de parada evitadas para `ΔP ∈ {30, 60, 120, 240} min` e `redução ∈ {50%, 70%, 90%}`. O relatório apresenta uma **superfície** ao invés de um número (mais honesto e mais robusto).

### T3.4 ⚠️ Sheets `Tendências` e `Eventos O&M` não foram exploradas

**Onde**: `Alarmes - Regra de Negocio.xlsx` tem 3 sheets, só usamos `CMA` (151 regras).
- `Tendências` (371 linhas): nomes e descrições de tendências OEM.
- `Eventos O&M` (147.943 linhas): universo de eventos possíveis dos equipamentos.

**Correção** (Fase 2): cruzar `Eventos O&M.Name` com `telemetry.Alarme.unique()` para entender cobertura — quantos alarmes da telemetria têm descrição catalogada vs órfãos. Pode virar feature de "alarme conhecido vs desconhecido".

### T3.5 ⚠️ Diagrama Figura 1 ainda em ASCII

**Correção**: gerar versão definitiva em **TikZ** (cabe direto no `.tex`) ou imagem vetorial (`graphviz` → SVG → incluir). Adicionar à fase de redação do `.tex`.

### T3.6 ⚠️ Pareamento Apontamento × Telemetria — não auditado

**Correção** (Fase 2 obrigatória): para uma amostra de ciclos de apontamento, contar quantos eventos de telemetria caem dentro do intervalo `[Inicio, Fim]` (deve ser >0 para `Operando`); auditar `Tag` consistente.

### T3.7 ⚠️ Coluna `Porte` no exemplo Don't Go — origem desconhecida

**Onde**: o exemplo `desenvolver_dontgo.xlsx` tem 19 colunas, com `Porte` ("Grande Porte") que **não existe no parquet bruto**.

**Correção**: na Fase 2, descobrir se `Porte` é (a) derivada de `Tag_Frota` por um mapeamento, (b) feature externa, (c) erro de exportação. Adicionar como feature derivada se for o caso (a).

### T3.8 ⚠️ Reprodutibilidade — seeds não fixados

**Correção**: criar `src/utils/seeds.py` com `SEED=42` aplicado a `numpy`, `random`, `torch`, `lightgbm`, `xgboost`. Documentar.

### T3.9 ⚠️ AUC-ROC continua sendo importante para comparação

**Correção**: mesmo não sendo a métrica primária, **reportar AUC-ROC** em todas as tabelas para permitir comparação com a literatura (que historicamente usa ROC).

### T3.10 ⚠️ H006 (localidade) é provavelmente vazia

**Correção**: marcar H006 como **inconclusiva por construção** se a Fase 2 confirmar localidade única; movê-la para "Trabalhos Futuros" sem testar.

---

## Síntese — o que muda concretamente antes da Fase 2

### Novas decisões a registrar (D008–D017)

| # | Decisão | Origem |
|---|---|---|
| **D008** | Unidade de predição: sliding window 15 min por equipamento ativo | T1.1 |
| **D009** | Definição de "incidente Don't Go" = sequência maximal com gap ≤ 30 min | T1.2 |
| **D010** | Regras de feature engineering: anti-leakage (proibições explícitas + análise por lead time bucket) | T1.3 |
| **D011** | Walk-forward expanding 4 folds (jan→fev→mar→abr→mai→jun) + teste final intocado em jun | T1.4 |
| **D012** | Métricas reportadas: AUC-PR + Lift + AUC-ROC + Brier + ECE + Recall@P=0,5 + Lead time | T2.1 |
| **D013** | Definição formal de TP/FN/FP e lead time por incidente | T2.2 |
| **D014** | Calibração: Platt + Isotonic, escolher por Brier/ECE no fold de validação | T2.3 |
| **D015** | Class imbalance: pesos sim, SMOTE não, undersampling com cuidado e avaliação na distribuição real | T2.4 |
| **D016** | Operador inferido por moda em telemetria dentro do intervalo de cada ciclo | T2.5 |
| **D017** | Sobrevivência: scoring horário + Cox PH com teste de Schoenfeld + Weibull AFT como alternativa | T2.6 |

### Decisão atualizada

| # | Antes | Depois | Motivo |
|---|---|---|---|
| **D001** | Janela única 4 h | **Múltiplas janelas em paralelo** (1h, 2h, 4h, 6h, 8h, 12h) | Decisão do usuário em 2026-04-28: "robustez > custo computacional" |

### Correções editoriais nos artefatos existentes

- `business_understanding.md` §1, §2.1, §3.6: substituir "apenas Itabira" por "amostra inicial sugere Itabira; confirmar na Fase 2".
- `business_understanding.md` §2.5: corrigir "5 disparos" → "verificar com inspeção exata; provavelmente 3 disparos do mesmo alarme nos 3 min finais".
- `business_understanding.md` §3.1: adicionar disclaimer "predição da regra vs predição do risco" (T1.5).
- `business_understanding.md` §3.3.4: substituir parâmetros fixos por análise de sensibilidade.
- `business_understanding.md` §3.6: adicionar "limitação 5 — predição do trigger vs do risco subjacente".
- `hypotheses.md` H006: marcar como **inconclusiva por construção** se Itabira for único.

---

## Veredito (atualizado em 2026-04-29)

**A Fase 1 está FECHADA EM v2.** Todas as 5 lacunas Tier 1 e as 6 lacunas Tier 2 foram resolvidas via decisões D008–D017 (ver `docs/decisions.md`); a D001 foi atualizada para múltiplas janelas paralelas. As correções editoriais Tier 3 foram aplicadas no `business_understanding.md`. As 4 inconsistências documentais subsequentes apontadas em `PENDENCIAS_FASE1.md` (status de PDFs, números do exemplo Don't Go, métricas do CNN-LSTM, chaves BibTeX) também já foram corrigidas.

### Status das lacunas

| Lacuna | Status | Resolução |
|---|---|---|
| T1.1 Unidade de predição não definida | ✅ RESOLVIDA | D008: sliding window 15 min |
| T1.2 Evento vs incidente | ✅ RESOLVIDA | D009: gap ≤ 30 min, primeira ocorrência |
| T1.3 Risco de leakage | ✅ RESOLVIDA | D010: blackout 5 min + análise por bucket |
| T1.4 Estratégia de split | ✅ RESOLVIDA | D011: walk-forward 4 folds + intocado |
| T1.5 "Predizer regra vs risco" | ✅ RESOLVIDA | Disclaimer §3.1.1 + 6 horizontes paralelos (D001 v2) |
| T2.1 AUC-PR depende de prevalência | ✅ RESOLVIDA | D012: pacote completo de 7 métricas |
| T2.2 Definição de TP/FN/FP/Lead time | ✅ RESOLVIDA | D013: definição formal |
| T2.3 Calibração não especificada | ✅ RESOLVIDA | D014: Platt + Isotonic comparados |
| T2.4 Class imbalance | ✅ RESOLVIDA | D015: pesos sim, SMOTE não |
| T2.5 Operador no apontamento | ✅ RESOLVIDA | D016: inferência por moda na telemetria |
| T2.6 Survival censoring | ✅ RESOLVIDA | D017: Cox PH + Schoenfeld + Weibull AFT |
| T3.1 Erro factual "5 disparos em 3 min" | ✅ CORRIGIDA | Re-verificado: 2 disparos em 3 min, 5 em 6 min |
| T3.2 "Apenas Itabira" | ✅ SUAVIZADO | "amostra inicial sugere Itabira" |
| T3.3 Custos hipotéticos | ✅ RESOLVIDA | Superfície de sensibilidade `(ΔP, ρ)` |
| T3.10 H006 localidade | ✅ MARCADA | Inconclusiva por construção (se Itabira único) |

**Luz verde definitiva** para Fase 2A. Não há mais lacunas Tier 1 ou Tier 2 abertas.
