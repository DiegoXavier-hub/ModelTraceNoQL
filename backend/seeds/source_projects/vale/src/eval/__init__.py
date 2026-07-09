"""Pacote de avaliação — splits temporais, métricas D012 e auditoria de drift.

Sub-módulos
-----------
- splits   : walk-forward (D011), filtro de censura (D032), auditoria de buffer.
- metrics  : pacote D012 (AUC-PR, Lift, AUC-ROC, Brier, ECE, Recall@P, Lead time).
- drift    : PSI / KS entre folds (Fase 4H).
"""
from __future__ import annotations
