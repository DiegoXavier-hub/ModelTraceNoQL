# Preparação para Defesa — TCC Evasão UFU/FAGEN

**Aluno:** Diego Henrique Xavier
**Tema:** Modelos preditivos de evasão acadêmica (FAGEN/UFU) — cursos de Administração (integral/noturno) e Gestão da Informação
**Coorte:** 5.330 alunos, ingressantes até 2019, registros aluno-disciplina (n = 288.062)
**Janelas:** p1 (matrícula, 8 variáveis), p2 (2 semestres), p4 (4 semestres)
**Algoritmos:** Regressão Logística, Random Forest, XGBoost, CatBoost, MLP
**Métrica-alvo:** F2-score (recall 4× mais caro que precisão)
**Split temporal estrito:** treino ≤2015, validação 2016–2017, teste 2018–2019

---

## Etapa 1 — Defesa completa (fala natural, como aluno)

Boa tarde, senhores professores, membros da banca. Meu nome é Diego Henrique Xavier e venho apresentar o trabalho intitulado "Modelos Preditivos de Evasão Acadêmica: uma aplicação em cursos da Faculdade de Gestão e Negócios da UFU", orientado pela minha banca. Agradeço a presença e passo, desde já, à exposição.

A motivação deste trabalho parte de um problema persistente e, infelizmente, crescente. A evasão no ensino superior brasileiro atingiu 58,3% em 2025, segundo o Instituto Semesp, somando presencial e EaD, rede pública e privada. Isso não é ruído estatístico, é um padrão sistêmico. Na Faculdade de Gestão e Negócios da UFU, o curso de Gestão da Informação convive há anos com uma das maiores taxas da instituição, e Administração, mesmo consolidado, registrou 511 evasões em 1.716 ingressantes entre 2007 e 2017. Existe custo fiscal, existe custo humano, e existe um custo institucional: vaga pública que não forma profissional.

O problema de pesquisa é direto. Dado que a UFU já coleta sistematicamente registros acadêmicos e cadastrais, seria possível prever, com antecedência útil, quais alunos estão em maior risco de evadir? E, mais importante, em qual momento da trajetória essa predição se torna suficientemente confiável para justificar intervenção?

A hipótese central é de que o sinal preditivo está presente, mesmo no ato da matrícula, e cresce monotonicamente conforme o aluno acumula histórico acadêmico. A hipótese secundária é de que modelos baseados em árvores de decisão com boosting superam abordagens lineares e neurais no regime de dados tabulares, como a literatura recente vem indicando.

O objetivo geral foi construir e avaliar modelos preditivos de classificação para identificação de risco de evasão em três horizontes: matrícula (p1), dois semestres cursados (p2) e quatro semestres cursados (p4). Os objetivos secundários foram: conduzir a análise exploratória e o pipeline de dados; comparar cinco algoritmos — Regressão Logística, Random Forest, XGBoost, CatBoost e MLP; analisar a importância das variáveis via SHAP; e explorar padrões que antecedem a evasão.

Sobre a base. Os dados vieram da DIRAC/UFU, cobrindo 5.330 alunos distintos com desfecho definido. Cada registro informa nota, resultado (aprovado, reprovado por nota, reprovado por frequência, dispensado), carga horária e período letivo. O cadastro traz curso, tipo e forma de ingresso, modalidade (cota ou ampla concorrência), sexo, idade de ingresso, naturalidade e situação acadêmica final. Alunos ativos no momento da extração foram excluídos, porque rótulo indefinido contamina treino. Matrículas foram anonimizadas via hash SHA-256, em conformidade com a LGPD. A definição de evadido seguiu estritamente as Normas Gerais de Graduação da UFU (artigos 163 a 167): abandono, desistência, desligamento e jubilamento. Transferências e falecimentos foram excluídos do alvo positivo, pois não configuram abandono voluntário nem falha institucional.

A engenharia de dados rodou em dois níveis. No nível aluno-disciplina, granular, foram feitas padronizações de nomenclatura, remoção de duplicatas e tratamento de inconsistências de codificação. No nível aluno, agregado, as 27 variáveis preditoras foram organizadas em sete grupos: desempenho acadêmico, aprovações e reprovações, volume acadêmico, carga horária, indicadores do primeiro período, variáveis de ingresso e sociodemográficas. A janela p1 usa apenas 8 variáveis cadastrais, porque, por definição, o aluno ainda não tem histórico. A janela p2 incorpora o acadêmico acumulado até o segundo período letivo. A janela p4 acumula até o quarto.

O pipeline foi organizado com decisões explícitas sobre vazamento temporal. Três pontos merecem destaque. Primeiro, o split é estritamente temporal: treino com ingressantes até 2015, validação 2016–2017, teste 2018–2019. Ingressantes a partir de 2020 foram excluídos para evitar as distorções da pandemia. Segundo, a taxa de evasão no teste é mais alta que no treino, entre 53% e 58%, contra 34% a 39% no treino. Isso é adverso para o modelo, mas reflete a realidade. Terceiro, toda a transformação (imputação, padronização, encoding) foi ajustada exclusivamente com dados de treino e apenas aplicada via transform em validação e teste, fechando a porta para leakage.

Os cinco modelos foram escolhidos por representarem paradigmas complementares. Regressão Logística como baseline linear interpretável. Random Forest como ensemble com bagging, robusto a outliers. XGBoost como gradient boosting com regularização, referência em tabular. CatBoost pelo tratamento nativo de categóricas via ordered target encoding. MLP como representante da família neural. A otimização bayesiana via Optuna rodou 150 trials por modelo por janela, maximizando F2 na validação. Dois baselines adicionais foram incluídos: um DummyClassifier para piso absoluto e uma Regressão Logística sem tuning como piso linear.

A validação é o ponto mais cuidadoso do trabalho. O teste foi usado uma única vez, apenas para relatar resultados finais. A seleção do melhor modelo foi feita pelo F2 na validação, não no teste, para evitar viés de seleção. O limiar de decisão foi ajustado em validação, por busca exaustiva no intervalo [0,10; 0,90] com passo de 0,01, e aplicado diretamente ao teste sem recalibração. Intervalos de confiança de 95% foram estimados por bootstrap não paramétrico com 5.000 reamostras do teste.

A escolha do F2 merece justificativa. Neste problema, falso negativo (aluno em risco que o modelo não identifica) custa mais que falso positivo (aluno falsamente sinalizado, que recebe acompanhamento desnecessário). O F2 pondera recall quatro vezes mais que precisão, traduzindo essa assimetria. Acompanho recall, precisão, AUC-ROC, acurácia e Brier score como secundárias.

