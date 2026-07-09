"""Pacote de modelos preditivos da Fase 4.

Sub-módulos
-----------
- ``pa1_lightgbm``       : classificador supervisionado primário (D004, D015).
- ``pa1_xgb``            : comparativo XGBoost.
- ``pa1_catboost``       : comparativo CatBoost.
- ``pa2_survival``       : Cox PH + Weibull AFT (D017).
- ``pa3_isolation_forest`` : anomalia LeTourneau (D027).
- ``pa3_autoencoder_lstm`` : anomalia LSTM (D027).
- ``calibration``        : Platt + Isotonic (D014).
"""
from __future__ import annotations
