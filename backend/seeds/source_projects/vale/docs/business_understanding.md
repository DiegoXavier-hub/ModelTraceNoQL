# Fase 1 — Business Understanding

> **Documento canônico** que cobre os Conteúdos Mínimos **CM 1.1** e **CM 1.2** do Estudo Guiado.
> Este texto é a base para o **Capítulo 1 — Introdução** (Motivação + Objetivos) e parte do **Capítulo 2 — Referencial Teórico** (Contextualização do domínio) do TCC ABNT.
>
> **Status**: **v2 — fechado em 2026-04-28** após auto-revisão metodológica (`docs/methodology_review.md`).
> Aplica decisões D001 (atualizada) e D008–D017 do `docs/decisions.md`.
> Sujeito apenas a ajustes pontuais após a EDA da Fase 2 — o conteúdo está pronto para virar Capítulo 1 + parte do Capítulo 2 do `.tex`.

---

## 1. Sumário executivo

A operação de mineração à céu aberto da Vale (e de qualquer grande mineradora) opera **24/7** com uma frota de equipamentos de alto custo de aquisição e de oportunidade — caminhões fora-de-estrada, escavadeiras, carregadeiras e auxiliares. Cada **hora de parada não planejada** representa perda direta de produção e, em casos extremos, risco à integridade do ativo e à segurança do operador. Para mitigar isso, os fabricantes (CAT, Komatsu, LeTourneau) embarcam sistemas de telemetria que emitem **alarmes operacionais em tempo real**. Quando um conjunto específico desses alarmes ocorre — codificado em um catálogo proprietário de **151 regras de negócio (CMA)** —, o sistema dispara um alerta **"Don't Go"**, sinalizando que o equipamento **não deve continuar operando** até inspeção/manutenção.

O presente trabalho busca **antecipar** esse alerta. Em vez de reagir ao Don't Go quando ele acontece, treinamos modelos preditivos que estimam, a partir do histórico recente de telemetria e do padrão de operação, **a probabilidade de um equipamento disparar um Don't Go nas próximas horas**. O objetivo é converter **reação em prevenção**: trocar paradas emergenciais por intervenções programadas, reduzindo horas perdidas, custos de reparo e risco operacional.

---

## 2. CM 1.1 — Contextualização da operação de mina

### 2.1 Operação a céu aberto: visão de alto nível

A mineração de minério de ferro em larga escala — exemplificada pelas operações de Itabira/MG, dominantes na amostra inicial dos dados — segue um **ciclo produtivo** repetido continuamente:

1. **Desmonte** da rocha (perfuração + detonação)
2. **Carregamento** do material por escavadeiras/carregadeiras em caminhões fora-de-estrada
3. **Transporte** do caminhão da frente de lavra à britagem ou ao depósito de estéril
4. **Basculamento** (descarga) e retorno
5. Repetição

Cada um desses passos é **registrado** por dois subsistemas independentes mas interligados:

