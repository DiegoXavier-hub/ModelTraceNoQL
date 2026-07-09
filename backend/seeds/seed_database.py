"""Generate a realistic, heavy-volume seed of the ModelTrace JSON document store.

Five projects are produced from copies of the user's local source projects:

    - Vale - Industrial Predictive Maintenance
    - CNPJ Closure Risk Radar
    - LLMs sob o microscopio
    - ML From Scratch - Algorithms Lab (10 algorithms = 10 models)
    - TCC Student Outcomes Full Replay

Total: ~95k predictions, with metrics snapshots, alerts, audit events,
intervention cases, model cards, model evaluations and cohorts. Output is a
single `backend/.data/modeltrace.json` ready to be loaded by JsonDocumentStore.

This script intentionally bypasses JsonDocumentStore.insert_one because that
saves the JSON on every insert. With ~95k predictions, that would be O(n^2)
on file size. Here we build everything in memory and write once.
"""

from __future__ import annotations

import hashlib
import json
import random
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.privacy import (  # noqa: E402  (sys.path must be set first)
    blind_index,
    encrypt_text,
    mask_email,
    protect_email,
)
from app.core.security import hash_password  # noqa: E402

OUTPUT_PATH = BACKEND_ROOT / ".data" / "modeltrace.json"
TCC_EXTRACTED_PATH = BACKEND_ROOT / "seeds" / "tcc_students_extracted.json"


# Features definition reused by the five TCC models. Matches NUM_FEATURES + CAT_FEATURES
# from `src/modelagem/config_modelagem.py` of the original TCC.
TCC_FEATURE_DEFS: list[dict[str, str]] = [
    {"name": "nota_media", "type": "numeric"},
    {"name": "nota_mediana", "type": "numeric"},
    {"name": "nota_desvio", "type": "numeric"},
    {"name": "nota_min", "type": "numeric"},
    {"name": "nota_max", "type": "numeric"},
    {"name": "qtd_aprovacoes", "type": "numeric"},
    {"name": "qtd_reprovacoes", "type": "numeric"},
    {"name": "qtd_dispensas", "type": "numeric"},
    {"name": "qtd_sem_resultado", "type": "numeric"},
    {"name": "qtd_reprov_nota", "type": "numeric"},
    {"name": "qtd_reprov_freq", "type": "numeric"},
    {"name": "taxa_aprovacao", "type": "numeric"},
    {"name": "qtd_disciplinas_total", "type": "numeric"},
    {"name": "media_disc_por_periodo", "type": "numeric"},
    {"name": "ch_acumulada", "type": "numeric"},
    {"name": "nota_p1", "type": "numeric"},
    {"name": "delta_nota", "type": "numeric"},
    {"name": "reprov_p1", "type": "numeric"},
    {"name": "disc_p1", "type": "numeric"},
    {"name": "pct_ch_concluida", "type": "numeric"},
    {"name": "num_semestre_ingresso", "type": "numeric"},
    {"name": "primeira_categoria", "type": "categorical"},
]

USER_ID = "user_diego_ops"
ORG_ID = "org_ufu_gi_ops"
DEMO_EMAIL = "diegohenrique.mail@gmail.com"
DEMO_PASSWORD = "D1eg0X@vi3rHUB"
DEMO_NAME = "Diego Henrique Xavier"

# Reproducible randomness for the entire seed
SEED = 20260514
random.seed(SEED)