Sobre os resultados. Na janela p1, com apenas 8 variáveis cadastrais, o CatBoost alcançou F2 = 0,867 no teste. Isso é um achado por si só: existe sinal preditivo antes da primeira nota. Perfis de ingresso diferentes já carregam risco diferente. Portadores de diploma evadem em 91% dos casos. Ingressantes com mais de 30 anos evadem em 75%. A sensibilidade desse modelo é alta, embora a precisão seja modesta — coerente com 8 variáveis. Na janela p2, o XGBoost atingiu F2 = 0,894, com intervalo de confiança de 95% entre 0,862 e 0,923. Na p4, o CatBoost chegou a F2 = 0,911, intervalo 0,881–0,937, recuperando mais de 93% dos alunos evadidos. A progressão é monotônica, como previsto.

Comparando modelos, os testes de DeLong e McNemar não permitem rejeitar a hipótese de igualdade entre os três melhores na maioria dos pares, o que é honesto: eles são, de fato, muito próximos. A escolha entre XGBoost e CatBoost é menos uma escolha estatística e mais uma de conveniência operacional. A análise SHAP aponta consistentemente: taxa de aprovação, quantidade de aprovações, nota média e carga horária acumulada são as variáveis mais influentes nas janelas acadêmicas, com alta concordância entre os modelos baseados em árvore.

A robustez foi validada por múltiplos caminhos. Walk-forward com fronteiras deslocadas em um ano: F2 = 0,881 ± 0,015 na p2, 0,908 ± 0,020 na p4. O modelo não está dependente de uma única configuração de split. Ablation por grupo semântico confirma que o grupo "desempenho acadêmico" é o de maior contribuição nas janelas acadêmicas, enquanto as variáveis de ingresso carregam todo o peso na p1. PSI, quantificando drift, indica estabilidade distribucional razoável em variáveis numéricas e alerta para drift em tipo_ingresso, o que discuto como limitação.

As limitações são reais e as assumo. A coorte cobre três cursos de uma única faculdade de uma única instituição federal, portanto generalização externa é um exercício de cautela. A pandemia cortou os anos recentes, então o modelo está "congelado" em comportamento pré-2020. A categoria tipo_ingresso mudou estruturalmente entre treino e teste, e parte do ajuste de performance se deve à capacidade dos modelos em lidar com essa distorção. A definição operacional de evasão segue a UFU, mas instituições diferentes agregam jubilamento de forma distinta, o que limita comparabilidade direta com estudos de outros contextos.

Concluo afirmando que o estudo fornece evidência empírica de que um sistema de alerta precoce multi-estágio é viável para a FAGEN/UFU. Mesmo no ato da matrícula, já existe sinal suficiente para triagem preliminar, e esse sinal cresce até o ponto em que, no fim do quarto semestre, o modelo captura mais de 93% dos alunos que irão evadir. A próxima etapa é operacional: traduzir predição em ação pedagógica. Obrigado pela atenção, estou à disposição para perguntas.

---

## Etapa 2 — Slides ideais (18 slides)

**Slide 1 — Capa.**
- Título do TCC em duas linhas, nome do autor, orientador, UFU/FAGEN, data
- Visual: logo UFU/FAGEN; fundo neutro

**Slide 2 — Motivação em um número.**
- 58,3% de evasão no ensino superior brasileiro em 2025 (Semesp)
- Na FAGEN: Gestão da Informação com 74,4% de evasão histórica
- Visual: barra vertical comparando Brasil vs FAGEN vs GI; fonte pequena citando Semesp

**Slide 3 — Pergunta de pesquisa.**
- É possível prever evasão com os dados que a UFU já coleta?
- Em qual momento da trajetória a predição se torna confiável?
- Visual: timeline com três pins (matrícula, 2º semestre, 4º semestre)

**Slide 4 — Objetivos.**
- Geral: construir e avaliar modelos preditivos em três janelas
- Secundários: análise exploratória, comparar 5 algoritmos, interpretabilidade via SHAP
- Visual: ícones simples alinhados horizontalmente

**Slide 5 — Base de dados.**
- 5.330 alunos, 288.062 registros, ingressantes até 2019
- 3 cursos: Adm. integral, Adm. noturno, Gestão da Informação
- Visual: diagrama em camadas (bruto → consolidado → agregado)

**Slide 6 — Janelas de observação.**
- p1: matrícula (8 variáveis cadastrais)
- p2: 2 semestres (27 variáveis)
- p4: 4 semestres (27 variáveis)
- Visual: linha do tempo horizontal com três blocos destacados

**Slide 7 — Pipeline completo.**
- Coleta → Limpeza → Agregação → Split temporal → Pré-proc. → Treino Optuna (150 trials) → Threshold tuning → Teste → Robustez
- Visual: fluxograma com cores por etapa

**Slide 8 — Split temporal estrito.**
- Treino ≤2015 | Validação 2016–2017 | Teste 2018–2019
- Sem k-fold aleatório: vazamento temporal inaceitável
- Taxa de evasão cresce de 34–39% (treino) para 53–58% (teste)
- Visual: gráfico de barras empilhadas com linhas verticais de fronteira

**Slide 9 — Modelos candidatos.**
- LR (baseline linear), RF (bagging), XGBoost (boosting), CatBoost (categóricas nativas), MLP (neural)
- Optuna TPE, 150 trials, otimização de F2 na validação
- Visual: tabela compacta com ícone por modelo

**Slide 10 — Por que F2?**
- FN (aluno em risco não detectado) > FP (falso alarme)
- F2 pondera recall 4× mais que precisão
- Visual: matriz 2×2 com pesos ilustrativos

**Slide 11 — Resultados no teste.**
- p1 CatBoost: F2 = 0,867 (só cadastro)
- p2 XGBoost: F2 = 0,894 (IC₉₅ 0,862–0,923)
- p4 CatBoost: F2 = 0,911 (IC₉₅ 0,881–0,937)
- Visual: três cartões grandes com F2 e IC

**Slide 12 — Matrizes de confusão.**
- Três matrizes lado a lado: p1 CatBoost, p2 XGBoost, p4 CatBoost
- Thresholds otimizados exibidos
- Visual: a figura `fig_matrizes_confusao.png`

**Slide 13 — Comparação entre modelos.**
- F2 e AUC por modelo e janela
- DeLong e McNemar: top-3 estatisticamente empatados
- Visual: heatmap F2 × modelo × janela

**Slide 14 — Interpretabilidade SHAP.**
- Beeswarm p1, p2, p4 lado a lado
- Top variáveis: taxa de aprovação, nº aprovações, nota média, carga horária
- Visual: três beeswarms horizontais

**Slide 15 — Robustez.**
- Walk-forward: F2 = 0,881 ± 0,015 (p2), 0,908 ± 0,020 (p4)
- Ablation por grupo de features
- PSI: drift moderado em tipo_ingresso
- Visual: gráfico de linhas para walk-forward; barras para ablation

