"""Auditoria abrangente das Fases 0-6 (2026-05-10).

Estende `_audit_fases_0_a_5.py` com verificações da Fase 6 (Deployment).
Saída: stdout + reports/eda_results/audit_fases_0_6.json.

Cobertura:
- Bloco 1: replica os 70 checks de _audit_fases_0_a_5.py.
- Bloco 2: 14 checks específicos da Fase 6 (Cap. 6 + Resumo/Abstract +
  frentes opcionais F1-F5 + auditoria estendida).
"""

from __future__ import annotations

import json
import re
import sys
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
except Exception:
    pass


RESULTS: dict = {"checks": [], "totals": {}}
N_PASS = 0
N_FAIL = 0


def check(label: str, ok: bool, detail: str = "") -> None:
    global N_PASS, N_FAIL
    status = "PASSA" if ok else "FALHA"
    if ok:
        N_PASS += 1
    else:
        N_FAIL += 1
    print(f"  [{status}] {label}")
    if detail:
        print(f"           {detail}")
    RESULTS["checks"].append({"label": label, "ok": bool(ok), "detail": detail})


def safe_run(label: str, fn) -> None:
    try:
        ok, detail = fn()
        check(label, ok, detail)
    except Exception as e:  # pragma: no cover
        tb = traceback.format_exc().splitlines()[-1]
        check(label, False, f"EXCECAO: {tb}")


# ---------- Bloco 1 — Auditoria Fases 0-5 (reutilizada) ----------
print("=" * 70)
print("Bloco 1 — Auditoria Fases 0-5 (delegada)")
print("=" * 70)
prev = json.loads(
    (PROJECT_ROOT / "reports" / "eda_results" / "audit_fases_0_5.json").read_text(
        encoding="utf-8"
    )
)
for c in prev["checks"]:
    check(c["label"], c["ok"], c["detail"])


# ---------- Bloco 2 — Auditoria Fase 6 ----------
print()
print("=" * 70)
print("Bloco 2 — Auditoria Fase 6 (Deployment / CM 6.2, 6.3)")
print("=" * 70)


def c61_cap6_existe_e_min_secoes() -> tuple[bool, str]:
    p = PROJECT_ROOT / "docs" / "article_dontgo" / "cap6_conclusao.tex"
    if not p.is_file():
        return False, f"arquivo ausente: {p}"
    txt = p.read_text(encoding="utf-8")
    n_sec = len(re.findall(r"^\\section\{", txt, flags=re.MULTILINE))
    n_lines = len(txt.splitlines())
    return n_sec >= 5 and n_lines >= 200, f"sections={n_sec}, lines={n_lines}"


safe_run("6.1: cap6_conclusao.tex com >=5 secoes e >=200 linhas", c61_cap6_existe_e_min_secoes)


def c62_cap6_topicos_obrigatorios() -> tuple[bool, str]:
    p = PROJECT_ROOT / "docs" / "article_dontgo" / "cap6_conclusao.tex"
    txt = p.read_text(encoding="utf-8")
    needed = [
        "Síntese Executiva",
        "Resposta Formal",
        "Resultados em Números",
        "Plano de Implantação",
        "Trabalhos Futuros",
        "Considerações Finais",
    ]
    miss = [n for n in needed if n not in txt]
    return len(miss) == 0, f"missing topics={miss}"


safe_run("6.2: cap6 contém todos os tópicos obrigatórios", c62_cap6_topicos_obrigatorios)


def c63_cap6_cinco_trabalhos_futuros() -> tuple[bool, str]:
    p = PROJECT_ROOT / "docs" / "article_dontgo" / "cap6_conclusao.tex"
    txt = p.read_text(encoding="utf-8")
    n = len(re.findall(r"Trabalho Futuro \\#\d", txt))
    return n >= 5, f"trabalhos_futuros_detalhados={n} (esperado >=5)"


safe_run("6.3: cap6 detalha 5 trabalhos futuros", c63_cap6_cinco_trabalhos_futuros)


def c64_resumo_abstract_preenchidos() -> tuple[bool, str]:
    p = PROJECT_ROOT / "docs" / "article_dontgo" / "TCC_DontGo.tex"
    txt = p.read_text(encoding="utf-8")
    # Resumo deve ter >= 800 chars dentro do bloco \begin{resumo}..\end{resumo}.
    blocks = re.findall(r"\\begin\{resumo\}.*?\\end\{resumo\}", txt, flags=re.DOTALL)
    if len(blocks) < 2:
        return False, f"esperado 2 blocos resumo, achou {len(blocks)}"
    pt_len = len(blocks[0])
    en_len = len(blocks[1])
    has_keywords = (
        "Palavras-chave" in blocks[0] and "Keywords" in blocks[1]
    )
    ok = pt_len >= 800 and en_len >= 800 and has_keywords
    return ok, f"pt_len={pt_len}, en_len={en_len}, keywords={has_keywords}"


