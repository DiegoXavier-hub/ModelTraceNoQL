"""Regeração das predições do JUN holdout (Fase 5 / PRE-1).

Para cada horizonte H ∈ {1, 2, 4, 6, 8, 12} esta camada:

1. Lê ``data/processed/features_2025-06.parquet``.
2. Filtra ``OEM == 'Caterpillar'`` (D027) e aplica ``apply_censura_filter`` (D038).
3. Constrói matriz de features via ``build_feature_matrix`` (descarta D030 +
   identificadores + flags de censura, garantindo as mesmas colunas usadas em 4B).
4. Carrega o booster ``outputs/models/lgbm_h{H}_holdout_jun.txt`` (treino jan-mai).
5. Carrega o calibrador ``outputs/models/lgbm_calibrated_h{H}.joblib`` e aplica o
   método registrado em D037 (``chosen_method`` no ``.joblib``).
6. Persiste ``outputs/predictions/preds_jun_h{H}.parquet`` com colunas:
   ``[TAG, t_window, y_true, score_raw, score_cal, target_lead_time_min, mes_str]``.

Princípio operativo
-------------------
- ``score_raw`` é a saída direta do booster (clipada em [1e-6, 1-1e-6]).
- ``score_cal`` aplica EXATAMENTE o calibrador escolhido na Fase 4F. Não
  recalibra, não escolhe método novo.
- Idempotente: pode ser re-executado sem efeitos colaterais.
- Validação opcional contra ``fase4b_pa1_lightgbm.json`` confirma que AUC-PR
  recomputado bate com o número canônico (D012 → D013 dependem disso).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd

from src.eval.metrics import metric_pack
from src.eval.splits import apply_censura_filter
from src.models.calibration import apply_isotonic, apply_platt
from src.models.pa1_lightgbm import build_feature_matrix
from src.utils.paths import MODELS_DIR, PREDICTIONS_DIR, PROJECT_ROOT

PROCESSED_DIR: Path = PROJECT_ROOT / "data" / "processed"

CARRY_COLS: tuple[str, ...] = (
    "TAG",
    "t_window",
    "Tag_Frota",
    "mes_str",
    "target_lead_time_min",
    "bucket_hora",
    "turno",
    "hora",
    "dow",
)

EPS_CLIP: float = 1e-6


@dataclass(frozen=True)
class PredictionArtifacts:
    """Artefatos gerados por ``predict_holdout_jun``."""

    horizon_h: int
    parquet_path: Path
    n_rows: int
    n_pos: int
    chosen_method: str
    auc_pr_raw: float
    brier_cal: float


def _calibrate(scores: np.ndarray, calib: dict) -> tuple[np.ndarray, str]:
    """Aplica o método escolhido em D037 (``chosen_method`` no joblib)."""
    method = calib["chosen_method"]
    if method == "isotonic":
        cal = apply_isotonic(calib["isotonic"], scores)
    elif method == "platt":
        cal = apply_platt(calib["platt"], scores)
    else:
        raise ValueError(f"chosen_method inesperado: {method!r}")
    return np.clip(np.asarray(cal, dtype=float), 0.0, 1.0), method


def predict_holdout_jun(
    horizon_h: int,
    *,
    df_jun_cat: pd.DataFrame | None = None,
    out_dir: Path = PREDICTIONS_DIR,
    models_dir: Path = MODELS_DIR,
) -> PredictionArtifacts:
    """Gera ``preds_jun_h{H}.parquet`` para um horizonte.

    Parameters
    ----------
    horizon_h
        Um de {1, 2, 4, 6, 8, 12}.
    df_jun_cat
        DataFrame opcional já filtrado por ``OEM='Caterpillar'`` (evita reler o
        parquet 6× quando o driver chama todos os horizontes em sequência).
        Se ``None``, é carregado e filtrado.
    out_dir, models_dir
        Diretórios de saída e dos modelos serializados.
    """
    if horizon_h not in (1, 2, 4, 6, 8, 12):
        raise ValueError(f"horizon_h inválido: {horizon_h}")

    if df_jun_cat is None:
        df_jun_cat = load_holdout_cat()

    df_eval = apply_censura_filter(df_jun_cat, horizon_h=horizon_h, kind="eval")

    X, y, _ = build_feature_matrix(df_eval, horizon_h)

    booster_path = models_dir / f"lgbm_h{horizon_h}_holdout_jun.txt"
    if not booster_path.exists():
        raise FileNotFoundError(f"Modelo holdout ausente: {booster_path}")
    booster = lgb.Booster(model_file=str(booster_path))

    raw = np.asarray(booster.predict(X), dtype=float)
    raw = np.clip(raw, EPS_CLIP, 1.0 - EPS_CLIP)

    calib_path = models_dir / f"lgbm_calibrated_h{horizon_h}.joblib"
    if not calib_path.exists():
        raise FileNotFoundError(f"Calibrador ausente: {calib_path}")
    calib = joblib.load(calib_path)
    cal, chosen = _calibrate(raw, calib)

    carry = {c: df_eval[c].to_numpy() for c in CARRY_COLS if c in df_eval.columns}
    out = pd.DataFrame(
        {
            **carry,
            "y_true": y.to_numpy(dtype="int8"),
            "score_raw": raw.astype("float64"),
            "score_cal": cal.astype("float64"),
        }
    )
    out["horizon_h"] = np.int8(horizon_h)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"preds_jun_h{horizon_h}.parquet"
    out.to_parquet(out_path, index=False)

    pack_raw = metric_pack(y.to_numpy(), raw)
    return PredictionArtifacts(
        horizon_h=horizon_h,
        parquet_path=out_path,
        n_rows=int(len(out)),
        n_pos=int(out["y_true"].sum()),
        chosen_method=chosen,
        auc_pr_raw=float(pack_raw["auc_pr"]),
        brier_cal=float(metric_pack(y.to_numpy(), cal)["brier"]),
    )


def load_holdout_cat() -> pd.DataFrame:
    """Lê o parquet de junho e filtra Caterpillar (D027)."""
    path = PROCESSED_DIR / "features_2025-06.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Parquet de junho ausente: {path}")
    df = pd.read_parquet(path)
    df["t_window"] = pd.to_datetime(df["t_window"])
    return (
        df[df["OEM"] == "Caterpillar"]
        .sort_values(["TAG", "t_window"])
        .reset_index(drop=True)
    )


__all__ = [
    "CARRY_COLS",
    "EPS_CLIP",
    "PredictionArtifacts",
    "load_holdout_cat",
    "predict_holdout_jun",
]
