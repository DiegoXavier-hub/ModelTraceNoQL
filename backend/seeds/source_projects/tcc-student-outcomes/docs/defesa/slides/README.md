# Slides — Defesa do TCC

**Trabalho:** Modelos Preditivos de Evasão Acadêmica — uma aplicação em cursos da FAGEN/UFU
**Autor:** Diego Henrique Xavier
**Curso:** Gestão da Informação — FAGEN/UFU

---

## Como abrir os slides

A apresentação é construída em **Reveal.js 5.1.0** (HTML/CSS/JS puro, sem build). Para visualizar:

### Opção 1 — Duplo clique
Abra `index.html` em qualquer navegador moderno (Chrome, Edge, Firefox). Recomendado: **Chrome** ou **Edge** para fidelidade visual e exportação PDF.

### Opção 2 — Servidor local (recomendado para evitar bloqueios CORS)
```bash
cd "D:\TCC - versão final\docs\defesa\slides"
python -m http.server 8000
# abra http://localhost:8000 no navegador
```

---

## Atalhos durante a apresentação

| Tecla | Ação |
|---|---|
| **→** ou **Espaço** | Próximo slide |
| **←** | Slide anterior |
| **F** | Tela cheia |
| **Esc** ou **O** | Visão geral (overview) de todos os slides |
| **S** | Abre janela de notas do palestrante |
| **B** ou **.** | Pausa (tela preta) |
| **Ctrl + Shift + F** | Busca dentro dos slides |

---

## Exportar para PDF (para imprimir ou enviar à banca)

1. Abra **Chrome** ou **Edge**
2. Acesse os slides com o sufixo `?print-pdf`:
   ```
   file:///D:/TCC%20-%20versão%20final/docs/defesa/slides/index.html?print-pdf
   ```
   Ou se estiver usando servidor local:
   ```
   http://localhost:8000/?print-pdf
   ```
3. Pressione **Ctrl + P** (ou **Cmd + P** no Mac)
4. Configure:
   - **Destino:** Salvar como PDF
   - **Layout:** Paisagem
   - **Margens:** Nenhuma
   - **Gráficos de fundo:** ✅ habilitado
   - **Tamanho do papel:** A4 ou Personalizado 1280×800
5. Clique em **Salvar**

---

## Estrutura da apresentação

### Slides principais (1–18) — ~20 minutos
| # | Slide | Tempo sugerido |
|---|---|---|
| 1 | Capa | 30s |
| 2 | Motivação · 58,3% de evasão | 60s |
| 3 | Pergunta de pesquisa | 60s |
| 4 | Objetivos | 45s |
| 5 | Base de dados | 75s |
| 6 | Janelas de observação (P1, P2, P4) | 60s |
| 7 | Pipeline completo | 90s |
| 8 | Split temporal estrito ⚠️ banca cava | 120s |
| 9 | Modelos candidatos | 75s |
| 10 | Por que F2? ⚠️ banca questiona | 90s |
| 11 | Resultados no teste 🎯 | 90s |
| 12 | Matrizes de confusão ⚠️ banca conta FN/FP | 90s |
| 13 | Comparação entre modelos | 75s |
| 14 | Interpretabilidade SHAP ⚠️ não é causalidade | 90s |
| 15 | Robustez (walk-forward, ablação, PSI) | 120s |
| 16 | Achados por subgrupo | 75s |
| 17 | Limitações (assumir antes da banca cavar) | 75s |
| 18 | Conclusão e próximos passos | 60s |
| Final | Obrigado | 15s |

**Total:** ~20 minutos com margem de 3 minutos.

