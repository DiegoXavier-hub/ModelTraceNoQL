"""Seeds globais para reprodutibilidade.

Aplica SEED=42 a todos os subsistemas estocasticos relevantes do projeto:
random, numpy, torch (CPU+CUDA). LightGBM/XGBoost/sklearn nao tem 'global
seed' — passe SEED como random_state nos estimators.

Uso tipico em notebook (primeira celula apos imports):
    from src.utils.seeds import SEED, set_global_seed
    set_global_seed()  # ou set_global_seed(strict_torch=True) p/ bit-exact

NOTA sobre PYTHONHASHSEED: para ter efeito real ele precisa estar setado
ANTES do interpretador iniciar. Esta funcao apenas avisa se voce esqueceu.
"""
from __future__ import annotations

import os
import random
import warnings
from typing import Any

import numpy as np

SEED: int = 42


def set_global_seed(seed: int = SEED, *, strict_torch: bool = False) -> dict[str, Any]:
    """Aplica `seed` em random, numpy e torch (se instalado).

    Args:
        seed: inteiro, default SEED=42.
        strict_torch: se True, forca cudnn deterministic + benchmark=False.
            Custa ~20% de throughput. Use apenas para auditoria bit-exact.

    Returns:
        Dicionario com o que foi setado — util para logar no inicio do run.
    """
    info: dict[str, Any] = {"seed": seed, "strict_torch": strict_torch}

    random.seed(seed)
    info["random"] = "ok"

    np.random.seed(seed)
    info["numpy_legacy"] = "ok"
    info["numpy_rng"] = np.random.default_rng(seed)  # rota moderna

    if os.environ.get("PYTHONHASHSEED") != str(seed):
        warnings.warn(
            f"PYTHONHASHSEED nao esta como '{seed}' no ambiente. "
            "Hashes de dict/set podem variar entre runs. "
            f"Para fixar: export PYTHONHASHSEED={seed} antes de iniciar Python.",
            stacklevel=2,
        )
    info["pythonhashseed_env"] = os.environ.get("PYTHONHASHSEED")

    try:
        import torch

        torch.manual_seed(seed)
        info["torch"] = torch.__version__
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            info["torch_cuda"] = True
            if strict_torch:
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False
                info["cudnn_deterministic"] = True
        else:
            info["torch_cuda"] = False
    except ImportError:
        info["torch"] = "not_installed"

    return info


__all__ = ["SEED", "set_global_seed"]