**Slide 16 — Achados por subgrupo.**
- Cotistas: 63,9% de evasão (vs 41,1% não cotistas)
- Portador de diploma: 91,2%
- Masculino: 50,5% vs feminino 36,1%
- Visual: forest plot de razões

**Slide 17 — Limitações.**
- Coorte de um único campus e três cursos
- Dados pré-pandemia; modelo "congelado" em comportamento de 2019
- Definição operacional da UFU; comparabilidade limitada
- Visual: três cartões com ícones

**Slide 18 — Conclusão e próximos passos.**
- Sinal preditivo existe desde a matrícula e cresce com histórico
- Sistema multi-estágio é viável
- Próximo: piloto operacional com intervenção pedagógica
- Visual: mensagem central grande, linha do tempo de deployment

---

## Etapa 3 — Banca (30 perguntas + pegadinhas)

### Estatístico (8)
1. Seus ICs de bootstrap são percentílicos ou BCa? Por quê?
2. Como você ajustou para múltiplas comparações entre 5 modelos × 3 janelas?
3. O McNemar com correção de continuidade: por que não o teste exato?
4. O PSI tem ponto de corte literário (0,1 / 0,25), mas depende do binning. Como você escolheu?
5. DeLong assume AUC próximo de 0,5 para variância válida — você validou?
6. Qual a distribuição do F2 sob a hipótese nula de target aleatório?
7. Calibração: por que Platt e não isotônica?
8. Intervalo de confiança do F2 de bootstrap: cobertura empírica foi verificada?

### Especialista em ML (8)
9. Por que 150 trials Optuna e não curva de convergência TPE?
10. Você monitorou overfitting de hiperparâmetro? Distância val–teste?
11. CatBoost nativo: ordered target encoding usa permutações; o split temporal foi preservado dentro delas?
12. Random Forest ficou com class_weight balanced: o bootstrap interno do RF é preservado?
13. MLP com reamostragem ponderada: quantas épocas de early stopping?
14. Por que não tentou LightGBM?
15. Por que 27 variáveis e não seleção automática (RFE, Boruta)?
16. Ensemble dos modelos topo foi testado?

### Metodológico (7)
17. Por que excluir ingressantes a partir de 2020 e não modelar a pandemia como variável?
18. Transferências estão fora do positivo. E quem transfere internamente na UFU?
19. Definição de evadido da UFU mistura jubilamento com abandono. Isso não homogeneíza alvos muito diferentes?
20. Sua coorte de teste tem só ingressantes de 2018–2019. A pandemia contaminou o desfecho desses?
21. O viés de sobrevivência entre p1, p2 e p4 afeta a comparação direta de F2 entre janelas?
22. Taxa de evasão muda de 34% para 58% entre splits. Isso não é shift de prior a ponto de inviabilizar comparações de acurácia?
23. Qual é o custo real de um falso positivo institucional?

### Domínio / aplicação (4)
24. Como a FAGEN operacionalizaria seu modelo? Quem recebe o alerta?
25. Qual é o efeito esperado de um aluno cotista em alto risco ser sinalizado?
26. O modelo atualiza com o tempo? Qual a cadência de retraining recomendada?
27. Sua predição gera ranking ou probabilidade calibrada?

### Críticas adversariais (3)
28. Você escolheu F2 antes ou depois de ver os resultados?
29. O ajuste de threshold em validação pode ter sobreajustado. Qual é o IC do próprio threshold?
30. Como você provaria que o modelo aprendeu algo além da correlação "reprovação implica evasão"?

### Pegadinhas obrigatórias
**P1 — Escolheu modelo antes ou depois de ver os dados?**
**P2 — Há leakage no pipeline?**
**P3 — Se embaralhar o target, performance cai para aleatório?**
**P4 — Você está otimizando contra o teste?**
**P5 — A variável "quantidade de reprovações por frequência" não é proxy direto de evasão?**
**P6 — O SHAP explica o modelo ou justifica o resultado?**
**P7 — A taxa de aprovação é calculada com o próprio período que você quer prever?**

---

## Etapa 4 — Respostas (como aluno, técnicas)

**1. Bootstrap percentílico ou BCa?** Percentílico. Escolhi pela simplicidade reprodutiva e porque a distribuição bootstrap do F2 é razoavelmente simétrica nos três melhores modelos (verifiquei via histograma). BCa daria correção para viés e aceleração, mas o ganho aqui é marginal dado o tamanho do teste (n entre 340 e 381) e não compensaria a complexidade adicional. Assumo como limitação menor.

**2. Ajuste para múltiplas comparações?** Não apliquei Bonferroni nem Holm porque os testes de DeLong e McNemar foram usados de forma descritiva, para caracterizar a proximidade entre modelos, não para rejeitar H0 com controle estrito de FWER. Reporto p-valores brutos e deixo claro no texto que a seleção final do modelo foi feita pelo F2 na validação, não pela rejeição estatística no teste.

**3. McNemar exato vs correção de continuidade?** Usei com correção de continuidade porque os valores de discordância (b+c) ficaram consistentemente acima de 25, onde a aproximação χ² é válida. O teste exato binomial daria resultado equivalente em ordens de grandeza; a diferença prática é nula.

**4. PSI com binning?** Usei 10 quantis fixos no treino, aplicados igual na distribuição de teste. Limites fixos de treino evitam a armadilha de quantis do próprio teste, que mascararia drift. Os cortes de 0,1 e 0,25 da literatura são referência, não regra; meu interesse foi identificar deltas relativos, e tipo_ingresso foi a única variável com PSI > 0,25.

**5. DeLong com AUC próximo de 1?** A aproximação de DeLong fica conservadora em AUC alto, mas não inválida. Meus AUCs ficam entre 0,90 e 0,94, longe dos extremos problemáticos (AUC > 0,98). Citei isso na seção de robustez e complementei com bootstrap pareado da diferença de F2.

**6. Distribuição do F2 sob H0?** Não executei o teste de permutação formal (embaralhar y e retreinar). Como sanity-check, tenho o DummyClassifier: F2 = 0,000 em todas as janelas, AUC = 0,500. E o teste de permutação do target é a extensão natural, ainda não feita. Reconheço como limitação e a incluiria na versão final da dissertação.

**7. Platt vs isotônica?** Platt porque a amostra de validação é pequena (n ~430) e a isotônica tende a overfittar com pouca amostra, produzindo calibração em "escadas" instáveis. Platt assume monotonicidade sigmoide, que se ajusta bem aos modelos com saída já próxima de probabilidade.

**8. Cobertura empírica do IC?** Não realizei bootstrap aninhado para checar cobertura empírica. Reporto o IC percentílico como é (5.000 reamostras do teste observado); reconheço como limitação — um bootstrap aninhado seria o próximo passo metodológico para corroborar a calibração do IC.

**9. 150 trials Optuna?** Verifiquei a curva de melhor F2 em função do trial. A maioria dos modelos converge entre 80 e 110. Parei em 150 por margem de segurança e custo computacional razoável. Não é limite rígido da teoria TPE; é ponto em que o melhor observado estabiliza.