- **Apontamentos**: cada ciclo de atividade do equipamento (operando, parado, em manutenção) é registrado com `Inicio`, `Fim`, `Tag` (identificador físico do equipamento), `Frota` (modelo, ex: `793-D 5S`), `Tipo` (`Caminhao`, `Carregadeira`, etc.) e `Classe` da atividade (`Operando`, `Parado`, etc.). Equivale ao "diário de operação".
- **Telemetria**: stream de eventos emitidos pelo próprio equipamento — alarmes, leituras de sensores, mudanças de estado. Cada evento traz `Data_Evento` (timestamp em microssegundos), `Alarme` (texto do alarme), `Id_Criticidade` (1=Crítico, 2=Não Crítico, 3=Informacional, 4=Outros), `Valor` (numérico, quando aplicável), `Classe` (`Activate`/`Inactive`/`NULL`) e — fundamental para este projeto — `Is_Dont_Go` (0/1 indicando se o evento dispara um alerta Don't Go).

> **Volume**: 377.907 ciclos de apontamento e **37.164.054 eventos de telemetria** entre 2025-01-01 e 2025-06-30 (6 meses). A amostra inicial sugere **Itabira/MG** como única localidade — confirmação formal a cargo da Fase 2.

### 2.2 O que é um alerta "Don't Go" e por que ele importa

Um alerta **"Don't Go"** é a sinalização operacional mais grave do sistema de monitoramento embarcado. Diferente de alarmes informacionais (ruído rotineiro) ou alarmes apenas críticos (severos mas que não interrompem operação), o Don't Go é uma **diretiva ao operador**: o equipamento **não deve continuar operando** porque uma combinação de condições foi identificada como representando risco iminente de:

- **Falha catastrófica** de um componente de alto custo (motor, transmissão, sistema hidráulico)
- **Risco à segurança** do operador ou de terceiros (superaquecimento, falha de freio, vazamento)
- **Perda de integridade** do ativo (degradação acelerada que multiplica o custo de reparo se ignorada)

Operacionalmente, ao receber um Don't Go o **dispatcher** (controle central) tem três caminhos:

- Continuar operação sob risco (raramente — apenas com aval explícito do supervisor)
- Conduzir o equipamento à oficina para inspeção
- Parar imediatamente no local e aguardar guincho/equipe técnica

**Impacto de cada cenário**:

| Cenário | Custo aproximado |
|---|---|
| Parada programada para inspeção (modelo antecipa em horas) | baixo — janela na agenda existente |
| Parada não programada para inspeção (Don't Go reativo) | médio — interrompe ciclo, pode esperar reboque |
| Falha catastrófica (Don't Go ignorado ou não detectado) | alto — reparo de capital + horas perdidas + risco de segurança |

A diferença entre o primeiro e o terceiro cenário pode ser de **uma ordem de grandeza** em custo. Antecipar o Don't Go é, portanto, exatamente onde **inteligência preditiva tem o maior leverage**.

### 2.3 Catálogo de regras de negócio: o "código" do Don't Go

O arquivo `Alarmes - Regra de Negocio.xlsx` é o **catálogo oficial** que define, em forma tabular, quais combinações de eventos disparam um Don't Go. Estrutura:

- **151 regras** ativas no catálogo CMA
- Distribuição por **TIPO de fonte da regra**:
  - `ALARME OEM` — 142 regras (94%) — alarmes de fábrica do equipamento (CAT, Komatsu, LeTourneau)
  - `TENDÊNCIA` — 7 regras (5%) — tendências internas customizadas
  - `SISTEMA` — 2 regras (1%) — alarmes do sistema interno
- Distribuição por **NIVEL de severidade da regra**:
  - `Muito Alto` — 82 regras (54%) — criticidade máxima
  - `Alto` — 69 regras (46%)

Cada regra é a tupla `(TIPO, EVENTO, SITUACAO, QTD, TEMPO, NIVEL)`:

- **EVENTO**: nome textual do evento OEM (ex: `Engine Coolant Level - Active`, `Low Transmission Oil Level`, `High Engine Coolant Temperature`).
- **SITUACAO**: condição de disparo. **81 das 151 regras (54%)** disparam "**Em qualquer situação**" (instantâneas); o restante exige contagem de pré-eventos consecutivos:
  - "Mediante alarme nível 3" (16×)
  - "Após cinco alarmes consecutivos" (11×)
  - "Mediante cinco alarmes nível 2 consecutivos" (6×)
  - etc.
- **QTD**: quantidade mínima de pré-eventos (mediana 1, máximo 10).
- **TEMPO**: janela em segundos para acumular os QTD eventos (0 = instantâneo, 360 s = 6 min, 720 s = 12 min). Mediana 0; máximo 720 s.
- **NIVEL**: severidade do Don't Go resultante.

### 2.4 Exemplos representativos de regras "Muito Alto"

Os eventos de criticidade máxima cobrem majoritariamente **superaquecimento, baixo nível de fluidos vitais e falhas de transmissão**:

| Categoria operacional | Eventos representativos | # regras |
|---|---|---|
| **Sistema de arrefecimento (motor)** | `Engine Coolant Level - Active`, `Low Engine Coolant Level`, `High Engine Coolant Temperature`, `Coolant Level - Valid But Low - Most Severe` | ≈ 15 |
| **Lubrificação do motor** | `Engine Oil Level - Active`, `Oil Level Low Mark`, `Oil Level Add Mark`, `High Engine Oil Temperature` | ≈ 10 |
| **Transmissão** | `Low Transmission Oil Level`, `Transmission Oil Level - Active` | ≈ 5 |
| **Hidráulico** | `Very Low Hydraulic Oil Level`, `Hydraulic Oil Temperature` | ≈ 5 |
| **Turbinas e exaustão** | `High Right/Left Turbo Turbine Inlet Temperature`, `Right/Left Exhaust Temperature - Active` | ≈ 8 |
| **Sistemas auxiliares** | `Aftercooler Level - Active` e correlatos | ≈ 5 |

Em quase todos esses casos, a operação continuada do equipamento sob a condição é o **mecanismo direto** de uma falha catastrófica: superaquecer um motor por mais 30 min pode literalmente fundi-lo.

### 2.5 Padrão sequencial precursor — evidência empírica

O arquivo `desenvolver_dontgo.xlsx` traz **uma janela completa de 1h58min** de telemetria de um único caminhão (`CA65924`, `793-D 4S`, Grande Porte, Itabira) que culmina em um Don't Go. **Estatísticas exatas dessa janela** (verificadas no dado bruto, 2026-04-28):

- **147 eventos** no total
- **1 evento** com `Is_Dont_Go=1` — o último, em `2025-01-01 02:03:02.140` (`Engine Coolant Level - Active`, `Id_Criticidade=1`)
- **10 eventos** com `Id_Criticidade=1 (Crítico)` no período inteiro — e **todos os 10 são do mesmo alarme** `Engine Coolant Level - Active`
- **Acumulação monotônica em janelas crescentes** ANTES do Don't Go (sem incluir o próprio):

| Janela | Eventos totais | `Engine Coolant Level - Active` | `Id_Criticidade=1` |
|---|---:|---:|---:|
| 3 min antes | 4 | 2 | 2 |
| 6 min antes | 10 | 5 | 5 |
| 12 min antes | 24 | 7 | 7 |
| 30 min antes | 40 | 7 | 7 |
| 60 min antes | 83 | 9 | 9 |

Ou seja: o evento Don't Go **não é "o pior alarme isolado"** — é o ponto em que a **acumulação de pré-condições** cruza um limiar definido pela regra. O sinal precursor é **pelo menos parcialmente capturado em janelas longas** (1h antes, 9 dos 10 críticos já tinham ocorrido), o que sustenta a viabilidade de antecipação por horas — não apenas por minutos. Modelar este comportamento exige features que capturem **histórico recente sequencial**, não apenas o estado instantâneo.

### 2.6 Diagrama do fluxo operacional (CM 1.1 — Figura 1)

```text
                  ┌──────────────────────┐
                  │   Frente de lavra    │
                  │  (escav./caminhão)   │
                  └──────────┬───────────┘
                             │
                             │ ciclos contínuos
                             ▼
            ┌──────────────────────────────────┐
            │ Sistema de Apontamentos          │
            │ (Inicio, Fim, Tag, Frota, Tipo,  │
            │  Classe da atividade)            │
            │ → 377.907 ciclos / 6 meses       │
            └──────────────┬───────────────────┘
                           │
            ┌──────────────┴────────────────┐
            │                               │
            ▼                               ▼
 ┌─────────────────────┐        ┌─────────────────────────────┐
 │ Telemetria embarcada│        │ Catálogo de Regras (CMA)    │
 │ (alarmes OEM, tend.,│        │ 151 regras Don't Go         │
 │  estados, valores)  │        │ TIPO+EVENTO+SITUACAO+NIVEL  │
 │ → 37.164.054 eventos│        │ + QTD + TEMPO               │
 └──────────┬──────────┘        └──────────────┬──────────────┘
            │                                  │
            └────────────┬─────────────────────┘
                         │  rotulação automatizada
                         ▼
            ┌────────────────────────────────┐
            │ Flag Is_Dont_Go (já presente   │
            │ no parquet de telemetria)      │
            │ → ground truth do problema     │
            └────────────────┬───────────────┘
                             │
                             ▼
            ┌────────────────────────────────┐
            │ MODELO PREDITIVO (este TCC)    │
            │ horizonte de antecipação:      │
            │ próximas N horas               │
            └────────────────┬───────────────┘
                             │
                             ▼
            ┌────────────────────────────────┐
            │ Dispatcher / Manutenção        │
            │ → priorização de inspeção      │
            │ → parada programada            │
            │ → redução de horas perdidas    │
            └────────────────────────────────┘
```

> No relatório `.tex`, este diagrama será refeito como uma figura formal (TikZ ou imagem), referenciada como **Figura 1**.

---

## 3. CM 1.2 — Definição do problema analítico

### 3.1 Pergunta analítica principal (definitiva)

> **PA-1**: Dado o estado operacional e o histórico recente de eventos de telemetria de um equipamento de mineração, **qual é a probabilidade de o equipamento disparar um alerta Don't Go em cada um dos horizontes futuros H ∈ {1 h, 2 h, 4 h, 6 h, 8 h, 12 h}**?

**Unidade de predição** (D008): o modelo emite uma predição a cada **janela deslizante de 15 min** por equipamento ativo — frequência alinhada ao ciclo de atualização do painel do dispatcher.

**Estratégia de múltiplas janelas (D001 — atualizada em 2026-04-28)**: em vez de comprometer-se com uma única janela, treinamos e avaliamos **seis modelos paralelos** — um para cada horizonte H ∈ {1, 2, 4, 6, 8, 12} h. Isso permite responder simultaneamente:

- **Curva risco-vs-horizonte**: como o sinal preditivo decai (ou não) à medida que afastamos a predição do evento.
- **Ponto operacional ótimo**: qual H equilibra recall técnico × tempo útil de ação na operação.
- **Robustez do modelo**: se o desempenho cai catastroficamente em H ≥ 4 h, o modelo está apenas detectando o trigger da regra (ver disclaimer abaixo); se mantém AUC-PR razoável em H = 6–12 h, está capturando risco subjacente real.

**Justificativa**:

1. **Formulação binária com janela fixa** é a abordagem operacionalmente mais útil — o dispatcher precisa de uma **decisão acionável**, não de um número abstrato de "tempo até falha".
2. **Múltiplas janelas em paralelo** é mais robusto do que comprometer-se a uma janela única antes da EDA: a melhor janela é descoberta pelos dados, não imposta a priori.
3. **Probabilidade calibrada** (não apenas classe) permite **ranking de risco da frota** em tempo real — o dispatcher consegue priorizar inspeção pelos N equipamentos com maior score, mesmo quando o limiar binário não é atingido.

#### 3.1.1 Disclaimer crítico — "predizer a regra" vs "predizer o risco"

A flag `Is_Dont_Go` é gerada por um motor de regras determinístico aplicado à própria telemetria. Logo, um modelo trivial que detecta "estou no quarto alarme de uma regra que dispara aos cinco" pode atingir excelentes métricas em janelas curtas (≤ 15 min) sem realmente predizer **risco físico** — está apenas antecipando o **disparo algorítmico** de uma regra cujos componentes ele já observa.

Para distinguir os dois fenômenos, este trabalho adota duas defesas explícitas:

1. **Anti-leakage rigoroso na construção de features** (D010): nenhuma feature pode usar `Is_Dont_Go` (auto-leak) nem agregações que reproduzam literalmente uma regra do CMA. Toda agregação de eventos exclui um **blackout de 5 min** imediatamente anterior ao instante de scoring, impedindo o "vislumbre" da janela exata da regra.
2. **Análise estratificada por lead time bucket**: as métricas finais são reportadas separadamente em **três faixas** — (i) lead time 0–15 min, (ii) 15–60 min, (iii) 1–4 h. Sinal forte exclusivamente em (i) sugere predição da regra; sinal preservado em (iii) é evidência empírica de predição de risco subjacente.

### 3.2 Perguntas analíticas secundárias (suporte e diferenciação)

Para tornar o trabalho mais profundo do que "mais um classificador", duas perguntas complementares orientam abordagens secundárias:

> **PA-2 (sobrevivência / regressão)**: Qual é o **tempo esperado até o próximo Don't Go** de um equipamento, condicional ao seu estado atual? Permite prever **intervalos de confiança** ("95% de chance de estar entre 1,5 h e 6 h"), informação mais rica do que um simples "vai ou não vai nas próximas 4h".
>
> **PA-3 (não supervisionado / anomalia)**: Quais **perfis de equipamento e sequências de eventos** são atípicos em relação ao comportamento normal da frota? Permite detectar pré-condições **não cobertas pelas 151 regras CMA** — e portanto antecipar **modos de falha que o catálogo não conhece ainda**.

A combinação das três responde à pergunta operacional na sua forma mais completa: **vai falhar?** (PA-1), **quando?** (PA-2), **e o que está fora do padrão?** (PA-3).

### 3.3 Métricas de sucesso

> **Pacote completo de métricas (D012)**: a rigor estatística e a comparabilidade com a literatura exigem mais do que uma única métrica. Cada modelo treinado é avaliado pelo **conjunto** abaixo, reportado em todas as tabelas finais.

#### 3.3.1 Métricas primárias técnicas

| Métrica | Por que reportar |
|---|---|
| **AUC-PR** | Métrica primária. Mais informativa que ROC sob desbalanceamento extremo (Saito & Rehmsmeier, 2015). |
| **Lift = AUC-PR / prevalência** | AUC-PR isolada engana — varia com prevalência. Lift normaliza e permite comparação entre folds e janelas. |
| **AUC-ROC** | Padrão histórico da literatura; reportado para comparabilidade externa, mesmo não sendo primário. |
| **Brier Score** | Mede calibração (quão bem as probabilidades batem com frequências empíricas). |
| **Expected Calibration Error (ECE)** | Complemento do Brier: erro médio de calibração em bins de probabilidade. |

#### 3.3.2 Métrica primária operacional

> **Recall@Precision=0,5**: dado um limiar de operação que mantém pelo menos 50% de precisão (i.e., metade dos alertas do modelo viram inspeção real bem-aproveitada), **qual fração dos incidentes Don't Go reais o modelo capturou?**

**Justificativa**: Recall puro favorece "alarmar tudo"; Precision puro favorece "alarmar nada". O ponto **P=0,5** é um compromisso explícito que diz à manutenção: "para cada 2 alertas que mando, 1 é verdadeiro" — taxa aceitável para inspeção preventiva sem sobrecarregar a equipe.

#### 3.3.3 Métrica secundária (negócio): Lead time

**Definição formal (D013)**: dado um incidente Don't Go (D009 — primeiro evento `Is_Dont_Go=1` de uma sequência maximal com gap ≤ 30 min) ocorrido no instante `t_I` em um equipamento `e`:

- Seja `P(I)` o conjunto de predições positivas (score ≥ limiar operacional) emitidas pelo modelo no equipamento `e` durante a janela `[t_I − H, t_I]`, onde `H` é o horizonte de predição treinado (1, 2, 4, 6, 8 ou 12 h).
- Se `P(I) = ∅`: incidente é **Falso Negativo (FN)**.
- Caso contrário: incidente é **Verdadeiro Positivo (TP)** e `lead_time(I) = t_I − min(P(I))` (em minutos).
- Falsos Positivos (FP): predições positivas em janelas `[t_pred, t_pred + H]` que **não contêm** um incidente.

Reportamos: **lead time mediano (P50) e P25/P75** entre TPs, separadamente por bucket (0–15 min, 15–60 min, 1–4 h).

#### 3.3.4 Tradução em valor de negócio — análise de sensibilidade

A entrega final do Capítulo 5 (Discussão) traduzirá as métricas técnicas em afirmações concretas:

- **"Com Recall@P=0,5 = X% e lead time mediano P50 = Y min no horizonte H = h, o modelo teria antecipado N incidentes críticos no período de teste, representando uma janela acumulada de Z horas de ação preventiva."**

Como o **custo financeiro real** de cada modo operacional não está nos dados, optou-se por uma **superfície de sensibilidade** (T3.3) em vez de números fixos:

- Parametrize a duração de uma parada **não programada**: `ΔP ∈ {30, 60, 120, 240}` min.
- Parametrize a redução obtida ao virar a parada **programada**: `ρ ∈ {50%, 70%, 90%}` (i.e., parada programada dura `ΔP · (1 − ρ)`).
- Critério de "antecipação útil": apenas TPs com `lead_time ≥ 30` min contam como evitados.
- Calcule **horas de parada evitadas** em todas as 12 combinações `(ΔP, ρ)` e apresente uma **tabela 4×3** + uma **superfície 3D ou heatmap** no Capítulo 5.

Vantagem: o resultado é honesto sobre incerteza nos parâmetros e oferece ao gestor uma **leitura por cenário** ("se a sua parada não programada típica é 2 h e a redução esperada é 70%, o modelo evita W horas/mês").

### 3.4 Cenários de aplicação (CM 1.2 — cenário concreto)

#### Cenário A — Painel do dispatcher (uso primário)

**Onde**: sala de controle da operação (Itabira). **Quem**: dispatcher de turno + supervisor de frota.
**Como**: a cada 5–15 min, o modelo recalcula o **score de Don't Go nas próximas 4 h** para todos os equipamentos ativos. O painel mostra a **lista priorizada** dos equipamentos com maior risco e o **lead time esperado**.
**Ação possível**: alocar inspeção rápida na próxima troca de turno, redirecionar o equipamento ao pátio mais próximo, ou trocar com um equipamento de reserva.
**Valor**: a parada vira **programada**, não emergencial.

#### Cenário B — Fila de prioridade da manutenção (uso complementar)

**Onde**: planejamento da manutenção preventiva. **Quem**: planejador de manutenção.
**Como**: ao final de cada turno, agregar os scores médios e máximos por equipamento → **fila ordenada** dos N equipamentos com maior risco acumulado nas últimas 24 h.
**Ação possível**: priorizar inspeções e revisões; ajustar a ordem do plano de manutenção semanal.
**Valor**: o orçamento limitado de horas de oficina é alocado **onde o risco é maior**, não pela rotação cronológica padrão.

#### Cenário C (stretch) — Detector de modos de falha emergentes

**Onde**: análise pós-operacional, semanal/mensal. **Quem**: engenharia de confiabilidade.
**Como**: monitorar o **score do modelo de anomalia (PA-3)** para sequências de telemetria que **não têm rótulo Don't Go** mas pontuam alto na anomalia.
**Ação possível**: revisar com o time de OEM se essas sequências indicam um **modo de falha novo** que justificaria adicionar uma regra ao catálogo CMA.
**Valor**: o sistema **aprende** modos de falha novos antes que eles sejam codificados manualmente — fechamento do ciclo regra→dado→regra.

### 3.5 Hipóteses iniciais de modelagem (a confirmar/refutar na EDA)

Registradas formalmente em `docs/hypotheses.md`. Resumo:

- **H1**: A taxa empírica de eventos `Is_Dont_Go=1` é < 0,1% do total de eventos de telemetria (forte desbalanceamento).
- **H2**: A grande maioria dos Don't Go precede uma sequência de pelo menos 3–5 alarmes do mesmo evento ou da mesma família (motor, transmissão, hidráulico) nas duas horas anteriores.
- **H3**: Existe **concentração temporal** dos Don't Go em determinados turnos (provavelmente o noturno) e/ou em finais de turno (fadiga acumulada do equipamento).
- **H4**: Determinadas frotas (modelos mais antigos) e/ou faixas de "Tag_Frota" concentram desproporcionalmente os Don't Go.
- **H5**: O operador (anonimizado) tem efeito mensurável — equipamentos operados por certos perfis de operador apresentam taxa Don't Go diferente da média da frota.
- **H6**: Existe **dependência de localidade** (relevante apenas se houver mais de uma localidade nos dados — a inspeção inicial sugere apenas Itabira).

### 3.6 Limitações declaradas a priori

- **Janela temporal de 6 meses** (jan–jun 2025) limita a captura de sazonalidades anuais (chuva/seca, paradas de manutenção planejadas) e ciclos plurianuais de desgaste.
- **Predominância de Itabira** na amostra inicial — generalização para outras minas (Carajás, S11D) é hipotética sem teste; confirmação formal de localidade única na Fase 2.
- **Apontamentos no parquet têm 7 colunas**, o dicionário lista 9 (faltam `Nome_Operador_Anon` e `Matricula_Operador_Hash`). Operador será **inferido** a partir da telemetria via D016 (moda do operador no intervalo do ciclo); se a inferência não for estável (< 80% de moda), H5 vira inconclusiva por construção.
- **Custo financeiro real** de cada cenário (parada programada vs. não programada vs. catastrófica) não está nos dados — usaremos uma **superfície de sensibilidade** parametrizada em `ΔP × ρ` (§3.3.4).
- **Predição da regra vs predição do risco subjacente**: a flag `Is_Dont_Go` é gerada pelo motor de regras CMA. O modelo, em janelas curtas, pode estar antecipando o disparo determinístico da regra ao invés do risco físico (§3.1.1). Mitigações: blackout de 5 min nas features (D010), análise estratificada por lead time bucket, treino em múltiplos horizontes paralelos (D001).
- **`Is_Dont_Go` como ground truth não é o mesmo que "falha física" como ground truth**: validação cruzada da flag com o catálogo CMA é prevista para a Fase 3 (D006); falhas físicas reais (que poderiam exigir um Don't Go que a regra não detectou) ficam fora do escopo deste estudo por ausência de outra fonte de verdade.

---

## 4. Decisões registradas nesta fase (resumo — ver `docs/decisions.md` para detalhes)

| # | Decisão | Justificativa resumida |
|---|---|---|
| **D001** (atualizada) | Múltiplas janelas em paralelo: H ∈ {1, 2, 4, 6, 8, 12} h | Robustez > custo computacional; descobre a janela ótima nos dados ao invés de impor a priori |
| **D002** | Métrica primária: AUC-PR | Don't Go é raro; AUC-ROC superestima sob desbalanceamento extremo |
| **D003** | Métrica operacional: Recall@P=0,5 + Lead time mediano | Compromisso explícito entre sensibilidade e custo de FP |
| **D004** | 3 lentes complementares: classificação (PA-1) + sobrevivência (PA-2) + anomalia (PA-3) | Responde "vai falhar?" + "quando?" + "fora do padrão?" |
| **D005** | Escopo: Itabira/MG (predominante na amostra inicial) | Confirmação formal na Fase 2; generalização é trabalho futuro |
| **D006** | `Is_Dont_Go` como ground truth, com validação cruzada vs. CMA na Fase 3 | Economiza rotulação manual; risco residual mitigado pela validação |
| **D007** | Entregável final: LaTeX/ABNT em `D:\TCC - versão final\article\` | Decisão do usuário; reuso do template `TCC_Evasao.tex` |
| **D008** | Unidade de predição: sliding window de 15 min por equipamento ativo | Mimetiza atualização do painel; dataset gerenciável |
| **D009** | Definição de "incidente Don't Go" = sequência maximal com gap ≤ 30 min | Evita inflar Recall/Lead time por eventos repetidos |
| **D010** | Anti-leakage: blackout de 5 min + proibições explícitas + análise por lead time bucket | Defesa contra "predizer a regra" ao invés do risco |
| **D011** | Validação: walk-forward expanding 4 folds + teste final intocado em junho + buffer de 4h | Robustez vs single hold-out; captura concept drift |
| **D012** | Pacote de métricas: AUC-PR + Lift + AUC-ROC + Brier + ECE + Recall@P=0,5 + Lead time | Comparabilidade externa + diagnóstico de calibração |
| **D013** | Definição formal de TP/FN/FP e Lead time por incidente | Inambiguidade necessária para reprodutibilidade |
| **D014** | Calibração: Platt + Isotonic, escolhido pelo melhor Brier/ECE | Padrão para LightGBM/XGBoost com classes raras |
| **D015** | Class imbalance: pesos OK; SMOTE proibido em séries temporais | Evita amostras "impossíveis" e leakage entre janelas |
| **D016** | Operador inferido pela moda da telemetria no intervalo do ciclo (≥ 80%) | Apontamentos não traz operador; permite testar H5 |
| **D017** | Sobrevivência: Cox PH com teste de Schoenfeld + Weibull AFT como fallback | Verificação obrigatória da hipótese de proporcional hazards |

---

## 5. Próximos passos (Fase 2 — Data Understanding/EDA)

Sem reabrir esta fase, os próximos passos iniciam o **CM 2.1**:

1. **Setup operacional (Fase 2A)**: criar `src/utils/paths.py` (paths centralizados), `src/utils/seeds.py` (SEED=42 em numpy/random/torch/lightgbm/xgboost), `src/data/loaders.py` (funções duckdb para ler telemetria sem estourar RAM, com conversão de `Valor` string→float, `Inicio_Turno`/`Fim_Turno` string→timestamp, normalização de `NULL` literal). Verificar `lifelines`/`prophet`/`pmdarima`. Gerar `requirements.txt`.
2. **Carregamento e estatísticas básicas (Fase 2B)**: shapes, dtypes, % nulos, duplicados, distribuição temporal por mês, estatísticas descritivas em `notebooks/02_data_understanding_eda.ipynb`.
3. **Confirmação de premissas da Fase 1**:
   - Localidade: confirmar se Itabira é único nos 6 meses inteiros (T3.2); se não, reabrir D005.
   - `Is_Dont_Go`: taxa empírica por mês, frota, equipamento (validar H001).
   - Pareamento Apontamento × Telemetria: % de eventos dentro de cada ciclo `[Inicio, Fim]` (T3.6).
   - Operador inferido (D016): % de ciclos com moda estável ≥ 80%.
   - Coluna `Porte` no exemplo Don't Go: descobrir origem (T3.7).
4. **Análise da variável alvo**: definição de "incidente Don't Go" (D009) aplicada — distribuição de gap entre Don't Gos consecutivos do mesmo equipamento (refinar tolerância de 30 min se necessário).
5. **Hipóteses iniciais**: testar H001 (taxa empírica), H002 (padrão sequencial), H003 (turnos), H004 (frotas), H005 (operador, se D016 viabilizar), H008 (coerência flag × CMA).
6. **Cobertura de eventos**: cruzar `Eventos O&M.Name` (147.943 nomes) com `telemetry.Alarme.unique()` para entender órfãos (T3.4).
7. **Materializar Figura 1 definitiva** em TikZ ou imagem vetorial (T3.5).
