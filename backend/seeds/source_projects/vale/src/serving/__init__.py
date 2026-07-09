"""Pacote de serving — inferência online e batch para deployment.

Conteúdo:
- ``predict_realtime``: CLI de inferência batch sobre um parquet de
  features (89 cols) já preparado pela pipeline da Fase 3. Produz CSV
  de alertas calibrados por horizonte.

Uso típico via CLI::

    python -m src.serving.predict_realtime \
        --features-in data/processed/features_2025-06.parquet \
        --thresholds 0.4757 0.4757 0.4757 0.3590 0.3590 0.3590 \
        --out-csv outputs/alerts/alerts_2025-06.csv

Princípio governante: ROBUSTEZ > custo computacional. Em produção,
este script seria substituído por um servidor FastAPI (ver Trabalho
Futuro #5 do Cap. 6), mas como protótipo inicial ele já encapsula
toda a lógica de inferência multi-horizonte calibrada.
"""

__all__: list[str] = []