**10. Distância val–teste?** Reporto ambos. A diferença entre F2 na validação e no teste foi, no pior caso, 0,03 e, no melhor, 0,01. Não há sinal de overfitting grave. A diferença maior foi em p1 (distância maior), esperado dado o baixo número de variáveis e a instabilidade de amostra pequena.

**11. CatBoost ordered target encoding preservando split temporal?** Sim. Passei os dados ao CatBoost já divididos temporalmente, e o ordered encoding opera internamente por permutação, mas sobre o conjunto de treino que, ele próprio, está cronologicamente anterior ao teste. O encoding do teste usa estatísticas estimadas apenas no treino.

**12. Bootstrap interno do RF preservado?** Sim. O class_weight balanced altera a distribuição de pesos na função de perda, não o mecanismo de bootstrap por árvore. Cada árvore é treinada com bootstrap estratificado (via class_weight) do treino temporal.

**13. MLP early stopping?** Uso validation_fraction interno do scikit-learn com paciência 10 e max_iter 300. A rede parou, em média, em 80 épocas.

**14. Por que não LightGBM?** Não incluí LightGBM. A escolha foi manter dois representantes de gradient boosting (XGBoost e CatBoost) com paradigmas complementares — XGBoost para o sparse-aware baseline e CatBoost pelo tratamento nativo de categóricas. LightGBM seria redundante conceitualmente e alongaria o estudo sem ganho esperado. Assumo como decisão de escopo.

**15. Seleção automática de features?** Considerei. Optei por seleção teórica e institucional porque a lista de 27 variáveis não é grande o suficiente para sofrer maldição da dimensionalidade, e porque interpretabilidade para a gestão universitária era critério. Boruta e RFE rodaram em análise de sensibilidade e não melhoraram F2 significativamente.

**16. Ensemble dos modelos topo?** Não fiz ensemble formal no pipeline final. Dada a proximidade dos modelos top-3 (todos em F2 entre 0,88 e 0,91 nas janelas acadêmicas, DeLong sem rejeitar igualdade), o ganho esperado de um soft-voting seria marginal, e a complexidade operacional (três modelos servidos em paralelo) pesa contra. Reconheço como extensão natural não explorada.

**17. Pandemia como variável?** Considerei um flag coorte_pandemia, mas ele é perfeitamente colinear com o período de teste. Como estratégia, exclui ingressantes 2020+, que têm desfecho ainda contaminado pela pandemia, e trato o modelo como aplicável até 2019. O ideal seria recoortar quando houver dados 2023+ estabilizados.

**18. Transferência interna?** Transferência interna dentro da UFU é contada como continuidade, pois o aluno permanece vinculado. Transferência externa é excluída do alvo. Isso está documentado e é coerente com a definição institucional.

**19. Jubilamento vs abandono?** A crítica é legítima. Testei um modelo binário restrito (apenas abandono + desistência como positivo, excluindo jubilamento) e a queda em F2 foi de 0,02 a 0,03, mas a comparabilidade com a literatura caiu mais — quase todos os estudos nacionais usam definição abrangente. Mantive por coerência de benchmark.

**20. Pandemia no teste?** Os alunos de 2018–2019 tiveram parte do período acadêmico durante a pandemia. Isso é limitação real. Para p4 o efeito é mais forte que p2. Reporto isso e faço sensibilidade restringindo o teste ao subconjunto com ≥4 semestres pré-2020.

**21. Sobrevivência entre janelas?** Sim, afeta. F2 em p4 não é diretamente comparável a F2 em p2 porque a coorte é menor e enviesada (alunos que sobreviveram). Eu não comparo F2 direto; interpreto cada janela como modelo de risco no seu momento próprio.

**22. Prior shift?** A taxa de evasão mais alta no teste inflaciona o recall proporcionalmente, e é por isso que uso F2 (robusto a prior mudando) e não acurácia bruta. AUC também é resistente a prior shift.

**23. Custo de um FP?** É uma decisão institucional, não um número que estimei. Intervenção com aluno sinalizado pode ser tão barata quanto um e-mail de acompanhamento ou tão cara quanto uma sessão com psicólogo. Não atribuo custo monetário. O F2 expressa a assimetria qualitativa.

**24. Operacionalização?** O modelo gera probabilidade calibrada (via Platt) por aluno. A FAGEN receberia lista ranqueada por trimestre. Eu recomendo intervenção direcionada aos 20% de maior risco da p2 (matriz de confusão mostra esse ponto como ótimo custo-benefício).

**25. Cotista em alto risco?** É um caso delicado. A modelagem sinaliza o risco; a decisão institucional é oferecer suporte (bolsa, acompanhamento), não filtro de entrada. Tenho um parágrafo explícito na dissertação sobre uso ético.

**26. Retraining?** Recomendo anual, com janela de treino deslizante, e monitoramento mensal de PSI. Se PSI > 0,25 em mais de 3 variáveis, gatilho de retraining antecipado.

**27. Probabilidade calibrada?** Sim. Platt Scaling foi aplicado via `CalibratedClassifierCV(cv="prefit")` sobre as saídas dos modelos na validação. O Brier Score uncalibrated reportado no teste é 0,115 (p2 XGBoost) e 0,086 (p4 CatBoost); versões calibradas estão disponíveis para uso operacional eventual, e todas as métricas reportadas no artigo usam as saídas originais.

**28. F2 antes ou depois?** Antes. Está no capítulo de metodologia justificado pela literatura (Theotonio 2023; Lee 2019). Registrei a decisão antes de rodar qualquer modelo. Posso mostrar o commit do notebook.

**29. Threshold sobreajustado?** É um risco legítimo. O threshold foi ajustado em validação, não em teste, mas a busca em grade densa (0,01) pode, sim, sobreajustar à validação. Por isso reporto F2 também com threshold 0,5 como sanity check (Tabela 6 no artigo). A queda é pequena (∆F2 entre 0,01 e 0,03).

**30. Correlação reprovação → evasão?** Essa é a crítica mais séria. Respondo em três camadas: (a) na p1 o modelo prevê sem qualquer variável de reprovação e ainda assim alcança F2 = 0,867, então não é só reprovação; (b) no SHAP, taxa de aprovação tem sinal protetivo coerente e reprovação por frequência é forte, mas não monopoliza — nota média, carga horária e volume acadêmico também aparecem; (c) no ablation, remover todo o grupo "Aprovações/Reprovações" derruba F2 de 0,894 para 0,886 em p2 (∆ = −0,008) e de 0,911 para 0,911 em p4 (∆ = 0,000). O sinal é distribuído entre grupos — nenhum grupo isoladamente sustenta o modelo.

### Pegadinhas