### Slides backup (B1–B11) — para arguição
| # | Tópico | Quando usar |
|---|---|---|
| B1 | Validação estatística (resumo) | Pergunta sobre testes |
| B2 | Calibração (Platt vs isotônica) | Pergunta sobre probabilidade |
| B3 | Curvas Precisão-Recall | Trade-off precisão/recall |
| B4 | PSI / drift detalhado | Pergunta sobre robustez |
| B5 | Ablation study completo | "Modelo depende de qual variável?" |
| B6 | Curva de aprendizado | "Mais dados ajudariam?" |
| B7 | Anti-leakage (5 âncoras) | Pergunta sobre vazamento |
| B8 | Operacionalização | "Como a UFU usaria?" |
| B9 | Hiperparâmetros campeões | Pergunta sobre tuning |
| B10 | Mapa de riscos | "Qual a maior fragilidade?" |
| B11 | Comparação com literatura | "Como dialoga com Theotonio/Lee?" |

---

## Personalização rápida

### Trocar cores (paleta institucional)
Edite `theme.css`, no topo, dentro de `:root`:
```css
--ufu-blue: #1e3a8a;        /* azul institucional */
--ufu-blue-dark: #0f1e4d;   /* azul escuro para cover */
--ufu-gold: #f59e0b;        /* dourado de destaque */
```

### Trocar imagens institucionais
Substitua os PNGs em `img/` mantendo os mesmos nomes.

### Adicionar logo da UFU/FAGEN
1. Coloque `logo_ufu.png` em `img/`
2. No HTML do slide de capa, antes do `<span class="eyebrow">`, adicione:
   ```html
   <img src="img/logo_ufu.png" style="height:60px; margin-bottom:1.5em;" alt="UFU">
   ```

### Adicionar notas do palestrante
Dentro de qualquer `<section>`, adicione:
```html
<aside class="notes">
  Diga aqui o que você quer lembrar ao apresentar este slide.
</aside>
```
As notas só aparecem na **janela do palestrante** (tecla **S**).

---

## Checklist pré-defesa

- [ ] Testar em tela cheia (**F**) na resolução do projetor da banca
- [ ] Exportar PDF como **plano B** caso o computador da banca não rode HTML
- [ ] Levar PDF em pendrive **e** subir em nuvem (Drive)
- [ ] Cronometrar cada bloco (slides 1–6, 7–10, 11–16, 17–18)
- [ ] Revisar números do slide 11 (F2: 0,867 / 0,894 / 0,911)
- [ ] Reler slide 17 — assumir limitações antes da banca cavar
- [ ] Praticar transição entre slide principal e backup correspondente
- [ ] Ter o `preparacao_defesa.md` impresso ou no celular como cola final

---

## Estrutura de arquivos

```
docs/defesa/slides/
├── index.html      ← Apresentação principal (29 slides)
├── theme.css       ← Tema customizado UFU
├── README.md       ← Este arquivo
└── img/            ← Figuras do artigo (PNG)
    ├── fig_split_temporal.png
    ├── fig_matrizes_confusao.png
    ├── fig_shap_bar_p1.png
    ├── fig_shap_bar_p2.png
    ├── fig_shap_bar_p4.png
    ├── fig_estabilidade_walkforward.png
    ├── fig_ablation_study.png
    ├── fig_forest_plot_p2.png
    ├── fig_psi_drift.png
    ├── fig_calibracao_teste.png
    ├── fig_pr_curves_teste.png
    ├── fig_learning_curve.png
    └── fig_tabela_comparativa_teste.png
```

---

## Troubleshooting

**As figuras não aparecem.**
Você abriu via `file://` e o browser bloqueou. Use o servidor local (Opção 2 acima).

**O PDF exportado fica desformatado.**
Use o **Chrome** (não Firefox/Safari) e o sufixo `?print-pdf` na URL antes de abrir o diálogo de impressão.

**O texto está pequeno demais.**
Os slides são desenhados para 1280×800 (16:10). Em projetores 4:3 antigos, ajuste no `index.html`:
```js
Reveal.initialize({
  width: 1024,    // antes 1280
  height: 768,    // antes 800
  // ...
});
```

**Quero apresentar offline (sem internet).**
Baixe Reveal.js localmente em `vendor/reveal.js/` e troque os `<script>` e `<link>` que apontam para CDN por caminhos locais.

---

**Boa defesa!**