NOW = datetime(2026, 5, 14, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def gen_id(prefix: str, *parts: str) -> str:
    seed = "::".join(parts) if parts else secrets.token_hex(6)
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def score_band(score: float) -> str:
    if score < 0.25:
        return "low"
    if score < 0.50:
        return "medium"
    if score < 0.75:
        return "high"
    return "critical"


def random_walk_scores(n: int, base_mean: float, base_std: float, drift: float = 0.0) -> list[float]:
    """Generate `n` scores with smooth drift over the timeline."""
    scores = []
    for i in range(n):
        progress = i / max(1, n - 1)
        mean = base_mean + drift * progress
        value = random.gauss(mean, base_std)
        scores.append(max(0.0, min(1.0, value)))
    return scores


def random_timestamps(start: datetime, end: datetime, n: int) -> list[datetime]:
    span = (end - start).total_seconds()
    return sorted(start + timedelta(seconds=random.uniform(0, span)) for _ in range(n))


def histogram_from_scores(scores: list[float]) -> list[dict]:
    buckets = [0] * 10
    for s in scores:
        idx = min(9, int(s * 10))
        buckets[idx] += 1
    return [
        {"bucket": f"{i / 10:.1f}-{(i + 1) / 10:.1f}", "count": buckets[i]}
        for i in range(10)
    ]


def protect_entity(value: str, type_: str) -> dict:
    hashed = blind_index(value, "entity") or ""
    suffix = hashed.removeprefix("hmac_sha256:")[:12]
    return {
        "id": f"entity_{suffix}" if suffix else "[protected]",
        "type": type_,
        "display_name": "[protected]",
        "id_hash": hashed,
        "id_encrypted": encrypt_text(value),
        "display_name_encrypted": encrypt_text(value),
        "display_name_masked": "[protected]",
    }


# ---------------------------------------------------------------------------
# Project definitions
# ---------------------------------------------------------------------------


PROJECTS: list[dict] = [
    {
        "slug": "vale-predictive-maintenance",
        "id": "proj_vale_predictive_maintenance",
        "name": "Vale - Industrial Predictive Maintenance",
        "description": "Modelos industriais para antecipar eventos DontGo em equipamentos de mina.",
        "domain": "industrial",
        "tags": ["maintenance", "industrial", "dontgo"],
        "entity_label": "ativos",
        "entity_type": "industrial_asset",
        "bias_sensitive_features": ["shift", "site"],
        "default_threshold": 0.50,
        "models": [
            {
                "name": "DontGo Event Risk",
                "slug": "dontgo-event-risk",
                "target_name": "event_risk",
                "labels": {"positive": "event_risk", "negative": "normal_operation"},
                "primary_metric": "average_precision",
                "default_threshold": 0.50,
                "features": [
                    {"name": "n_evt_1h", "type": "numeric"},
                    {"name": "n_crit_1h", "type": "numeric"},
                    {"name": "vibration_rms", "type": "numeric"},
                    {"name": "oil_temp_c", "type": "numeric"},
                    {"name": "shift", "type": "categorical"},
                    {"name": "site", "type": "categorical"},
                ],
                "versions": [
                    {"version": "h4", "algorithm": "RandomForest", "status": "deprecated"},
                    {"version": "h8", "algorithm": "LightGBM", "status": "deprecated"},
                    {"version": "h12", "algorithm": "LightGBM", "status": "production"},
                ],
                "production_version": "h12",
            }
        ],
        "n_predictions": 25_000,
        "feedback_rate": 0.85,
        "base_mean_score": 0.22,
        "base_std": 0.18,
        "drift": 0.04,
        "positive_rate": 0.18,
    },
    {
        "slug": "cnpj-closure-radar",
        "id": "proj_cnpj_closure_radar",
        "name": "CNPJ Closure Risk Radar",
        "description": "Probabilidade de encerramento de empresa brasileira em 12 meses, baseado em historico de CNPJs.",
        "domain": "economics",
        "tags": ["survival", "cnpj", "brasil"],
        "entity_label": "cnpjs",
        "entity_type": "company",
        "bias_sensitive_features": ["uf", "cnae_secao"],
        "default_threshold": 0.55,
        "models": [
            {
                "name": "Closure Risk LR",
                "slug": "closure-risk-lr",
                "target_name": "closes_12m",
                "labels": {"positive": "closes_12m", "negative": "remains_active"},
                "primary_metric": "auc_roc",
                "default_threshold": 0.55,
                "features": [
                    {"name": "idade_meses", "type": "numeric"},
                    {"name": "capital_social_log", "type": "numeric"},
                    {"name": "num_socios", "type": "numeric"},
                    {"name": "tem_filial", "type": "numeric"},
                    {"name": "cnae_secao", "type": "categorical"},
                    {"name": "uf", "type": "categorical"},
                    {"name": "regime_tributario", "type": "categorical"},
                ],
                "versions": [
                    {"version": "lr_v1", "algorithm": "LogisticRegression", "status": "deprecated"},
                    {"version": "lr_v2", "algorithm": "LogisticRegression", "status": "production"},
                ],
                "production_version": "lr_v2",
            },
            {
                "name": "Closure Risk XGB",
                "slug": "closure-risk-xgb",
                "target_name": "closes_12m",
                "labels": {"positive": "closes_12m", "negative": "remains_active"},
                "primary_metric": "auc_roc",
                "default_threshold": 0.55,
                "features": [
                    {"name": "idade_meses", "type": "numeric"},
                    {"name": "capital_social_log", "type": "numeric"},
                    {"name": "num_socios", "type": "numeric"},
                    {"name": "tem_filial", "type": "numeric"},
                    {"name": "cnae_secao", "type": "categorical"},
                    {"name": "uf", "type": "categorical"},
                    {"name": "regime_tributario", "type": "categorical"},
                ],
                "versions": [
                    {"version": "xgb_v1", "algorithm": "XGBoost", "status": "production"},
                ],
                "production_version": "xgb_v1",
            },
        ],
        "n_predictions": 18_000,
        "feedback_rate": 0.60,
        "base_mean_score": 0.28,
        "base_std": 0.22,
        "drift": 0.02,
        "positive_rate": 0.22,
    },
    {
        "slug": "llms-microscope",
        "id": "proj_llms_microscope",
        "name": "LLMs sob o Microscopio",
        "description": "Deteccao de alucinacoes em respostas de LLMs em tarefas de QA com e sem retrieval.",
        "domain": "research",
        "tags": ["llm", "evaluation", "hallucination"],
        "entity_label": "prompts",
        "entity_type": "prompt_evaluation",
        "bias_sensitive_features": ["model_family", "task_type"],
        "default_threshold": 0.50,
        "models": [
            {
                "name": "Hallucination Detector",
                "slug": "hallucination-detector",
                "target_name": "hallucinated",
                "labels": {"positive": "hallucinated", "negative": "grounded"},
                "primary_metric": "f1",
                "default_threshold": 0.50,
                "features": [
                    {"name": "prompt_length", "type": "numeric"},
                    {"name": "temperature", "type": "numeric"},
                    {"name": "retrieval_used", "type": "numeric"},
                    {"name": "model_family", "type": "categorical"},
                    {"name": "task_type", "type": "categorical"},
                    {"name": "language", "type": "categorical"},
                ],
                "versions": [
                    {"version": "v0_baseline", "algorithm": "LogisticRegression", "status": "deprecated"},
                    {"version": "v1_finetune", "algorithm": "BERT-finetune", "status": "production"},
                ],
                "production_version": "v1_finetune",
            }
        ],
        "n_predictions": 12_000,
        "feedback_rate": 0.70,
        "base_mean_score": 0.32,
        "base_std": 0.20,
        "drift": 0.03,
        "positive_rate": 0.28,
    },
    {
        "slug": "ml-from-scratch",
        "id": "proj_ml_from_scratch",
        "name": "ML From Scratch - Algorithms Lab",
        "description": "Laboratorio didatico com dez algoritmos de Machine Learning implementados do zero.",
        "domain": "education",
        "tags": ["education", "algorithms", "didactic"],
        "entity_label": "amostras",
        "entity_type": "demo_sample",
        "bias_sensitive_features": [],
        "default_threshold": 0.50,
        "models": [
            {
                "name": algo,
                "slug": algo.lower().replace(" ", "-"),
                "target_name": "y_true",
                "labels": {"positive": "positive", "negative": "negative"},
                "primary_metric": "accuracy",
                "default_threshold": 0.50,
                "features": [
                    {"name": "x1", "type": "numeric"},
                    {"name": "x2", "type": "numeric"},
                    {"name": "x3", "type": "numeric"},
                    {"name": "x4", "type": "numeric"},
                ],
                "versions": [{"version": "v1", "algorithm": algo, "status": "production"}],
                "production_version": "v1",
            }
            for algo in [
                "Decision Tree",
                "KMeans",
                "KNN",
                "Linear Regression",
                "Logistic Regression",
                "Naive Bayes",
                "PCA",
                "Perceptron",
                "Random Forest",
                "SVM",
            ]
        ],
        "n_predictions": 12_000,  # 1200 per model
        "feedback_rate": 0.50,
        "base_mean_score": 0.45,
        "base_std": 0.25,
        "drift": 0.0,
        "positive_rate": 0.45,
    },
    {
        "slug": "tcc-student-outcomes",
        "id": "proj_tcc_student_outcomes",
        "name": "TCC Student Outcomes - GI Real Cohort",
        "description": "Decisoes reais dos 5 modelos do TCC sobre a coorte completa de Gestao da Informacao (alunos vinculados + evadidos extraidos de D:/alunos-vinculo-GI.xlsx).",
        "domain": "education",
        "tags": ["education", "student-retention", "tcc", "real-cohort"],
        "entity_label": "alunos",
        "entity_type": "student",
        "bias_sensitive_features": ["tipo_ingresso", "cotista", "natural_uberlandia"],
        "default_threshold": 0.50,
        # Predictions are generated from real extracted students (see
        # extract_tcc_students.py). The five TCC models match nb07_modelos_optuna.py:
        # LR, RF, XGBoost, CatBoost, MLP. Each model has three versions matching
        # the TCC janelas (P1/P2/P4) for the period-based decision points.
        "predictions_source": "tcc_extracted",
        "models": [
            {
                "name": "TCC GI LR",
                "slug": "tcc-gi-lr",
                "target_name": "evasao",
                "labels": {"positive": "high_risk", "negative": "low_risk"},
                "primary_metric": "f2",
                "default_threshold": 0.50,
                "algorithm": "LogisticRegression",
                "features": TCC_FEATURE_DEFS,
                "versions": [
                    {"version": "p1", "algorithm": "LogisticRegression", "status": "deprecated"},
                    {"version": "p2", "algorithm": "LogisticRegression", "status": "deprecated"},
                    {"version": "p4", "algorithm": "LogisticRegression", "status": "production"},
                ],
                "production_version": "p4",
            },
            {
                "name": "TCC GI RF",
                "slug": "tcc-gi-rf",
                "target_name": "evasao",
                "labels": {"positive": "high_risk", "negative": "low_risk"},
                "primary_metric": "f2",
                "default_threshold": 0.50,
                "algorithm": "RandomForest",
                "features": TCC_FEATURE_DEFS,
                "versions": [
                    {"version": "p1", "algorithm": "RandomForest", "status": "deprecated"},
                    {"version": "p2", "algorithm": "RandomForest", "status": "deprecated"},
                    {"version": "p4", "algorithm": "RandomForest", "status": "production"},
                ],
                "production_version": "p4",
            },
            {
                "name": "TCC GI XGBoost",
                "slug": "tcc-gi-xgboost",
                "target_name": "evasao",
                "labels": {"positive": "high_risk", "negative": "low_risk"},
                "primary_metric": "f2",
                "default_threshold": 0.50,
                "algorithm": "XGBoost",
                "features": TCC_FEATURE_DEFS,
                "versions": [
                    {"version": "p1", "algorithm": "XGBoost", "status": "deprecated"},
                    {"version": "p2", "algorithm": "XGBoost", "status": "deprecated"},
                    {"version": "p4", "algorithm": "XGBoost", "status": "production"},
                ],
                "production_version": "p4",
            },
            {
                "name": "TCC GI CatBoost",
                "slug": "tcc-gi-catboost",
                "target_name": "evasao",
                "labels": {"positive": "high_risk", "negative": "low_risk"},
                "primary_metric": "f2",
                "default_threshold": 0.50,
                "algorithm": "CatBoost",
                "features": TCC_FEATURE_DEFS,
                "versions": [
                    {"version": "p1", "algorithm": "CatBoost", "status": "deprecated"},
                    {"version": "p2", "algorithm": "CatBoost", "status": "deprecated"},
                    {"version": "p4", "algorithm": "CatBoost", "status": "production"},
                ],
                "production_version": "p4",
            },
            {
                "name": "TCC GI MLP",
                "slug": "tcc-gi-mlp",
                "target_name": "evasao",
                "labels": {"positive": "high_risk", "negative": "low_risk"},
                "primary_metric": "f2",
                "default_threshold": 0.50,
                "algorithm": "MLP",
                "features": TCC_FEATURE_DEFS,
                "versions": [
                    {"version": "p1", "algorithm": "MLP", "status": "deprecated"},
                    {"version": "p2", "algorithm": "MLP", "status": "deprecated"},
                    {"version": "p4", "algorithm": "MLP", "status": "production"},
                ],
                "production_version": "p4",
            },
        ],
        "n_predictions": 0,  # populated from extracted students, not synthetic
        "feedback_rate": 1.0,
        "base_mean_score": 0.50,
        "base_std": 0.22,
        "drift": 0.0,
        "positive_rate": 0.62,
    },
]


# Feature value generators per project (keyed by feature name)
def generate_feature_value(feature: dict, project_slug: str) -> Any:
    name = feature["name"]
    if feature["type"] == "categorical":
        choices = {
            "shift": ["morning", "afternoon", "night"],
            "site": ["mine_a", "mine_b", "port_x"],
            "cnae_secao": ["A", "B", "C", "D", "G", "K", "M", "N"],
            "uf": ["SP", "RJ", "MG", "BA", "RS", "PR", "SC", "GO"],
            "regime_tributario": ["MEI", "SIMPLES", "LUCRO_PRESUMIDO", "LUCRO_REAL"],
            "model_family": ["GPT-4", "Claude", "Llama", "Mistral", "Gemini"],
            "task_type": ["qa_closed", "qa_open", "summarization", "reasoning"],
            "language": ["pt", "en", "es"],
            "tipo_ingresso": ["Processo Seletivo", "Vestibular", "Transferencia", "PROUNI"],
        }.get(name, ["A", "B", "C"])
        return random.choice(choices)
    else:
        ranges = {
            "n_evt_1h": (0, 120),
            "n_crit_1h": (0, 60),
            "vibration_rms": (1.0, 7.0),
            "oil_temp_c": (60.0, 110.0),
            "idade_meses": (3, 360),
            "capital_social_log": (6.0, 16.0),
            "num_socios": (1, 8),
            "tem_filial": (0, 1),
            "prompt_length": (10, 1500),
            "temperature": (0.0, 1.5),
            "retrieval_used": (0, 1),
            "x1": (-3.0, 3.0),
            "x2": (-3.0, 3.0),
            "x3": (-3.0, 3.0),
            "x4": (-3.0, 3.0),
            "nota_media": (30.0, 95.0),
            "qtd_reprovacoes": (0, 12),
            "qtd_aprovacoes": (5, 60),
            "taxa_aprovacao": (0.2, 1.0),
            "idade_ingresso": (16.0, 45.0),
            "delta_nota": (-30.0, 30.0),
            "cotista": (0, 1),
            "natural_uberlandia": (0, 1),
        }
        low, high = ranges.get(name, (0.0, 1.0))
        if isinstance(low, int) and isinstance(high, int):
            return random.randint(low, high)
        return round(random.uniform(low, high), 4)


# ---------------------------------------------------------------------------
# Build user + organization
# ---------------------------------------------------------------------------


def build_user_and_org() -> tuple[dict, dict]:
    email_protection = protect_email(DEMO_EMAIL)
    user = {
        "_id": USER_ID,
        "org_id": ORG_ID,
        "name": DEMO_NAME,
        "email": email_protection["email_masked"],
        "password_hash": hash_password(DEMO_PASSWORD),
        "role": "OWNER",
        "project_permissions": {},
        "preferences": {
            "theme": "dark",
            "default_project": "proj_vale_predictive_maintenance",
            "email_alerts": True,
            "locale": "pt-BR",
            "compact_mode": False,
        },
        "created_at": iso(NOW - timedelta(days=30)),
        "last_login_at": iso(NOW - timedelta(hours=4)),
        "status": "active",
        "email_masked": email_protection["email_masked"],
        "email_encrypted": email_protection["email_encrypted"],
        "email_hash": email_protection["email_hash"],
        "job_title": "Cientista de Dados / IT Onsite Technician",
        "department": "IT / Governanca de Modelos",
        "company": "UFU GI Decision Ops Lab",
        "phone": "37 9 9914-6270",
        "timezone": "America/Sao_Paulo",
        "bio": None,
        "updated_at": iso(NOW - timedelta(days=1)),
    }
    org = {
        "_id": ORG_ID,
        "name": "UFU GI Decision Ops Lab",
        "slug": "ufu-gi-decision-ops-lab",
        "plan": "enterprise-simulation",
        "owner_id": USER_ID,
        "settings": {
            "max_projects": 50,
            "max_predictions_per_day": 250_000,
            "retention_days": 1825,
            "enable_bias_analysis": True,
            "enable_webhooks": True,
            "enable_case_management": True,
            "enable_model_governance": True,
        },
        "created_at": iso(NOW - timedelta(days=30)),
        "status": "active",
    }
    return user, org


# ---------------------------------------------------------------------------
# Build per-project artifacts
# ---------------------------------------------------------------------------


def build_project_documents(project_def: dict) -> dict:
    """Returns a dict with all per-project documents."""
    project_id = project_def["id"]
    org_id = ORG_ID

    project_created_at = NOW - timedelta(days=random.randint(20, 40))

    project_doc = {
        "_id": project_id,
        "org_id": org_id,
        "name": project_def["name"],
        "slug": project_def["slug"],
        "description": project_def["description"],
        "problem_type": "binary_classification",
        "domain": project_def["domain"],
        "owner_id": USER_ID,
        "collaborators": [{"user_id": USER_ID, "role": "owner"}],
        "tags": project_def["tags"],
        "entity_label": project_def["entity_label"],
        "settings": {
            "default_threshold": project_def["default_threshold"],
            "positive_label": project_def["models"][0]["labels"]["positive"],
            "negative_label": project_def["models"][0]["labels"]["negative"],
            "retention_days": 1825,
            "enable_drift_monitoring": True,
            "drift_check_frequency": "weekly",
            "alert_email": "d***@example.com",
            "bias_sensitive_features": project_def["bias_sensitive_features"],
            "case_sla_days": {"critical": 2, "high": 7, "medium": 14},
            "alert_email_hash": blind_index("alerts@example.com", "email"),
            "data_contract_mode": "warn",
        },
        "stats": {
            "total_predictions": project_def["n_predictions"],  # patched after build for tcc-extracted
            "total_models": len(project_def["models"]),
            "active_alerts": 0,  # computed later
            "last_prediction_at": iso(NOW - timedelta(hours=random.randint(1, 12))),
        },
        "created_at": iso(project_created_at),
        "status": "active",
    }

    models: list[dict] = []
    versions: list[dict] = []
    model_cards: list[dict] = []
    model_evaluations: list[dict] = []
    api_keys: list[dict] = []
    cohorts: list[dict] = []
    datasets: list[dict] = []
    data_quality_reports: list[dict] = []
    audit_events: list[dict] = []
    alerts: list[dict] = []
    alert_rules: list[dict] = []
    intervention_cases: list[dict] = []
    metrics_snapshots: list[dict] = []
    drift_reports: list[dict] = []
    notifications: list[dict] = []
    jobs: list[dict] = []
    approvals: list[dict] = []
    saved_views: list[dict] = []
    exports: list[dict] = []
    predictions: list[dict] = []
    prediction_replays: list[dict] = []

    # ---- API key -----------------------------------------------------------
    api_key_id = gen_id("key", project_id, "pipeline")
    api_keys.append({
        "_id": api_key_id,
        "org_id": org_id,
        "project_id": project_id,
        "name": f"Pipeline {project_def['slug']}",
        "prefix": f"mt_live_{secrets.token_hex(4)}",
        "key_hash": hashlib.sha256(secrets.token_bytes(32)).hexdigest(),
        "scopes": ["predictions:write", "predictions:batch", "feedback:write"],
        "created_by": USER_ID,
        "created_at": iso(project_created_at),
        "last_used_at": iso(NOW - timedelta(hours=random.randint(1, 24))),
        "status": "active",
    })

    # ---- Models + versions -------------------------------------------------
    use_tcc_extracted = project_def.get("predictions_source") == "tcc_extracted"
    model_registry: list[dict] = []  # used by the TCC extracted-students branch
    n_predictions_per_model = max(1, max(1, project_def["n_predictions"]) // len(project_def["models"]))
    for model_def in project_def["models"]:
        model_id = gen_id("model", project_id, model_def["slug"])
        version_ids: dict[str, str] = {}
        for vdef in model_def["versions"]:
            vid = gen_id("version", model_id, vdef["version"])
            version_ids[vdef["version"]] = vid

        production_version = model_def["production_version"]
        production_version_id = version_ids[production_version]

        model_doc = {
            "_id": model_id,
            "project_id": project_id,
            "org_id": org_id,
            "name": model_def["name"],
            "slug": model_def["slug"],
            "description": f"{model_def['name']} treinado para {model_def['target_name']}.",
            "problem_type": "binary_classification",
            "target_name": model_def["target_name"],
            "labels": model_def["labels"],
            "default_threshold": model_def["default_threshold"],
            "primary_metric": model_def["primary_metric"],
            "expected_features": model_def["features"],
            "production_version_id": production_version_id,
            "created_by": USER_ID,
            "created_at": iso(project_created_at),
            "status": "active",
        }
        models.append(model_doc)

        for vdef in model_def["versions"]:
            vid = version_ids[vdef["version"]]
            base_ap = round(random.uniform(0.62, 0.88), 4)
            offline_metrics = {
                "accuracy": round(base_ap - 0.06 + random.uniform(-0.02, 0.04), 4),
                "precision": round(base_ap - 0.18 + random.uniform(-0.02, 0.04), 4),
                "recall": round(0.70 + random.uniform(-0.05, 0.15), 4),
                "f1": round(base_ap - 0.10 + random.uniform(-0.02, 0.04), 4),
                "f2": round(base_ap - 0.04 + random.uniform(-0.02, 0.04), 4),
                "auc_roc": round(base_ap + random.uniform(-0.05, 0.04), 4),
                "pr_auc": round(base_ap + random.uniform(-0.05, 0.04), 4),
                "brier": round(0.20 + random.uniform(-0.05, 0.06), 4),
            }
            versions.append({
                "_id": vid,
                "model_id": model_id,
                "project_id": project_id,
                "org_id": org_id,
                "version": vdef["version"],
                "algorithm": vdef["algorithm"],
                "status": vdef["status"],
                "created_by": USER_ID,
                "created_at": iso(project_created_at + timedelta(days=random.randint(0, 5))),
                "promoted_to_production_at": iso(project_created_at + timedelta(days=random.randint(1, 6)))
                    if vdef["status"] == "production" else None,
                "deprecated_at": iso(NOW - timedelta(days=random.randint(2, 15)))
                    if vdef["status"] == "deprecated" else None,
                "features": [f["name"] for f in model_def["features"]],
                "hyperparameters": {"learning_rate": 0.05, "n_estimators": 200, "max_depth": 8}
                    if "GBM" in vdef["algorithm"] or "Forest" in vdef["algorithm"]
                    else {"C": 1.0, "penalty": "l2"},
                "training_metadata": {
                    "source": f"backend/seeds/source_projects/{project_def['slug']}",
                    "window": vdef["version"],
                    "copied_artifacts_dir": f"backend/seeds/source_projects/{project_def['slug']}",
                },
                "offline_metrics": offline_metrics,
                "changelog": f"Versao {vdef['version']} ({vdef['algorithm']}) registrada pelo seed.",
                "notes": "Artefatos originais copiados sob backend/seeds/source_projects/. Originais nao foram modificados.",
            })

            # Model evaluation
            model_evaluations.append({
                "_id": gen_id("eval", vid),
                "project_id": project_id,
                "org_id": org_id,
                "model_id": model_id,
                "model_version_id": vid,
                "algorithm": vdef["algorithm"],
                "window": vdef["version"],
                "rank": 1 if vdef["status"] == "production" else 2,
                "offline_test_metrics": offline_metrics,
                "production_simulation": {
                    "prediction_count": int(n_predictions_per_model * random.uniform(0.18, 0.42)),
                    "feedback_count": int(n_predictions_per_model * project_def["feedback_rate"] * random.uniform(0.6, 1.0)),
                    "high_risk_rate": round(project_def["positive_rate"] * random.uniform(0.7, 1.1), 4),
                    "avg_score": round(project_def["base_mean_score"] * random.uniform(0.85, 1.15), 4),
                    "performance": {
                        "accuracy": round(offline_metrics["accuracy"] * 0.95, 4),
                        "precision": round(offline_metrics["precision"] * 0.92, 4),
                        "recall": round(offline_metrics["recall"] * 0.96, 4),
                        "f1": round(offline_metrics["f1"] * 0.93, 4),
                    },
                },
                "business_fit": {
                    "recall_first_policy": True,
                    "recommended_use": "operational_screening",
                },
                "created_at": iso(project_created_at + timedelta(days=2)),
            })

        # Model card
        model_cards.append({
            "_id": gen_id("card", model_id),
            "org_id": org_id,
            "project_id": project_id,
            "model_id": model_id,
            "title": f"Model Card - {model_def['name']}",
            "intended_use": f"Apoiar decisoes operacionais sobre {model_def['target_name']}.",
            "not_for_use": "Nao deve substituir decisao humana, decisoes regulatorias automaticas ou ranking de pessoas.",
            "training_context": f"Modelo {model_def['versions'][-1]['algorithm']} treinado em dados de {project_def['domain']}.",
            "known_limitations": [
                "Dataset de treino tem cobertura limitada para alguns segmentos.",
                "Necessita re-avaliacao mensal e feedback humano para acionamento operacional.",
            ],
            "governance": {
                "owner": "Decision Ops",
                "review_cycle": "mensal",
                "approval_required": True,
            },
            "created_at": iso(project_created_at + timedelta(days=3)),
        })

        if use_tcc_extracted:
            model_registry.append({
                "model_def": model_def,
                "model_id": model_id,
                "version_ids": version_ids,
            })
        else:
            # ---- Predictions for this model ----
            _build_predictions_for_model(
                project_def=project_def,
                model_def=model_def,
                model_id=model_id,
                production_version_id=production_version_id,
                version_ids=version_ids,
                n_predictions=n_predictions_per_model,
                project_created_at=project_created_at,
                predictions=predictions,
                intervention_cases=intervention_cases,
                metrics_snapshots=metrics_snapshots,
                drift_reports=drift_reports,
            )

    if use_tcc_extracted:
        _build_tcc_predictions_from_extracted(
            project_def=project_def,
            model_registry=model_registry,
            project_created_at=project_created_at,
            predictions=predictions,
            intervention_cases=intervention_cases,
            metrics_snapshots=metrics_snapshots,
            drift_reports=drift_reports,
        )

    # ---- Alert rules + alerts ---------------------------------------------
    for severity, rule_type, metric, threshold, operator in [
        ("high", "missing_features", "missing_rate", 0.05, "greater_than"),
        ("medium", "data_drift", "feature_attention_count", 5, "greater_than"),
        ("medium", "feedback_rate_low", "feedback_rate", 0.25, "less_than"),
    ]:
        rule_id = gen_id("rule", project_id, rule_type)
        alert_rules.append({
            "_id": rule_id,
            "project_id": project_id,
            "org_id": org_id,
            "model_id": models[0]["_id"] if models else None,
            "name": f"{rule_type} - {project_def['slug']}",
            "type": rule_type,
            "metric": metric,
            "operator": operator,
            "threshold": threshold,
            "severity": severity,
            "min_feedback_count": 1,
            "enabled": True,
            "created_at": iso(project_created_at + timedelta(days=1)),
        })

        # Generate one open alert per rule for realism
        observed = threshold * random.uniform(1.2, 2.0) if operator == "greater_than" else threshold * random.uniform(0.3, 0.85)
        alert_id = gen_id("alert", rule_id, "01")
        alerts.append({
            "_id": alert_id,
            "org_id": org_id,
            "project_id": project_id,
            "model_id": models[0]["_id"] if models else None,
            "rule_id": rule_id,
            "title": rule_type.replace("_", " ").capitalize(),
            "type": rule_type,
            "severity": severity,
            "status": "open",
            "message": f"{metric}={round(observed, 4)} / {operator} {threshold}.",
            "metric": metric,
            "observed_value": round(observed, 4),
            "threshold": threshold,
            "created_at": iso(NOW - timedelta(days=random.randint(1, 6))),
        })

        notifications.append({
            "_id": gen_id("notif", alert_id),
            "org_id": org_id,
            "user_id": USER_ID,
            "project_id": project_id,
            "type": "alert.created",
            "title": rule_type.replace("_", " ").capitalize(),
            "message": f"{metric} fora do limiar configurado.",
            "severity": severity,
            "link": {"view": "operations", "resource_id": alert_id},
            "metadata": {"alert_id": alert_id, "rule_id": rule_id},
            "read_at": None,
            "created_at": iso(NOW - timedelta(days=random.randint(1, 6))),
        })

    project_doc["stats"]["active_alerts"] = len(alerts)
    # Always reflect the actual number of predictions written, including the TCC
    # branch where n_predictions in the project_def is 0 (predictions come from
    # the extracted students JSON instead of synthetic generation).
    project_doc["stats"]["total_predictions"] = len(predictions)

    # ---- Cohorts ----------------------------------------------------------
    for cohort_label, cohort_type, size_ratio in [
        ("Operacional (acionavel)", "actionable", 0.25),
        ("Sem feedback", "no_feedback", 1.0 - project_def["feedback_rate"]),
        ("Critico", "critical", 0.10),
    ]:
        cohorts.append({
            "_id": gen_id("cohort", project_id, cohort_type),
            "org_id": org_id,
            "project_id": project_id,
            "name": cohort_label,
            "type": cohort_type,
            "filters": {"cohort_type": cohort_type},
            "size": int(project_def["n_predictions"] * size_ratio),
            "open_cases": int(len(intervention_cases) * 0.4),
            "created_at": iso(project_created_at + timedelta(days=5)),
        })

    # ---- Datasets + data quality -----------------------------------------
    dataset_id = gen_id("dataset", project_id, "primary")
    datasets.append({
        "_id": dataset_id,
        "org_id": org_id,
        "project_id": project_id,
        "name": f"{project_def['slug']}-primary",
        "type": "full_modeling_replay",
        "source_files": [{
            "path": f"backend/seeds/source_projects/{project_def['slug']}",
            "sha256": hashlib.sha256(project_def["slug"].encode()).hexdigest(),
            "copied_to": f"backend/seeds/source_projects/{project_def['slug']}",
        }],
        "row_count": project_def["n_predictions"],
        "created_at": iso(project_created_at + timedelta(days=1)),
    })

    data_quality_reports.append({
        "_id": gen_id("dq", project_id),
        "org_id": org_id,
        "project_id": project_id,
        "dataset_id": dataset_id,
        "created_at": iso(project_created_at + timedelta(days=2)),
        "source": {
            "row_count": project_def["n_predictions"],
            "column_count": len(project_def["models"][0]["features"]),
        },
        "missingness": {
            f["name"]: round(random.uniform(0.0, 0.15), 4)
            for f in project_def["models"][0]["features"]
        },
        "pii_fields_detected": [],
        "controls": [
            "IDs de entidades sao hash-encriptados antes de persistir.",
            "Arquivos originais dos projetos nao sao modificados; o seed trabalha com copias em backend/seeds/source_projects.",
        ],
        "warnings": [],
    })

    # ---- Approvals + audit events -----------------------------------------
    approval_id = gen_id("approval", project_id)
    approvals.append({
        "_id": approval_id,
        "org_id": org_id,
        "project_id": project_id,
        "title": f"Promocao operacional da versao {project_def['models'][0]['production_version']}",
        "status": "approved_for_simulation",
        "requested_by": USER_ID,
        "approved_by": USER_ID,
        "created_at": iso(project_created_at + timedelta(days=4)),
        "approved_at": iso(project_created_at + timedelta(days=4, hours=2)),
        "notes": "Versao com melhor desempenho na simulacao de producao.",
    })

    audit_events.append({
        "_id": gen_id("audit", project_id, "creation"),
        "org_id": org_id,
        "project_id": project_id,
        "actor": {"type": "user", "id": USER_ID, "email_masked": mask_email(DEMO_EMAIL)},
        "event_type": "project.created",
        "resource": {"type": "project", "id": project_id},
        "context": {"name": project_def["name"]},
        "created_at": iso(project_created_at),
    })
    audit_events.append({
        "_id": gen_id("audit", project_id, "seed_imported"),
        "org_id": org_id,
        "project_id": project_id,
        "actor": {"type": "system", "id": "modeltrace_seed", "email": None},
        "event_type": "dataset.full_replay_completed",
        "resource": {"type": "project", "id": project_id},
        "context": {
            "predictions": len(predictions),
            "source_mode": "seed-from-source-projects",
            "source_dir": f"backend/seeds/source_projects/{project_def['slug']}",
        },
        "created_at": iso(project_created_at + timedelta(hours=1)),
    })

    # ---- Jobs (completed examples) ----------------------------------------
    for job_type in ["alerts", "drift", "metrics"]:
        jobs.append({
            "_id": gen_id("job", project_id, job_type),
            "org_id": org_id,
            "project_id": project_id,
            "model_id": models[0]["_id"] if models else None,
            "type": job_type,
            "params": {},
            "status": "completed",
            "created_by": USER_ID,
            "created_at": iso(NOW - timedelta(days=random.randint(1, 6))),
            "started_at": iso(NOW - timedelta(days=random.randint(1, 6))),
            "finished_at": iso(NOW - timedelta(days=random.randint(0, 1))),
            "result": {"evaluated": random.randint(3, 12), "created": random.randint(0, 3)},
            "error": None,
        })

    # ---- Exports + saved views --------------------------------------------
    exports.append({
        "_id": gen_id("export", project_id),
        "org_id": org_id,
        "project_id": project_id,
        "type": "predictions",
        "filters": {"project_id": project_id},
        "format": "csv",
        "include_features": True,
        "include_explanations": True,
        "status": "ready",
        "file_path": f"backend/.data/exports/export_{project_id}.csv",
        "record_count": len(predictions),
        "created_by": USER_ID,
        "created_at": iso(NOW - timedelta(days=2)),
    })

    saved_views.append({
        "_id": gen_id("view", project_id, "high_risk_no_feedback"),
        "org_id": org_id,
        "user_id": USER_ID,
        "project_id": project_id,
        "view": "predictions",
        "name": "Alto risco sem feedback",
        "filters": {"score_min": 0.75, "feedback": "pending"},
        "columns": ["entity", "score", "label", "created_at"],
        "created_at": iso(project_created_at + timedelta(days=6)),
    })

    # ---- A few prediction replays -----------------------------------------
    for sample in random.sample(predictions, min(4, len(predictions))):
        prediction_replays.append({
            "_id": gen_id("replay", sample["_id"]),
            "prediction_id": sample["_id"],
            "project_id": project_id,
            "org_id": org_id,
            "model_id": sample["model_id"],
            "target_version": project_def["models"][0]["production_version"],
            "replay_score": round(max(0.0, min(1.0, sample["prediction"]["score"] + random.uniform(-0.2, 0.2))), 4),
            "replay_label": sample["prediction"]["label"],
            "created_at": iso(NOW - timedelta(days=random.randint(1, 5))),
            "created_by": USER_ID,
        })

    return {
        "project": project_doc,
        "models": models,
        "versions": versions,
        "model_cards": model_cards,
        "model_evaluations": model_evaluations,
        "api_keys": api_keys,
        "cohorts": cohorts,
        "datasets": datasets,
        "data_quality_reports": data_quality_reports,
        "audit_events": audit_events,
        "alerts": alerts,
        "alert_rules": alert_rules,
        "intervention_cases": intervention_cases,
        "metrics_snapshots": metrics_snapshots,
        "drift_reports": drift_reports,
        "notifications": notifications,
        "jobs": jobs,
        "approvals": approvals,
        "saved_views": saved_views,
        "exports": exports,
        "predictions": predictions,
        "prediction_replays": prediction_replays,
    }


def _build_predictions_for_model(
    *,
    project_def: dict,
    model_def: dict,
    model_id: str,
    production_version_id: str,
    version_ids: dict[str, str],
    n_predictions: int,
    project_created_at: datetime,
    predictions: list[dict],
    intervention_cases: list[dict],
    metrics_snapshots: list[dict],
    drift_reports: list[dict],
) -> None:
    project_id = project_def["id"]
    org_id = ORG_ID

    # Generate unique entity pool (encrypt once, reuse many times)
    n_entities = max(1, n_predictions // 5)
    entity_pool: list[dict] = []
    for i in range(n_entities):
        raw_id = f"{project_def['slug']}-{model_def['slug']}-{i:06d}"
        entity_pool.append(protect_entity(raw_id, project_def["entity_type"]))

    # Timeline: spread from project_created_at to NOW
    start_time = project_created_at + timedelta(hours=1)
    end_time = NOW - timedelta(hours=1)
    timestamps = random_timestamps(start_time, end_time, n_predictions)
    scores = random_walk_scores(
        n_predictions,
        base_mean=project_def["base_mean_score"],
        base_std=project_def["base_std"],
        drift=project_def["drift"],
    )

    threshold = model_def["default_threshold"]
    positive_label = model_def["labels"]["positive"]
    negative_label = model_def["labels"]["negative"]

    # Distribute predictions across versions:
    # 70% to production, 20% to next-most-recent, 10% to oldest
    version_order = [v["version"] for v in model_def["versions"]]
    if len(version_order) >= 3:
        version_weights = [0.10, 0.20, 0.70]
    elif len(version_order) == 2:
        version_weights = [0.30, 0.70]
    else:
        version_weights = [1.0]

    feedback_rate = project_def["feedback_rate"]
    positive_rate = project_def["positive_rate"]

    critical_indices = set(random.sample(range(n_predictions), k=min(30, max(2, n_predictions // 800))))

    for i, (created_at, score) in enumerate(zip(timestamps, scores)):
        version_name = random.choices(version_order, weights=version_weights, k=1)[0]
        version_id = version_ids[version_name]
        above = score >= threshold
        label = positive_label if above else negative_label

        entity = random.choice(entity_pool)
        features = {f["name"]: generate_feature_value(f, project_def["slug"]) for f in model_def["features"]}

        # Top 3 explanations: pick random features, scale impact by score
        top_features = random.sample(list(features.items()), min(3, len(features)))
        explanations = [
            {
                "feature": fname,
                "value": fvalue,
                "impact": round(0.05 + random.random() * 0.30 * score, 4),
                "direction": "risk_up" if above else "risk_down",
                "rank": rank,
            }
            for rank, (fname, fvalue) in enumerate(top_features, start=1)
        ]

        decision = {
            "action": "human_review" if above else "auto_pass",
            "status": "triggered" if above else "skipped",
            "reason": "score_above_threshold" if above else "below_threshold",
            "triggered_at": iso(created_at) if above else None,
        }

        # Feedback. Observed_value is correlated with score so the resulting
        # confusion matrix actually reflects "model that gets it right more often
        # than chance, but with realistic mistakes". A purely random observed_value
        # (independent of score) would make any threshold curve degenerate to
        # precision == positive_rate everywhere.
        feedback = {"available": False}
        observed_value = None
        if random.random() < feedback_rate:
            # Soft mapping: with informativeness=0.55, P(positive | high score)
            # is much higher than P(positive | low score), but neither saturates.
            # cohort_prior pulls toward the base positive_rate so the marginal
            # outcome rate stays calibrated to the project definition.
            informativeness = 0.55
            cohort_prior = positive_rate
            target_prob = (1 - informativeness) * cohort_prior + informativeness * score
            target_prob = max(0.03, min(0.97, target_prob))
            observed_value = 1 if random.random() < target_prob else 0
            if above and observed_value == 1:
                classification = "tp"
            elif above and observed_value == 0:
                classification = "fp"
            elif not above and observed_value == 1:
                classification = "fn"
            else:
                classification = "tn"
            feedback_received = created_at + timedelta(days=random.randint(1, 20))
            if feedback_received > NOW:
                feedback_received = NOW - timedelta(hours=random.randint(1, 24))
            feedback = {
                "available": True,
                "observed_value": observed_value,
                "observed_label": positive_label if observed_value == 1 else negative_label,
                "classification_result": classification,
                "received_at": iso(feedback_received),
                "feedback_date": iso(feedback_received),
                "source": "seed_simulation",
                "notes": None,
            }

        is_critical = i in critical_indices or (above and score > 0.85)
        prediction_id = gen_id("pred", project_id, model_id, str(i))
        request_id = f"seed_{project_def['slug']}_{model_def['slug']}_{i:06d}"

        prediction = {
            "_id": prediction_id,
            "project_id": project_id,
            "org_id": org_id,
            "model_id": model_id,
            "model_version_id": version_id,
            "model_version": version_name,
            "entity": entity,
            "created_at": iso(created_at),
            "features": features,
            "prediction": {
                "label": label,
                "score": round(score, 4),
                "threshold": threshold,
                "above_threshold": above,
                "score_band": score_band(score),
            },
            "explanations": explanations,
            "decision": decision,
            "feedback": feedback,
            "annotations": [],
            "flags": {
                "is_critical": is_critical,
                "reviewed_by": None,
                "reviewed_at": None,
            },
            "metadata": {
                "source_system": "seed_simulation",
                "environment": "production_simulation",
                "request_id": request_id,
                "window": version_name,
                "algorithm": next(v["algorithm"] for v in model_def["versions"] if v["version"] == version_name),
            },
        }
        predictions.append(prediction)

        # Intervention cases for a fraction of critical predictions with feedback
        if is_critical and feedback["available"] and len(intervention_cases) < 80 and random.random() < 0.6:
            case_id = gen_id("case", prediction_id)
            sla_due = created_at + timedelta(days=2)
            intervention_cases.append({
                "_id": case_id,
                "org_id": org_id,
                "project_id": project_id,
                "model_id": model_id,
                "prediction_id": prediction_id,
                "entity_id": entity["id"],
                "student_id": entity["id"],
                "status": random.choice(["open", "assigned", "in_progress", "resolved"]),
                "priority": "critical" if score > 0.9 else "high",
                "priority_rank": 1 if score > 0.9 else 2,
                "risk_score": round(score, 4),
                "risk_band": score_band(score),
                "window_used": version_name,
                "recommended_action": "operational_review",
                "owner_team": "Decision Ops",
                "sla_due_at": iso(sla_due),
                "outcome_status": "known" if feedback["available"] else "unknown",
                "drivers": explanations[:2],
                "timeline": [{
                    "status": "created",
                    "note": "Caso aberto pelo seed para revisao operacional.",
                    "actor": {"id": "system", "email": None},
                    "created_at": iso(created_at),
                }],
                "created_at": iso(created_at),
            })

    # Bucketed metrics_snapshots (weekly aggregation, last 8 weeks)
    granularity_weeks = 8
    for w in range(granularity_weeks):
        period_end = NOW - timedelta(days=w * 7)
        period_start = period_end - timedelta(days=7)
        window_preds = [
            p for p in predictions
            if p["model_id"] == model_id
            and period_start <= datetime.strptime(p["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) < period_end
        ]
        if not window_preds:
            continue
        total = len(window_preds)
        with_fb = sum(1 for p in window_preds if p["feedback"]["available"])
        positives = sum(1 for p in window_preds if p["prediction"]["above_threshold"])
        tp = sum(1 for p in window_preds if p["feedback"].get("classification_result") == "tp")
        fp = sum(1 for p in window_preds if p["feedback"].get("classification_result") == "fp")
        tn = sum(1 for p in window_preds if p["feedback"].get("classification_result") == "tn")
        fn = sum(1 for p in window_preds if p["feedback"].get("classification_result") == "fn")
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) else 0.0
        window_scores = [p["prediction"]["score"] for p in window_preds]
        metrics_snapshots.append({
            "_id": gen_id("metric", model_id, str(w)),
            "project_id": project_id,
            "org_id": org_id,
            "model_id": model_id,
            "model_version": project_def["models"][0]["production_version"],
            "period": {
                "granularity": "week",
                "start": iso(period_start),
                "end": iso(period_end),
                "label": period_start.strftime("%Y-W%V"),
            },
            "counts": {
                "total": total,
                "positive": positives,
                "negative": total - positives,
                "with_feedback": with_fb,
                "without_feedback": total - with_fb,
            },
            "performance": {
                "accuracy": round(accuracy, 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
            },
            "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
            "score_distribution": {
                "mean": round(sum(window_scores) / len(window_scores), 4),
                "std": round((sum((s - sum(window_scores) / len(window_scores)) ** 2 for s in window_scores) / len(window_scores)) ** 0.5, 4),
                "histogram": histogram_from_scores(window_scores),
            },
            "computed_at": iso(NOW),
        })

    # Drift report (one example)
    drift_reports.append({
        "_id": gen_id("drift", model_id),
        "project_id": project_id,
        "org_id": org_id,
        "model_id": model_id,
        "model_version": project_def["models"][0]["production_version"],
        "reference_period": {
            "start": iso(start_time),
            "end": iso(start_time + (end_time - start_time) / 2),
            "count": n_predictions // 2,
        },
        "current_period": {
            "start": iso(start_time + (end_time - start_time) / 2),
            "end": iso(end_time),
            "count": n_predictions // 2,
        },
        "prediction_drift": {
            "psi": round(0.20 + random.random() * 1.4, 4),
            "mean_score_ref": round(project_def["base_mean_score"], 4),
            "mean_score_cur": round(project_def["base_mean_score"] + project_def["drift"], 4),
            "status": "drift_detected" if abs(project_def["drift"]) > 0.02 else "stable",
        },
        "data_drift": {
            "features": [
                {
                    "name": f["name"],
                    "type": "continuous" if f["type"] == "numeric" else "categorical",
                    "delta": round(random.uniform(-0.1, 0.1), 4),
                    "status": random.choice(["stable", "attention"]),
                }
                for f in model_def["features"]
            ],
        },
        "created_at": iso(NOW - timedelta(days=random.randint(1, 5))),
    })


# ---------------------------------------------------------------------------
# TCC: real-student predictions built from the adapted extractor output.
# ---------------------------------------------------------------------------


def _sigmoid(x: float) -> float:
    if x >= 0:
        z = 2.718281828 ** -x
        return 1.0 / (1.0 + z)
    z = 2.718281828 ** x
    return z / (1.0 + z)


def _tcc_eligible_janelas(max_periodo: int | None) -> list[str]:
    """A student is scored at every janela up to the deepest one they reached."""
    if not max_periodo or max_periodo < 1:
        return ["p1"]
    janelas = ["p1"]
    if max_periodo >= 2:
        janelas.append("p2")
    if max_periodo >= 4:
        janelas.append("p4")
    return janelas


def _tcc_base_risk(student: dict, janela: str) -> float:
    """Heuristic risk derived from real features.

    Weights are intentionally soft so the score is *correlated* with the outcome
    but not deterministic — a real LR/RF/etc. has imperfect fit. The cohort
    intercept centers the average score near the population evasion rate (~50%)
    instead of biasing it high.
    """
    nota_media = float(student.get("nota_media") or 50.0)
    qtd_reprov = float(student.get("qtd_reprovacoes") or 0)
    qtd_reprov_freq = float(student.get("qtd_reprov_freq") or 0)
    qtd_aprov = float(student.get("qtd_aprovacoes") or 0)
    taxa_aprov = float(student.get("taxa_aprovacao") or 0.5)
    pct_ch = float(student.get("pct_ch_concluida") or 0.0)
    delta_nota = student.get("delta_nota")
    reprov_p1 = float(student.get("reprov_p1") or 0)

    score = (
        - 0.022 * (nota_media - 60.0)
        + 0.18 * qtd_reprov_freq
        + 0.09 * qtd_reprov
        - 0.02 * qtd_aprov
        - 0.95 * taxa_aprov
        - 0.85 * pct_ch
        + (0.0 if delta_nota is None else -0.012 * float(delta_nota))
        + 0.22 * reprov_p1
        + 0.20  # centered intercept: average score lands near 0.5 sigmoid
    )

    # Janela weights: p4 has more history => slightly sharper decisions; p1 is
    # the least informative.
    janela_weight = {"p1": 0.75, "p2": 0.90, "p4": 1.10}.get(janela, 1.0)
    score *= janela_weight

    # Cap so sigmoid stays informative.
    return max(-6.0, min(6.0, score))


# Model-specific decision biases (mimics that different algorithms disagree on
# borderline cases). Production tcc-gi-lr stays at 0 as the reference.
TCC_MODEL_BIAS = {
    "tcc-gi-lr": 0.00,
    "tcc-gi-rf": -0.18,
    "tcc-gi-xgboost": 0.22,
    "tcc-gi-catboost": -0.05,
    "tcc-gi-mlp": 0.34,
}

# How noisy each model is. LR is the most stable (smaller variance), tree
# ensembles slightly noisier, MLP the noisiest. Multiplies the gaussian-like
# logit noise so models disagree on borderline cases — which is what produces
# realistic precision/recall curves with overlap and non-monotonic regions.
TCC_MODEL_NOISE_SCALE = {
    "tcc-gi-lr": 1.20,
    "tcc-gi-rf": 1.35,
    "tcc-gi-xgboost": 1.45,
    "tcc-gi-catboost": 1.30,
    "tcc-gi-mlp": 1.65,
}

# Per-version drift on top of the model bias.
TCC_VERSION_DRIFT = {"p1": -0.30, "p2": -0.10, "p4": 0.05}


def _hash_uniform(*parts: str) -> float:
    """Deterministic uniform [0, 1) sample from a string tuple."""
    digest = hashlib.sha1("::".join(parts).encode("utf-8")).hexdigest()
    return int(digest[:8], 16) / 0xFFFFFFFF


def _hash_gaussian(*parts: str) -> float:
    """Deterministic, roughly Gaussian sample (CLT sum of 4 uniforms, mean 0)."""
    total = 0.0
    for i in range(4):
        total += _hash_uniform(*parts, str(i))
    return total - 2.0  # range ~[-2, +2], std ~0.58


def _tcc_load_extracted() -> list[dict]:
    if not TCC_EXTRACTED_PATH.exists():
        raise SystemExit(
            f"Arquivo nao encontrado: {TCC_EXTRACTED_PATH}\n"
            "Rode antes: python backend/seeds/extract_tcc_students.py"
        )
    payload = json.loads(TCC_EXTRACTED_PATH.read_text(encoding="utf-8"))
    return payload["students"]


def _tcc_feature_payload(student: dict) -> dict:
    feature_keys = [f["name"] for f in TCC_FEATURE_DEFS]
    out: dict = {}
    for key in feature_keys:
        value = student.get(key)
        if value is None:
            out[key] = None
        elif isinstance(value, float):
            out[key] = round(value, 4)
        else:
            out[key] = value
    return out


def _tcc_explanations(student: dict, score: float) -> list[dict]:
    candidates = [
        ("qtd_reprov_freq", student.get("qtd_reprov_freq"), 0.32, "increases_risk"),
        ("nota_media", student.get("nota_media"), -0.045, "decreases_risk_when_high"),
        ("taxa_aprovacao", student.get("taxa_aprovacao"), -1.6, "decreases_risk_when_high"),
        ("qtd_reprovacoes", student.get("qtd_reprovacoes"), 0.18, "increases_risk"),
        ("pct_ch_concluida", student.get("pct_ch_concluida"), -1.4, "decreases_risk_when_high"),
    ]
    ranked = []
    for feature, value, weight, direction in candidates:
        if value is None:
            continue
        try:
            impact = abs(weight * float(value))
        except (TypeError, ValueError):
            continue
        ranked.append({
            "feature": feature,
            "value": value,
            "impact": round(impact, 4),
            "direction": direction,
        })
    ranked.sort(key=lambda item: item["impact"], reverse=True)
    out = []
    for rank, item in enumerate(ranked[:3], start=1):
        item["rank"] = rank
        out.append(item)
    return out


def _build_tcc_predictions_from_extracted(
    *,
    project_def: dict,
    model_registry: list[dict],
    project_created_at: datetime,
    predictions: list[dict],
    intervention_cases: list[dict],
    metrics_snapshots: list[dict],
    drift_reports: list[dict],
) -> None:
    students = _tcc_load_extracted()
    project_id = project_def["id"]
    org_id = ORG_ID

    print(f"[seed]   tcc: scoring {len(students)} real students with {len(model_registry)} models", flush=True)

    # Per-model accumulators for metrics/drift/etc.
    per_model_predictions: dict[str, list[dict]] = {entry["model_id"]: [] for entry in model_registry}

    # Critical intervention budget per model (cap to avoid explosion).
    intervention_budget = 16

    for entry in model_registry:
        model_def = entry["model_def"]
        model_id = entry["model_id"]
        version_ids = entry["version_ids"]
        slug = model_def["slug"]
        model_bias = TCC_MODEL_BIAS.get(slug, 0.0)
        threshold = model_def["default_threshold"]
        positive_label = model_def["labels"]["positive"]
        negative_label = model_def["labels"]["negative"]
        per_model_interventions = 0

        for idx, student in enumerate(students):
            student_id = student["id_aluno"]
            entity = protect_entity(f"tcc-gi-{student_id}", "student")
            max_periodo = int(student.get("max_periodo") or 1)
            janelas = _tcc_eligible_janelas(max_periodo)
            base = _tcc_base_risk(student, janelas[-1])

            for janela in janelas:
                version_id = version_ids[janela]
                version_drift = TCC_VERSION_DRIFT.get(janela, 0.0)
                # Deterministic per (student, model, janela) noise from hashes so the
                # scores are reproducible across re-seeds. We use a *gaussian-shaped*
                # noise (CLT sum of 4 uniforms) scaled per-model so different models
                # disagree on borderline cases — that's what creates realistic
                # precision-recall curves with overlap between the two classes.
                noise_scale = TCC_MODEL_NOISE_SCALE.get(slug, 1.3)
                noise = _hash_gaussian(student_id, slug, janela) * noise_scale

                # Keep noise_seed available for the timeline offset below.
                noise_seed = int(hashlib.sha1(
                    f"{student_id}::{slug}::{janela}".encode("utf-8")
                ).hexdigest()[:8], 16)

                logit = base + model_bias + version_drift + noise
                score = _sigmoid(logit)
                above = score >= threshold
                label = positive_label if above else negative_label

                explanations = _tcc_explanations(student, score)

                # Timeline: spread the prediction creation across the project's lifetime
                # using a deterministic offset based on the student index.
                offset_hours = ((idx * 13 + noise_seed % 977) % 600)
                created_at = project_created_at + timedelta(hours=offset_hours + 4)
                if created_at > NOW - timedelta(hours=1):
                    created_at = NOW - timedelta(hours=1, minutes=offset_hours % 60)

                # Feedback observed-outcome assignment.
                # - Evadidos (y=1): always have observed_value=1, regardless of janela.
                # - Vinculados (y=None): only get observed_value=0 once they have lived
                #   long enough past the janela to confirm they did not evade in that
                #   horizon. This is right-censoring in the survival sense and gives
                #   the threshold curve a real precision-recall tradeoff.
                # Janela -> minimum max_periodo required to count Vinculado as TN:
                # p1 prediction needs >=3 sequential periods observed, p2 needs >=4,
                # p4 needs >=6. Below the floor, outcome stays "unknown".
                survival_floor = {"p1": 3, "p2": 4, "p4": 6}.get(janela, 6)
                feedback: dict = {"available": False}
                observed_value: int | None = None
                if student.get("y") == 1:
                    observed_value = 1
                    classification = "tp" if above else "fn"
                    feedback_at = created_at + timedelta(days=14)
                    if feedback_at > NOW:
                        feedback_at = NOW - timedelta(hours=2)
                    feedback = {
                        "available": True,
                        "observed_value": 1,
                        "observed_label": positive_label,
                        "classification_result": classification,
                        "received_at": iso(feedback_at),
                        "feedback_date": iso(feedback_at),
                        "source": "registro_academico_ufu",
                        "notes": f"Desfecho observado: {student.get('situacao_aluno')}.",
                    }
                elif max_periodo >= survival_floor:
                    # Vinculado who lived past the janela horizon -> true negative.
                    observed_value = 0
                    classification = "fp" if above else "tn"
                    feedback_at = created_at + timedelta(days=int(survival_floor) * 30)
                    if feedback_at > NOW:
                        feedback_at = NOW - timedelta(hours=2)
                    feedback = {
                        "available": True,
                        "observed_value": 0,
                        "observed_label": negative_label,
                        "classification_result": classification,
                        "received_at": iso(feedback_at),
                        "feedback_date": iso(feedback_at),
                        "source": "registro_academico_ufu",
                        "notes": (
                            f"Aluno com vinculo ativo confirmado em max_periodo={max_periodo} "
                            f">= floor({janela})={survival_floor}: nao evadiu nessa janela."
                        ),
                    }

                is_critical = above and score > 0.80
                prediction_id = gen_id("pred", project_id, model_id, janela, student_id)
                request_id = f"tcc_gi_{slug}_{janela}_{student_id}"

                prediction = {
                    "_id": prediction_id,
                    "project_id": project_id,
                    "org_id": org_id,
                    "model_id": model_id,
                    "model_version_id": version_id,
                    "model_version": janela,
                    "entity": entity,
                    "created_at": iso(created_at),
                    "features": _tcc_feature_payload(student),
                    "prediction": {
                        "label": label,
                        "score": round(score, 4),
                        "threshold": threshold,
                        "above_threshold": above,
                        "score_band": score_band(score),
                    },
                    "explanations": explanations,
                    "decision": {
                        "action": "human_review" if above else "auto_pass",
                        "status": "triggered" if above else "skipped",
                        "reason": "score_above_threshold" if above else "below_threshold",
                        "triggered_at": iso(created_at) if above else None,
                    },
                    "feedback": feedback,
                    "annotations": [],
                    "flags": {
                        "is_critical": is_critical,
                        "reviewed_by": None,
                        "reviewed_at": None,
                    },
                    "metadata": {
                        "source_system": "tcc_gi_real_cohort_seed",
                        "environment": "production_simulation",
                        "request_id": request_id,
                        "window": janela,
                        "algorithm": model_def["algorithm"],
                        "student_status": student.get("situacao_aluno"),
                        "outcome_status": "known" if observed_value is not None else "unknown",
                        "extraction_source": str(TCC_EXTRACTED_PATH.name),
                    },
                }
                predictions.append(prediction)
                per_model_predictions[model_id].append(prediction)

                # Open a few intervention cases per model for realism.
                if (
                    is_critical
                    and feedback["available"]
                    and per_model_interventions < intervention_budget
                    and janela == janelas[-1]
                ):
                    per_model_interventions += 1
                    case_id = gen_id("case", prediction_id)
                    sla_due = created_at + timedelta(days=2)
                    intervention_cases.append({
                        "_id": case_id,
                        "org_id": org_id,
                        "project_id": project_id,
                        "model_id": model_id,
                        "prediction_id": prediction_id,
                        "entity_id": entity["id"],
                        "student_id": entity["id"],
                        "status": random.choice(["open", "in_progress", "resolved"]),
                        "priority": "critical" if score > 0.9 else "high",
                        "priority_rank": 1 if score > 0.9 else 2,
                        "risk_score": round(score, 4),
                        "risk_band": score_band(score),
                        "window_used": janela,
                        "recommended_action": "retencao_academica",
                        "owner_team": "Coordenacao GI",
                        "sla_due_at": iso(sla_due),
                        "outcome_status": "known",
                        "drivers": explanations[:2],
                        "timeline": [{
                            "status": "created",
                            "note": "Caso aberto a partir do alerta operacional do modelo.",
                            "actor": {"id": "system", "email": None},
                            "created_at": iso(created_at),
                        }],
                        "created_at": iso(created_at),
                    })

    # Build per-model metrics_snapshots and drift_reports based on the real predictions.
    for entry in model_registry:
        model_id = entry["model_id"]
        model_preds = per_model_predictions[model_id]
        if not model_preds:
            continue

        # Weekly snapshots over the last 8 weeks.
        for w in range(8):
            period_end = NOW - timedelta(days=w * 7)
            period_start = period_end - timedelta(days=7)
            window_preds = [
                p for p in model_preds
                if period_start
                <= datetime.strptime(p["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                < period_end
            ]
            if not window_preds:
                continue
            total = len(window_preds)
            with_fb = sum(1 for p in window_preds if p["feedback"]["available"])
            positives = sum(1 for p in window_preds if p["prediction"]["above_threshold"])
            tp = sum(1 for p in window_preds if p["feedback"].get("classification_result") == "tp")
            fp = sum(1 for p in window_preds if p["feedback"].get("classification_result") == "fp")
            tn = sum(1 for p in window_preds if p["feedback"].get("classification_result") == "tn")
            fn = sum(1 for p in window_preds if p["feedback"].get("classification_result") == "fn")
            precision = tp / (tp + fp) if (tp + fp) else 0.0
            recall = tp / (tp + fn) if (tp + fn) else 0.0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
            accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) else 0.0
            window_scores = [p["prediction"]["score"] for p in window_preds]
            mean_score = sum(window_scores) / len(window_scores)
            metrics_snapshots.append({
                "_id": gen_id("metric", model_id, str(w)),
                "project_id": project_def["id"],
                "org_id": ORG_ID,
                "model_id": model_id,
                "model_version": "p4",
                "period": {
                    "granularity": "week",
                    "start": iso(period_start),
                    "end": iso(period_end),
                    "label": period_start.strftime("%Y-W%V"),
                },
                "counts": {
                    "total": total,
                    "positive": positives,
                    "negative": total - positives,
                    "with_feedback": with_fb,
                    "without_feedback": total - with_fb,
                },
                "performance": {
                    "accuracy": round(accuracy, 4),
                    "precision": round(precision, 4),
                    "recall": round(recall, 4),
                    "f1": round(f1, 4),
                },
                "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
                "score_distribution": {
                    "mean": round(mean_score, 4),
                    "std": round(
                        (
                            sum((s - mean_score) ** 2 for s in window_scores) / len(window_scores)
                        ) ** 0.5,
                        4,
                    ),
                    "histogram": histogram_from_scores(window_scores),
                },
                "computed_at": iso(NOW),
            })

        # Drift report (one per model) based on real feature stats.
        first_half = model_preds[: len(model_preds) // 2]
        second_half = model_preds[len(model_preds) // 2 :]
        mean_score_ref = sum(p["prediction"]["score"] for p in first_half) / max(1, len(first_half))
        mean_score_cur = sum(p["prediction"]["score"] for p in second_half) / max(1, len(second_half))
        drift_reports.append({
            "_id": gen_id("drift", model_id),
            "project_id": project_def["id"],
            "org_id": ORG_ID,
            "model_id": model_id,
            "model_version": "p4",
            "reference_period": {
                "start": first_half[0]["created_at"] if first_half else iso(NOW - timedelta(days=14)),
                "end": first_half[-1]["created_at"] if first_half else iso(NOW - timedelta(days=7)),
                "count": len(first_half),
            },
            "current_period": {
                "start": second_half[0]["created_at"] if second_half else iso(NOW - timedelta(days=7)),
                "end": second_half[-1]["created_at"] if second_half else iso(NOW),
                "count": len(second_half),
            },
            "prediction_drift": {
                "psi": round(abs(mean_score_cur - mean_score_ref) * 4.0, 4),
                "mean_score_ref": round(mean_score_ref, 4),
                "mean_score_cur": round(mean_score_cur, 4),
                "status": "drift_detected" if abs(mean_score_cur - mean_score_ref) > 0.05 else "stable",
            },
            "data_drift": {"features": []},
            "created_at": iso(NOW - timedelta(days=2)),
        })


# ---------------------------------------------------------------------------
# Email tokens (verify email used in registration flow)
# ---------------------------------------------------------------------------


def build_email_tokens() -> list[dict]:
    return [{
        "_id": gen_id("emailtoken", "diego", "verify"),
        "user_id": USER_ID,
        "purpose": "verify_email",
        "token_hash": hashlib.sha256(secrets.token_bytes(16)).hexdigest(),
        "created_at": iso(NOW - timedelta(days=30)),
        "consumed_at": iso(NOW - timedelta(days=29, hours=23)),
        "expires_at": iso(NOW - timedelta(days=29)),
    }]


# ---------------------------------------------------------------------------
# Top-level orchestration
# ---------------------------------------------------------------------------


def build_all() -> dict[str, list[dict]]:
    user, org = build_user_and_org()

    data: dict[str, list[dict]] = {
        "users": [user],
        "organizations": [org],
        "projects": [],
        "models": [],
        "model_versions": [],
        "api_keys": [],
        "email_tokens": build_email_tokens(),
        "notifications": [],
        "jobs": [],
        "saved_views": [],
        "entity_notes": [],
        "prediction_scenarios": [],
        "predictions": [],
        "prediction_annotations": [],
        "prediction_replays": [],
        "metrics_snapshots": [],
        "dashboard_cache": [],
        "diagnostic_cache": [],
        "drift_reports": [],
        "alert_rules": [],
        "alerts": [],
        "webhooks": [],
        "webhook_deliveries": [],
        "datasets": [],
        "cohorts": [],
        "model_evaluations": [],
        "model_cards": [],
        "intervention_cases": [],
        "incidents": [],
        "data_quality_reports": [],
        "approvals": [],
        "audit_events": [],
        "exports": [],
    }

    for project_def in PROJECTS:
        print(f"[seed] Building project {project_def['slug']} "
              f"({project_def['n_predictions']:,} predictions)...", flush=True)
        bundle = build_project_documents(project_def)
        data["projects"].append(bundle["project"])
        data["models"].extend(bundle["models"])
        data["model_versions"].extend(bundle["versions"])
        data["model_cards"].extend(bundle["model_cards"])
        data["model_evaluations"].extend(bundle["model_evaluations"])
        data["api_keys"].extend(bundle["api_keys"])
        data["cohorts"].extend(bundle["cohorts"])
        data["datasets"].extend(bundle["datasets"])
        data["data_quality_reports"].extend(bundle["data_quality_reports"])
        data["audit_events"].extend(bundle["audit_events"])
        data["alerts"].extend(bundle["alerts"])
        data["alert_rules"].extend(bundle["alert_rules"])
        data["intervention_cases"].extend(bundle["intervention_cases"])
        data["metrics_snapshots"].extend(bundle["metrics_snapshots"])
        data["drift_reports"].extend(bundle["drift_reports"])
        data["notifications"].extend(bundle["notifications"])
        data["jobs"].extend(bundle["jobs"])
        data["approvals"].extend(bundle["approvals"])
        data["saved_views"].extend(bundle["saved_views"])
        data["exports"].extend(bundle["exports"])
        data["predictions"].extend(bundle["predictions"])
        data["prediction_replays"].extend(bundle["prediction_replays"])

    return data


def main() -> None:
    print("[seed] Starting heavy seed of ModelTrace document store...")
    data = build_all()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    print("[seed] Serializing JSON to disk...")
    OUTPUT_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)
    print(f"[seed] Wrote {OUTPUT_PATH} ({size_mb:.1f} MB)")
    for name, items in data.items():
        if items:
            print(f"  - {name}: {len(items):,}")


if __name__ == "__main__":
    main()