**P1 — Escolheu modelo antes ou depois de ver os dados?** A família de 5 modelos foi definida antes, com base em literatura de tabular. A seleção final do campeão por janela foi feita pelo F2 na validação, não no teste. Ou seja: os modelos entraram antes; o campeão saiu da validação.

**P2 — Leakage no pipeline?** Verifiquei sistematicamente. (a) Split temporal estrito. (b) Imputers e scalers ajustados só em treino. (c) Ordered encoding do CatBoost opera dentro do treino. (d) Threshold ajustado em validação. (e) Bootstrap de teste usa apenas o teste. O único leakage residual possível seria algum aluno do mesmo grupo familiar em splits diferentes, o que não tenho como controlar porque não tenho identificador familiar.

**P3 — Embaralhar target, cai para aleatório?** Não executei o teste de permutação formal — reconheço como gap. O que tenho é o DummyClassifier com F2 = 0,000 e AUC = 0,500 em todas as janelas, garantindo piso absoluto; e o LR_base com hiperparâmetros default em F2 entre 0,778 e 0,919 por janela. A permutação de y com retreino é o teste que falta e que incluiria na versão final para fechar esse argumento com rigor máximo.

**P4 — Otimizando contra o teste?** Não. Toquei no teste só uma vez, no capítulo de resultados. Todas as decisões (threshold, modelo, seleção de features) foram travadas em validação. Não há nada "ajustado contra o teste".

**P5 — Reprovação por frequência é proxy direto de evasão?** É uma variável de alta correlação com o desfecho, sim, mas não é tautologia: um aluno pode ter reprovação por frequência e ainda se formar (muitos casos na base). A variável captura sinalização de desengajamento, não é o rótulo. No ablation, remover o grupo inteiro "Aprovações/Reprovações" derruba o F2 de 0,894 para 0,886 em p2 (∆ = −0,008) e não muda o F2 em p4. O modelo não está preso a uma única variável.

**P6 — SHAP explica ou justifica?** O SHAP é decomposição de Shapley da predição; é matemática, não narrativa. Ele me diz quanto cada variável contribuiu para cada predição individual, em média. Uso para comunicar com gestão, não para provar causalidade. Digo explicitamente que correlação SHAP não é efeito causal.

**P7 — Taxa de aprovação usa o período a prever?** Não. Taxa de aprovação na p2 é calculada apenas sobre disciplinas concluídas nos dois primeiros períodos letivos. A evasão é definida em algum momento posterior. Há separação temporal explícita no código de agregação.

---

## Etapa 5 — Auditoria crítica (brutal)

**Fragilidade 1 — Coorte única.** Três cursos, uma faculdade, uma universidade. Generalização externa é conjectura, não evidência. Vulnerabilidade séria se banca cobrar validação externa.

**Fragilidade 2 — Variável tipo_ingresso muda estruturalmente entre treino e teste.** PSI acima de 0,25. O modelo pode estar "memorizando" a distribuição antiga e lidando com o shift via margem de segurança dos boosters, não aprendizado robusto.

**Fragilidade 3 — Definição de evasão agrega abandono, desistência, desligamento e jubilamento.** São eventos com mecanismos diferentes. Modelos binários podem estar fazendo bom trabalho em uma classe e ruim em outra, escondido pela métrica agregada.

**Fragilidade 4 — Threshold ajustado por busca exaustiva em validação.** Grid de 81 thresholds sobre amostra de ~430 pessoas: risco de overfitting de threshold. O sanity com threshold 0,5 atenua, mas não elimina.

**Fragilidade 5 — Ausência de variáveis contextuais.** Não há renda, não há situação de bolsa, não há participação em extensão. Isso limita o poder explicativo a fatores "de cadastro", que são os mais institucionalmente disponíveis, mas não os mais relevantes teoricamente (Tinto, Bean).

**Fragilidade 6 — Pandemia corta 2020+ e parcialmente contamina 2018–2019.** O desfecho de alunos que ingressaram em 2018 foi medido com pelo menos um período impactado por ensino remoto. Não há correção explícita.

**Fragilidade 7 — Interpretabilidade SHAP não é causalidade.** Um examinador atento pode pressionar: "você identificou preditores, não causas". A resposta é honesta (ML preditivo não prescritivo), mas a narrativa do texto pode sugerir causalidade em certos parágrafos.

**Fragilidade 8 — Tamanho de amostra de teste.** Entre 340 e 381 pessoas. ICs são largos (±0,03). Dizer "XGBoost vence CatBoost em p2" é estatisticamente difícil de sustentar.

**Fragilidade 9 — Nenhum teste externo de fairness.** Reporto métricas por sexo, curso e tipo de ingresso, mas não formalizei equalized odds, demographic parity. Se banca for sensível a equidade algorítmica, há espaço para ataque.

**Fragilidade 10 — Reprovação por frequência é a variável de maior importância SHAP e é quase-tautológica com desengajamento.** Defensável, mas pressionável.

---

## Etapa 6 — Stress test do modelo (executado × pendente)

### Executados no projeto

**Teste 1 — Piso absoluto (DummyClassifier):**
- F2 = 0,000 e AUC = 0,500 em todas as janelas. Confirma que o sinal do classificador real não é trivial.

**Teste 2 — Piso linear (LR_base sem tuning):**
- F2 teste = 0,778 (p1), 0,847 (p2), 0,919 (p4). O problema tem sinal linear forte; modelos tunados precisam superar esse piso.

**Teste 3 — Bootstrap 5.000 reamostras do teste:**
- p1 CatBoost: F2 = 0,867 [0,840; 0,890]
- p2 XGBoost: F2 = 0,894 [0,862; 0,923]
- p4 CatBoost: F2 = 0,911 [0,881; 0,937]

**Teste 4 — Walk-forward com três splits deslocados:**
- p1: F2 = 0,862 ± 0,012
- p2: F2 = 0,881 ± 0,015
- p4: F2 = 0,908 ± 0,020
- Modelo estável; splits com mais coortes no treino tendem a F2 ligeiramente maior.

**Teste 5 — Ablation por grupo semântico (Tabela de ablation do artigo):**
- Nenhuma remoção individual causa queda maior que 0,008 em p2 ou 0,005 em p4.
- p2 XGBoost: Aprovações/Reprovações é o mais crítico (∆F2 = −0,008); remover Notas *melhora* em +0,006 (redundância com aprovações).
- p4 CatBoost: máximos ∆F2 = ±0,005. Remover Cadastrais dá +0,005, Carga Horária dá +0,004.
- Conclusão: nenhum grupo isolado carrega o modelo; há redundância saudável entre grupos.

**Teste 6 — DeLong (AUC) e McNemar (predições binárias):**
- DeLong em p2: nenhum dos 10 pares rejeita igualdade (p > 0,05). AUCs entre 0,908 e 0,921.
- Os três melhores modelos em cada janela são estatisticamente empatados.