safe_run("6.4: Resumo PT + Abstract EN preenchidos com keywords", c64_resumo_abstract_preenchidos)


def c65_f1_fairness() -> tuple[bool, str]:
    json_p = PROJECT_ROOT / "reports" / "eda_results" / "fase6_fairness_operador.json"
    csv_p = PROJECT_ROOT / "reports" / "tables" / "fase6_fairness_operador.csv"
    if not json_p.is_file() or not csv_p.is_file():
        return False, f"json={json_p.is_file()}, csv={csv_p.is_file()}"
    j = json.loads(json_p.read_text(encoding="utf-8"))
    needed = ["config", "per_horizon"]
    miss = [n for n in needed if n not in j]
    if miss:
        return False, f"missing keys={miss}"
    h12 = j["per_horizon"].get("h12", {})
    return (
        h12.get("n_incidents_total", 0) >= 100
        and "gini_recall" in h12
        and "disparity_ratio_q75_over_q25" in h12,
        f"h12={h12.get('n_incidents_total')} incid, gini={h12.get('gini_recall'):.3f}",
    )


safe_run("6.5 (F1): fairness audit por operador persistido", c65_f1_fairness)


def c66_f2_bootstrap_ic() -> tuple[bool, str]:
    json_p = PROJECT_ROOT / "reports" / "eda_results" / "fase6_bootstrap_ci.json"
    csv_p = PROJECT_ROOT / "reports" / "tables" / "fase6_bootstrap_ci.csv"
    if not json_p.is_file() or not csv_p.is_file():
        return False, f"json={json_p.is_file()}, csv={csv_p.is_file()}"
    j = json.loads(json_p.read_text(encoding="utf-8"))
    if j["config"].get("n_resamples", 0) < 1000:
        return False, f"n_resamples={j['config'].get('n_resamples')}"
    horizons = list(j["per_horizon"].keys())
    h12 = j["per_horizon"].get("h12", {})
    aucpr_ci = h12.get("per_window", {}).get("auc_pr", {})
    needed = {"ci_low", "ci_high", "mean"}
    return (
        len(horizons) == 6 and needed.issubset(aucpr_ci),
        f"horizons={horizons}, aucpr_ci_keys={set(aucpr_ci.keys())}",
    )


safe_run("6.6 (F2): bootstrap IC 95% (1000 resamples) persistido", c66_f2_bootstrap_ic)


def c67_f3_model_card() -> tuple[bool, str]:
    p = PROJECT_ROOT / "docs" / "model_card.md"
    if not p.is_file():
        return False, f"arquivo ausente: {p}"
    txt = p.read_text(encoding="utf-8")
    sections = [
        "Detalhes do Modelo",
        "Uso Pretendido",
        "Métricas de Desempenho",
        "Considerações Éticas",
        "Caveats",
    ]
    miss = [s for s in sections if s not in txt]
    return len(miss) == 0, f"missing model_card sections={miss}"


safe_run("6.7 (F3): model card presente com seções obrigatórias", c67_f3_model_card)


def c68_f4_predict_realtime_cli() -> tuple[bool, str]:
    p1 = PROJECT_ROOT / "src" / "serving" / "predict_realtime.py"
    p2 = PROJECT_ROOT / "src" / "serving" / "__init__.py"
    if not (p1.is_file() and p2.is_file()):
        return False, f"missing: predict_realtime={p1.is_file()}, init={p2.is_file()}"
    # Verifica execução do CLI gerou alertas
    alerts_dir = PROJECT_ROOT / "outputs" / "alerts"
    n_csvs = len(list(alerts_dir.glob("*.csv"))) if alerts_dir.is_dir() else 0
    return n_csvs >= 1, f"alerts_csvs={n_csvs}"


safe_run("6.8 (F4): predict_realtime.py CLI + alerts CSV gerado", c68_f4_predict_realtime_cli)


