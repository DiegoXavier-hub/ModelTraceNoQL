"""CLI de inferência batch — Don't Go multi-horizonte calibrado (Frente F4).

Toma como entrada um parquet de \textit{features} já preparado pela
\textit{pipeline} da Fase~3 (89 colunas no schema v2) e produz um CSV de
alertas calibrados por horizonte. Os limiares operacionais $\tau$ podem
ser fornecidos como parâmetro (lista de 6 valores em ordem
H={1,2,4,6,8,12}h) ou inferidos automaticamente do
``fase5a_consolidado.json`` (limiar `P>=0.5` por H).

Princípio: este script é o **protótipo** do servidor de inferência
descrito em Trabalho Futuro #5. Em produção, será substituído por um
servidor FastAPI com modelo carregado em memória, mas a lógica
algorítmica é idêntica.

Uso típico::

    python -m src.serving.predict_realtime \
        --features-in data/processed/features_2025-06.parquet \
        --horizons 12 \
        --threshold-mode auto \
        --out-csv outputs/alerts/alerts_h12.csv

    python -m src.serving.predict_realtime \
        --features-in data/processed/features_2025-06.parquet \
        --horizons 4 8 12 \
        --thresholds 0.4757 0.4081 0.3590 \
        --out-csv outputs/alerts/alerts_multi.csv

Saída CSV: ``[TAG, t_window, Tag_Frota, horizon_h, score_raw,
score_cal, threshold, is_alert, alert_severity]``.

``alert_severity`` é categórica em três níveis:
- ``high``: score_cal >= threshold * 1.5
- ``medium``: threshold <= score_cal < threshold * 1.5
- ``info``: 0.5 * threshold <= score_cal < threshold (alerta antecipado)
- omitido: score_cal < 0.5 * threshold
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd

from src.eval.predictions import EPS_CLIP, _calibrate
from src.eval.splits import apply_censura_filter
from src.models.pa1_lightgbm import build_feature_matrix
from src.utils.paths import MODELS_DIR, PROJECT_ROOT, REPORTS_DIR


HORIZONS_ALL: tuple[int, ...] = (1, 2, 4, 6, 8, 12)

logger = logging.getLogger("predict_realtime")


@dataclass(frozen=True)
class HorizonInferenceArtifacts:
    """Artefatos de uma inferência única em um horizonte."""

    horizon_h: int
    threshold: float
    n_windows_scored: int
    n_alerts: int
    n_high: int
    n_medium: int
    n_info: int


def _resolve_thresholds(
    horizons: Sequence[int],
    thresholds: Optional[Sequence[float]],
    threshold_mode: str,
) -> dict[int, float]:
    """Resolve limiar por horizonte conforme parâmetros do CLI.

    Modos:
    - ``thresholds``: lista explícita (mesma ordem que `horizons`).
    - ``threshold_mode='auto'``: lê do `fase5a_consolidado.json`.
    - ``threshold_mode='conservative'``: 0.30 para todos os H.
    - ``threshold_mode='aggressive'``: 0.20 para todos os H.
    """
    if thresholds is not None:
        if len(thresholds) != len(horizons):
            raise ValueError(
                f"thresholds tem {len(thresholds)} elementos mas horizons tem {len(horizons)}"
            )
        return {h: float(t) for h, t in zip(horizons, thresholds)}
    if threshold_mode == "conservative":
        return {h: 0.30 for h in horizons}
    if threshold_mode == "aggressive":
        return {h: 0.20 for h in horizons}
    if threshold_mode != "auto":
        raise ValueError(f"threshold_mode inválido: {threshold_mode!r}")

    json_path = REPORTS_DIR / "eda_results" / "fase5a_consolidado.json"
    if not json_path.is_file():
        raise FileNotFoundError(
            f"threshold_mode=auto requer {json_path} (Fase 5A não rodou?)"
        )
    with open(json_path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    out: dict[int, float] = {}
    for h in horizons:
        key = f"h{h}"
        cm = payload.get("confusion_matrix_h4" if h == 4 else f"confusion_matrix_h{h}")
        # Fase 5A só persiste confusion_matrix_h4 e confusion_matrix_h12.
        # Para outros, fallback razoável: 0.40 (entre Cap. 6 piloto e plena).
        if cm and "P>=0.5" in cm:
            out[h] = float(cm["P>=0.5"]["threshold"])
        elif cm and "P≥0.5" in cm:
            out[h] = float(cm["P≥0.5"]["threshold"])
        else:
            out[h] = 0.40
            logger.warning(
                "[threshold] H=%s sem CM persistida; usando default 0.40", h
            )
    return out


def _classify_severity(score_cal: float, threshold: float) -> str:
    """Classifica severidade do alerta em quatro níveis."""
    if score_cal >= threshold * 1.5:
        return "high"
    if score_cal >= threshold:
        return "medium"
    if score_cal >= threshold * 0.5:
        return "info"
    return "none"


def score_horizon(
    df_features: pd.DataFrame,
    horizon_h: int,
    *,
    threshold: float,
    models_dir: Path = MODELS_DIR,
) -> tuple[pd.DataFrame, HorizonInferenceArtifacts]:
    """Aplica modelo + calibrador para um único horizonte.

    Args:
        df_features: parquet de features carregado e filtrado.
        horizon_h: um de {1, 2, 4, 6, 8, 12}.
        threshold: limiar operacional.
        models_dir: pasta com boosters + calibradores.

    Returns:
        (df_alerts, artifacts) — df_alerts tem uma linha por janela com
        score e alerta classificado.
    """
    if horizon_h not in HORIZONS_ALL:
        raise ValueError(f"horizon_h inválido: {horizon_h}")

    df_eval = apply_censura_filter(df_features, horizon_h=horizon_h, kind="eval")
    if df_eval.empty:
        return df_eval, HorizonInferenceArtifacts(
            horizon_h=horizon_h,
            threshold=threshold,
            n_windows_scored=0,
            n_alerts=0,
            n_high=0,
            n_medium=0,
            n_info=0,
        )

    X, _y, _ = build_feature_matrix(df_eval, horizon_h)

    booster_path = models_dir / f"lgbm_h{horizon_h}_holdout_jun.txt"
    if not booster_path.is_file():
        raise FileNotFoundError(f"Booster ausente: {booster_path}")
    booster = lgb.Booster(model_file=str(booster_path))
    raw = np.clip(np.asarray(booster.predict(X), dtype=float), EPS_CLIP, 1.0 - EPS_CLIP)

    calib_path = models_dir / f"lgbm_calibrated_h{horizon_h}.joblib"
    if not calib_path.is_file():
        raise FileNotFoundError(f"Calibrador ausente: {calib_path}")
    calib = joblib.load(calib_path)
    cal, _chosen = _calibrate(raw, calib)

    severity = np.array(
        [_classify_severity(float(s), threshold) for s in cal], dtype=object
    )
    is_alert = severity != "none"

    out = pd.DataFrame(
        {
            "TAG": df_eval["TAG"].to_numpy(),
            "t_window": pd.to_datetime(df_eval["t_window"]).to_numpy(),
            "Tag_Frota": df_eval["Tag_Frota"].to_numpy(),
            "horizon_h": np.int8(horizon_h),
            "score_raw": raw.astype("float64"),
            "score_cal": cal.astype("float64"),
            "threshold": float(threshold),
            "is_alert": is_alert.astype(bool),
            "alert_severity": severity,
        }
    )
    artifacts = HorizonInferenceArtifacts(
        horizon_h=horizon_h,
        threshold=float(threshold),
        n_windows_scored=int(len(out)),
        n_alerts=int(is_alert.sum()),
        n_high=int((severity == "high").sum()),
        n_medium=int((severity == "medium").sum()),
        n_info=int((severity == "info").sum()),
    )
    return out, artifacts


def run_inference(
    features_path: Path,
    horizons: Iterable[int],
    threshold_map: dict[int, float],
    *,
    only_alerts: bool = True,
    out_csv: Optional[Path] = None,
) -> tuple[pd.DataFrame, list[HorizonInferenceArtifacts]]:
    """Executa inferência multi-horizonte e persiste CSV opcional."""
    if not features_path.is_file():
        raise FileNotFoundError(f"Features parquet ausente: {features_path}")

    df = pd.read_parquet(features_path)
    df["t_window"] = pd.to_datetime(df["t_window"])
    if "OEM" in df.columns:
        n0 = len(df)
        df = df[df["OEM"] == "Caterpillar"]
        logger.info(
            "[serving] OEM filter: %d -> %d janelas (Caterpillar apenas, D027)",
            n0,
            len(df),
        )

    pieces: list[pd.DataFrame] = []
    arts: list[HorizonInferenceArtifacts] = []
    for h in horizons:
        thr = threshold_map[h]
        df_h, art = score_horizon(df, h, threshold=thr)
        if only_alerts:
            df_h = df_h[df_h["is_alert"]]
        pieces.append(df_h)
        arts.append(art)
        logger.info(
            "[serving] H=%dh thr=%.4f scored=%d alerts=%d (high=%d med=%d info=%d)",
            h,
            thr,
            art.n_windows_scored,
            art.n_alerts,
            art.n_high,
            art.n_medium,
            art.n_info,
        )

    full = pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()
    if out_csv is not None:
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        full.to_csv(out_csv, index=False, encoding="utf-8")
        logger.info("[serving] alerts CSV -> %s (%d rows)", out_csv, len(full))
    return full, arts


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="predict_realtime",
        description=(
            "Inferência batch Don't Go multi-horizonte calibrada. "
            "Protótipo do servidor real-time descrito em Trabalho Futuro #5."
        ),
    )
    p.add_argument(
        "--features-in",
        type=Path,
        required=True,
        help="Caminho para o parquet de features (89 cols, schema v2).",
    )
    p.add_argument(
        "--horizons",
        type=int,
        nargs="+",
        choices=list(HORIZONS_ALL),
        default=list(HORIZONS_ALL),
        help="Horizontes a aplicar (default: todos).",
    )
    grp = p.add_mutually_exclusive_group()
    grp.add_argument(
        "--thresholds",
        type=float,
        nargs="+",
        help=(
            "Limiares operacionais (ordem deve casar com --horizons). "
            "Se omitido, --threshold-mode é usado."
        ),
    )
    grp.add_argument(
        "--threshold-mode",
        type=str,
        default="auto",
        choices=("auto", "conservative", "aggressive"),
        help="Modo de inferência de limiar quando --thresholds não fornecido.",
    )
    p.add_argument(
        "--out-csv",
        type=Path,
        default=PROJECT_ROOT / "outputs" / "alerts" / "alerts.csv",
        help="Caminho de saída do CSV de alertas.",
    )
    p.add_argument(
        "--all-rows",
        action="store_true",
        help="Persistir todas as janelas (não apenas alertas).",
    )
    p.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="Nível de logging.",
    )
    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    threshold_map = _resolve_thresholds(
        horizons=args.horizons,
        thresholds=args.thresholds,
        threshold_mode=args.threshold_mode,
    )
    logger.info("[serving] threshold_map=%s", threshold_map)
    _, arts = run_inference(
        features_path=args.features_in,
        horizons=args.horizons,
        threshold_map=threshold_map,
        only_alerts=not args.all_rows,
        out_csv=args.out_csv,
    )
    summary = {
        f"h{a.horizon_h}": {
            "threshold": a.threshold,
            "n_scored": a.n_windows_scored,
            "n_alerts": a.n_alerts,
            "n_high": a.n_high,
            "n_medium": a.n_medium,
            "n_info": a.n_info,
        }
        for a in arts
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