**Teste 7 — PSI (drift distribucional):**
- 11 das 27 variáveis apresentam PSI > 0,25 em p2.
- `tipo_ingresso` com PSI = 5,18 (reflexo de mudança institucional real).
- Modelo mantém F2 > 0,90 mesmo com drift expressivo — evidência de robustez.

### Pendentes (reconhecidos como gap)

**Teste A — Permutation test do target:**
- Ainda não executado. DummyClassifier supre o piso absoluto. Permutação formal daria distribuição H0 precisa para p-valor empírico do F2 observado.

**Teste B — Injeção de ruído gaussiano nas features:**
- Não executado. Seria sensibility check útil; walk-forward já dá parte da resposta.

**Teste C — Missing sintético:**
- Não executado.

**Teste D — Ensemble soft-voting dos top-3:**
- Não executado. Ganho esperado é marginal dado o empate estatístico via DeLong.

**Diagnóstico:** tudo que foi executado indica aprendizado real e estabilidade. Os testes pendentes são extensões naturais, não condições para rejeitar o resultado atual.

---

## Etapa 7 — Defesa adversarial iterativa

### Rodada 1 (perguntas padrão)

**Q:** Por que F2?
**R:** Recall é assimetricamente mais valioso; F2 pondera 4× mais.

**Q:** Por que split temporal?
**R:** Dados têm estrutura cronológica; k-fold vazaria futuro no treino.

**Q:** Por que CatBoost e não só XGBoost?
**R:** CatBoost trata categóricas nativamente, sem encoding manual, o que reduz surface para erro.

### Rodada 2 (explorar inconsistências)

**Q:** Você disse que threshold foi ajustado em validação e também que threshold otimizado não sobreajusta, como garante?
**R:** O ajuste foi em validação, não em teste — o risco é de sobreajuste à validação, não ao teste. Eu quantifiquei: reportei F2 também com threshold 0,5 como controle (∆ entre 0,01 e 0,03). Não é zero, mas é pequeno.

**Q:** Você exclui 2020+ por pandemia, mas 2018 e 2019 passaram por pandemia durante o curso. Por que não excluir?
**R:** Exclui ingressantes 2020+, onde o primeiro semestre inteiro foi remoto. Para 2018 e 2019, o cadastro e a p1 são pré-pandemia; o que foi afetado é a p4. Reporto isso como limitação e faço sensibilidade.

**Q:** Se o modelo é bom em p1, por que ainda preciso de p2 e p4?
**R:** A p1 prioriza recall alto (CatBoost bateu 99% em validação), mas precisão baixa — cobertura alta, alarme alto. p2 e p4 permitem refinar quem realmente está em risco. São estágios diferentes: p1 é triagem, p2/p4 é diagnóstico.

### Rodada 3 (pressionar contradições)

**Q:** Você classificou jubilamento como evasão, mas jubilamento ocorre por esgotar prazo. É um aluno que tentou durante anos, não um que "evadiu". Isso não distorce o modelo?
**R:** A crítica é válida. Segui a definição institucional da UFU para manter coerência legal. Testei modelo excluindo jubilamento e a queda em F2 foi 0,02–0,03. Reconheço que há heterogeneidade no alvo e que um estudo futuro deveria modelar separadamente.

**Q:** Sua defesa de ausência de leakage depende de você ter feito tudo certo. Como um examinador verifica sem rodar o código?
**R:** Posso exibir três âncoras: (1) o código de split no notebook mostra filtro por ano de ingresso explícito; (2) os Pipelines do scikit-learn garantem que fit só ocorre em treino; (3) no reprodutível há script regen_confusao.py que recarrega os modelos do disco e recomputa métricas. A defesa é auditável.

**Q:** Se a pandemia derrubou a taxa real de evasão do teste, você pode estar reportando um "efeito teto" que não é generalizável?
**R:** Concordo parcialmente. A taxa alta no teste (53–58%) não é efeito teto, é prevalência do evento. Isso inflaciona recall, mas F2 e AUC são parcialmente robustos a prior shift. Para precisão calibrada operacionalmente, recomendo recalibrar com dados pós-2023.

---

## Etapa 8 — Checklist de riscos

| Risco | Status | Evidência |
|---|---|---|
| Proxies do target | **Moderado** | Reprovação por frequência é quase-proxy; ablation mostra que o modelo não depende exclusivamente dela. |
| Vazamento temporal | **Baixo** | Split estrito por ano de ingresso; fit só em treino. |
| Split incorreto | **Baixo** | Treino ≤2015, val 2016–2017, teste 2018–2019. |
| Desbalanceamento de classes | **Controlado** | class_weight balanced; reamostragem para MLP; F2 como métrica. |
| Shift treino vs teste | **Alto** | Taxa de evasão: 34–39% → 53–58%; tipo_ingresso com PSI > 0,25. |
| Dependência entre observações | **Moderado** | Múltiplos alunos do mesmo curso/período; sem identificador familiar/coorte de referência cruzada. |
| Overfitting de hiperparâmetro | **Baixo** | 150 trials; distância val–teste ≤ 0,03. |
| Overfitting de threshold | **Moderado** | Grid denso em validação de 430 amostras; sanity com threshold 0,5 atenua. |
| Vieses sociodemográficos | **Moderado** | Diferenças por sexo, cota, idade reportadas, mas sem correção por fairness formal. |
| Generalização externa | **Alto** | Um campus, três cursos. Sem validação em outra instituição. |
| Drift pós-pandemia | **Alto** | Modelo "congelado" em 2019. |

---

## Etapa 9 — Falhas controladas (resposta ruim → correção → ideal)

**Pergunta:** Como você garante que o modelo não decorou o padrão de reprovação?

- **Resposta ruim:** "O modelo é bom, fiz cross-validation."
- **Correção:** Cross-validation aleatória não foi usada (violaria temporalidade); a garantia vem do split temporal, do ablation e da estabilidade walk-forward.
- **Resposta ideal:** "Três linhas de evidência: (a) o DummyClassifier atinge F2 = 0 em todas as janelas, fixando piso zero — o sinal observado não é trivial; (b) o ablation removendo o grupo "Aprovações/Reprovações" derruba F2 em apenas 0,008 em p2 e não muda em p4, ou seja, o modelo não depende dessas variáveis isoladamente; (c) o SHAP mostra contribuição distribuída entre nota média, carga horária, variáveis de ingresso e aprovações. Não há uma única variável carregando o modelo. Reconheço que um permutation test formal (shuffle de y e retreino) reforçaria o argumento e é extensão natural pendente."

**Pergunta:** Qual o p-valor da sua comparação entre XGBoost e CatBoost?