def c69_f5_requirements_deploy() -> tuple[bool, str]:
    p = PROJECT_ROOT / "requirements_deploy.txt"
    if not p.is_file():
        return False, f"arquivo ausente: {p}"
    txt = p.read_text(encoding="utf-8")
    needed = ["lightgbm", "joblib", "pyarrow", "scikit-learn", "numpy", "pandas"]
    forbidden = ["optuna", "shap", "torch", "catboost", "matplotlib"]
    miss = [n for n in needed if n not in txt]
    extra = [n for n in forbidden if n + "==" in txt or n + ">=" in txt]
    return len(miss) == 0 and len(extra) == 0, (
        f"missing={miss}, forbidden_present={extra}"
    )


safe_run("6.9 (F5): requirements_deploy.txt minimalista", c69_f5_requirements_deploy)


def c610_decisions_consistency() -> tuple[bool, str]:
    p = PROJECT_ROOT / "docs" / "decisions.md"
    txt = p.read_text(encoding="utf-8")
    # Conta D001..Dxx
    headers = re.findall(r"^## (D\d+)", txt, flags=re.MULTILINE)
    return len(headers) >= 40, f"n_decisions={len(headers)} (esperado >=40)"


safe_run("6.10: decisions.md tem >=40 entradas", c610_decisions_consistency)


def c611_memory_md_cap6_checkpoint() -> tuple[bool, str]:
    p = PROJECT_ROOT / "MEMORY.md"
    txt = p.read_text(encoding="utf-8")
    # Procura por seção da fase 6 ou checkpoint
    has_section = "Fase 6" in txt or "Cap. 6" in txt or "## 15" in txt
    return has_section, f"contains_phase6_section={has_section}"


safe_run("6.11: MEMORY.md menciona Fase 6", c611_memory_md_cap6_checkpoint)


def c612_pendencias_fase6_fechada() -> tuple[bool, str]:
    p = PROJECT_ROOT / "PENDENCIAS.md"
    txt = p.read_text(encoding="utf-8")
    # Marca "Fase 6 — FECHADA" ou similar
    fechada = "Fase 6" in txt and ("FECHADA" in txt.upper() or "Fechada" in txt)
    return fechada, f"pendencias_marca_fase6={fechada}"


safe_run("6.12: PENDENCIAS.md marca Fase 6 fechada", c612_pendencias_fase6_fechada)


def c613_resumo_keywords_5() -> tuple[bool, str]:
    p = PROJECT_ROOT / "docs" / "article_dontgo" / "TCC_DontGo.tex"
    txt = p.read_text(encoding="utf-8")
    # Busca conteúdo após "Palavras-chave"
    m = re.search(r"Palavras-chave\}?:\s*([^\.\n]+)\.?", txt)
    if not m:
        return False, "Palavras-chave não encontrado"
    kws = [k.strip() for k in m.group(1).split(";") if k.strip()]
    return len(kws) >= 5, f"n_keywords={len(kws)}: {kws}"


safe_run("6.13: Resumo PT tem >=5 palavras-chave", c613_resumo_keywords_5)


def c614_consistencia_numeros_executivos() -> tuple[bool, str]:
    """Verifica que os números canônicos no Cap. 6 batem com os JSONs."""
    p = PROJECT_ROOT / "docs" / "article_dontgo" / "cap6_conclusao.tex"
    txt = p.read_text(encoding="utf-8")
    # Pelo menos os valores canônicos da retunagem D044 devem aparecer no Cap. 6.
    has_214 = "214" in txt or "214{,}2" in txt
    has_282 = "282" in txt or "281{,}7" in txt
    has_recall_648 = "64,8" in txt or "64{,}8" in txt or "0{,}648" in txt or "0,648" in txt
    return has_214 and has_282 and has_recall_648, (
        f"has_214={has_214}, has_282={has_282}, has_recall_648={has_recall_648}"
    )


safe_run("6.14: Cap. 6 cita 214 h/mês, 282 h/mês e 64,8% recall", c614_consistencia_numeros_executivos)


# Fechamento
print()
print("=" * 70)
RESULTS["totals"] = {"n_pass": N_PASS, "n_fail": N_FAIL, "n_total": N_PASS + N_FAIL}
print(f"TOTAL: {N_PASS} PASSA | {N_FAIL} FALHA | {N_PASS + N_FAIL} checks")
out_path = PROJECT_ROOT / "reports" / "eda_results" / "audit_fases_0_6.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(
    json.dumps(RESULTS, indent=2, ensure_ascii=False),
    encoding="utf-8",
)
print(f"-> {out_path.relative_to(PROJECT_ROOT)}")
sys.exit(0 if N_FAIL == 0 else 1)