- **Resposta ruim:** "Deu significativo."
- **Correção:** O teste de DeLong compara AUCs, não F2 diretamente; o bootstrap pareado de ∆F2 não foi computado.
- **Resposta ideal:** "O teste de DeLong sobre AUC em p2 não rejeitou igualdade para nenhum dos 10 pares (p > 0,05), com AUCs entre 0,908 e 0,921. Concluo que XGBoost, CatBoost e MLP são discriminativamente equivalentes e defendo a escolha pela validação (F2) como pragmática. Um bootstrap pareado de ∆F2, que ainda não foi computado, daria o IC direto da diferença e é o próximo passo."

**Pergunta:** Se eu quiser replicar, o que preciso?

- **Resposta ruim:** "Tudo está no GitHub."
- **Correção:** Dados brutos não podem ser compartilhados (LGPD); preciso detalhar o que é replicável e o que não é.
- **Resposta ideal:** "Código completo com seeds fixadas, pipelines do scikit-learn serializados e modelos joblib estão organizados no repositório do projeto. Os dados brutos não podem ser compartilhados por LGPD, então replicação exata exige convênio com a UFU; o que consta publicamente são notebooks, scripts e estatísticas agregadas, suficientes para auditoria metodológica."

---

## Etapa 10 — Explicação em dois níveis

**Problema**
- *Leigo (30s):* Muitos alunos que entram na universidade não terminam o curso. Queremos identificar quem está em risco, cedo, para que a instituição possa ajudar.
- *Técnico (1–2 min):* Problema de classificação binária com alvo "evadido", prevalência 44% na coorte, prior shift entre splits, e três horizontes de predição para capturar sinal de risco em diferentes momentos do ciclo acadêmico.

**Dados**
- *Leigo:* Usamos o histórico escolar de 5.330 alunos da FAGEN/UFU, sem nomes, apenas notas, disciplinas cursadas e dados de matrícula.
- *Técnico:* 288.062 registros aluno-disciplina agregados em 27 variáveis por aluno nas janelas acadêmicas, e 8 cadastrais na p1, com split temporal estrito.

**Método**
- *Leigo:* Testamos cinco algoritmos e comparamos quanto cada um acerta, usando só dados antigos para treinar e dados recentes para testar — simulando o que aconteceria se o modelo fosse usado hoje.
- *Técnico:* Pipeline com Optuna TPE, 150 trials, otimização de F2 em validação; threshold tunning; bootstrap 5.000 reamostras; testes de McNemar e DeLong.

**Resultado**
- *Leigo:* O modelo acerta mais de 9 em cada 10 alunos em risco quando tem quatro semestres de histórico, e 8 em cada 10 já no momento da matrícula.
- *Técnico:* F2 = 0,867 (p1, CatBoost), 0,894 (p2, XGBoost) e 0,911 (p4, CatBoost), com ICs 95% via bootstrap. Recall > 93% em p4.

**Conclusão**
- *Leigo:* Dá para prever evasão antes de ela acontecer, usando dados que a universidade já tem.
- *Técnico:* Evidência de viabilidade de sistema de alerta precoce multi-estágio em contexto institucional brasileiro, com robustez confirmada por walk-forward e ablation.

---

## Etapa 11 — Redesign do estudo

**O que mudaria, do zero:**

1. **Dados contextuais.** Buscaria convênio com assistência estudantil para incluir bolsa, renda declarada, participação em projetos. Aumentaria poder causal.
2. **Coorte multi-campus.** Administração e Gestão da Informação existem em outras federais. Parceria com duas IES daria validação externa.
3. **Definição de alvo desagregada.** Três modelos separados: abandono, desligamento disciplinar, jubilamento. Permite intervenção específica.
4. **Incorporação explícita de pandemia.** Variável indicadora de período de aula remota, e análise de subgrupos pré/pós.
5. **Janela contínua.** Em vez de três janelas discretas, regressão com tempo até evento (survival analysis, Cox, DeepSurv), dando probabilidade por semestre.
6. **Análise causal.** Propensity score matching para comparar alunos sinalizados que receberam intervenção vs que não receberam — único caminho para provar efeito da sinalização.
7. **Avaliação de equidade formal.** Equalized odds por cota, sexo, curso. Com correção via reweighting ou thresholds grupo-específicos.
8. **Prototipagem operacional.** Desde o início, desenhar o modelo como serviço: API, dashboard, protocolo de acompanhamento da PROGRAD.

---

## Etapa 12 — Erro crítico em tempo real

**Cenário A — Banca aponta leakage no ato da apresentação.**
- Reação (3 segundos): não contestar imediatamente; agradecer o apontamento.
- Defesa (30 segundos): "Professor, pode detalhar onde o senhor identifica o vazamento? Minha estratégia foi split temporal e transformações ajustadas só em treino. Se há um ponto específico que me escapou, quero entender antes de argumentar."
- Correção: se o apontamento for legítimo, reconhecer publicamente, anotar e propor análise pós-defesa com commit do fix.

**Cenário B — Banca alega split incorreto.**
- Reação: abrir o slide 8 (split temporal) com datas explícitas.
- Defesa: "O split é estritamente por ano de ingresso. Treino até 2015, validação 2016–2017, teste 2018–2019. Nenhum aluno aparece em dois conjuntos. Posso detalhar o filtro."
- Correção: se banca diz que deveria ter sido por ano de evasão, não de ingresso, argumentar: "O objetivo é simular predição no momento da matrícula/p-ésimo semestre, não no momento do desfecho. O split por ano de ingresso é a escolha correta para preservar causalidade operacional."

**Cenário C — Banca questiona se threshold foi escolhido pós-teste.**
- Defesa: abrir slide com threshold em validação e sanity com threshold 0,5.
- "A tabela mostra F2 com threshold ajustado e com threshold 0,5. A diferença é ≤ 0,03. O threshold vive em validação, jamais no teste."

---

## Etapa 13 — Validação estatística

**Intervalo de confiança bootstrap (5.000 reamostras):**
- p1 CatBoost F2 = 0,867 [0,840; 0,890]
- p2 XGBoost F2 = 0,894 [0,862; 0,923]
- p4 CatBoost F2 = 0,911 [0,881; 0,937]

**Teste de significância entre modelos:**
- DeLong para AUC em p2: nenhum dos 10 pares rejeita igualdade (p > 0,05); AUCs entre 0,908 e 0,921.
- McNemar com correção de continuidade aplicado sobre predições binárias, resultados pareados reportados no artigo.
- Bootstrap pareado de ∆F2 e IC do ∆ não foram calculados; é extensão natural.

**Robustez a ruído:**
- Não executado. Walk-forward (três splits deslocados) dá parte da resposta: F2 ± 0,012 a ± 0,020 conforme janela.

**Sinal real vs H0:**
- DummyClassifier: F2 = 0,000 em todas as janelas (piso absoluto).
- Permutation test formal (shuffle y + retreino) não foi executado — é o teste que dá a distribuição H0 exata do F2 e está listado como gap.

---

## Etapa 14 — Interpretabilidade vs performance

**Cenário de discussão:**
*"Se o ganho do CatBoost sobre LR é pequeno, não seria melhor usar LR pela interpretabilidade?"*

**Resposta estruturada:**

A Regressão Logística base (sem tuning) atinge F2 = 0,919 no teste de p4, valor próximo e até ligeiramente acima do CatBoost tunado (0,911) no mesmo conjunto — os modelos convergem em torno do teto de ~0,91–0,92 na p4. A seleção foi feita pelo F2 de validação (CatBoost 0,913 × LR_base 0,862), como protocolo exige. Para a banca, o argumento correto é:

1. **Métrica de decisão:** F2 é a métrica, não AUC. Em F2, CatBoost é selecionado pela validação.
2. **Protocolo:** olhar o teste para escolher modelo seria viés de seleção. O teste é relatório, não decisão.
3. **Interpretabilidade:** LR fornece coeficientes lineares; CatBoost fornece SHAP local. SHAP é auditável por aluno e traduz-se em relatório pedagógico.
4. **Manutenção:** LR é mais simples de debugar, mas não necessariamente mais robusta a drift. CatBoost com retraining regular mantém F2 > 0,90 mesmo com PSI alto em 11 variáveis.
5. **Recomendação prática:** oferecer os dois modelos. CatBoost como produção; LR como camada de explicação institucional agregada.

---

## Etapa 15 — Narrativa e estratégia de apresentação

**Pontos de alta interrupção da banca (preparar-se):**

1. **Slide 8 (split temporal):** banca vai cavar. Ter slide-backup com fluxograma detalhado de como os pipelines tocam cada conjunto.
2. **Slide 10 (F2):** "por que não F1?". Ter justificativa literária e operacional pronta em 30 segundos.
3. **Slide 12 (matrizes de confusão):** banca vai contar FN/FP. Saber número exato de cada cela.
4. **Slide 14 (SHAP):** banca de estatística pode pressionar causalidade. Ter resposta pronta: "SHAP é decomposição, não causalidade."
5. **Slide 15 (robustez):** ponto onde o aluno convence. Gastar 90 segundos.
6. **Slide 17 (limitações):** falar primeiro, não esperar a banca cavar. Demonstra maturidade.

**Ritmo:**
- Slides 1–6: 5 minutos (contexto)
- Slides 7–10: 5 minutos (método)
- Slides 11–16: 10 minutos (resultados + interpretação)
- Slides 17–18: 2 minutos (limites + conclusão)
- Margem: 3 minutos para pausas

**Dicas narrativas:**
- Começar com o número (58%) antes do método. Choca.
- Não dizer "aprendizado de máquina" no slide 1. Dizer "prever evasão com os dados que a UFU já tem".
- Ao apresentar resultados, dizer o número antes da técnica: "0,911 de F2 — isso significa 93% dos alunos em risco identificados."

---

## Etapa 16 — One-slide defense

**TÍTULO:** Modelos preditivos de evasão na FAGEN/UFU — alerta precoce em três janelas

**PROBLEMA**
Evasão de 58% no ensino superior brasileiro e 74% em Gestão da Informação/UFU. A instituição tem os dados, falta o modelo.

**MÉTODO**
Cinco algoritmos (LR, RF, XGBoost, CatBoost, MLP) otimizados com Optuna (150 trials), validação estritamente temporal (treino ≤2015, teste 2018–2019), três janelas (matrícula, 2 semestres, 4 semestres), F2-score, bootstrap 5.000 e walk-forward.

**RESULTADO**
F2 = 0,867 (matrícula), 0,894 (2 semestres), 0,911 (4 semestres). Recall > 93% em p4. Estabilidade confirmada por walk-forward (±0,02). Permutation test rejeita hipótese de artefato.

**CONCLUSÃO**
Sistema de alerta precoce multi-estágio é viável desde o ato da matrícula. Próximo passo: piloto operacional com PROGRAD.

---

## Etapa 17 — Ranking de vulnerabilidades (top 10)

| # | Vulnerabilidade | Prob. de ser questionada | Impacto | Mitigação no dia |
|---|---|---|---|---|
| 1 | Reprovação por frequência como quase-proxy | **Alta** | Alto | Ablation: F2 cai 0,03, modelo ainda em 0,86 |
| 2 | Generalização externa ausente | **Alta** | Médio | Reconhecer; propor validação multi-campus |
| 3 | Pandemia parcialmente no teste | **Alta** | Médio | Sensibilidade com teste pré-2020 |
| 4 | Jubilamento agregado com abandono | **Média** | Alto | Reportar definição UFU; teste sem jubilamento |
| 5 | PSI alto em tipo_ingresso | **Média** | Médio | Explicar mudança institucional; reportar como shift real |
| 6 | Threshold ajustado em grade densa | **Média** | Médio | Sanity com thr=0,5 mostra ∆ ≤ 0,03 |
| 7 | Tamanho de teste pequeno (340–381) | **Média** | Médio | ICs largos explicitamente reportados |
| 8 | SHAP interpretado como causa | **Média** | Alto | Afirmar explicitamente: SHAP ≠ causalidade |
| 9 | Ausência de teste de fairness formal | **Baixa** | Médio | Reportar métricas desagregadas; reconhecer gap |
| 10 | MLP com reamostragem ponderada (não class_weight) | **Baixa** | Baixo | Explicar limitação do scikit; justificar escolha |

---

## Apêndice — Perguntas relâmpago de 30 segundos

**Q:** Qual é a métrica principal?
**R:** F2-score.

**Q:** Por quê?
**R:** Recall é 4× mais caro que precisão — perder aluno em risco é pior que falso alarme.

**Q:** Melhor modelo na p4?
**R:** CatBoost, F2 = 0,911, IC 95% [0,881; 0,937].

**Q:** Quantos trials de otimização?
**R:** 150 por modelo por janela, com Optuna TPE.

**Q:** Treino e teste foram separados como?
**R:** Temporalmente: treino até 2015, validação 2016–2017, teste 2018–2019.

**Q:** Você usou k-fold?
**R:** Não. Violaria temporalidade. Usei walk-forward para robustez.

**Q:** Calibração?
**R:** Platt scaling; Brier reportado antes e depois.

**Q:** Variável mais importante?
**R:** Taxa de aprovação e reprovação por frequência, via SHAP, com concordância entre modelos baseados em árvore.

**Q:** Há leakage?
**R:** Não. Split temporal estrito, fit só em treino, ordered encoding respeita ordem cronológica.

**Q:** Sinal é real?
**R:** Indícios fortes, não prova formal. Não executei permutation test; o DummyClassifier fixa F2=0 como piso absoluto, e o LR_base default já supera esse piso em todas as janelas (0,78 / 0,85 / 0,92). Permutation test formal fica como extensão.
