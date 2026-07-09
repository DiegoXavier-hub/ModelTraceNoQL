"""PA-3 Autoencoder LSTM sobre LeTourneau (D027).

Sequência de 12 janelas de 15 min (3h de história) por (TAG, t).
Encoder LSTM -> bottleneck (8) -> Decoder LSTM -> reconstrução.
Score de anomalia = MSE de reconstrução.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

from src.utils.seeds import SEED

SEQ_LEN = 12  # 12 janelas x 15 min = 3h
BOTTLENECK = 8
LSTM_HIDDEN = 32


class _SequenceDataset(Dataset):
    def __init__(self, sequences: np.ndarray) -> None:
        self.sequences = torch.from_numpy(sequences).float()

    def __len__(self) -> int:
        return len(self.sequences)

    def __getitem__(self, idx: int) -> torch.Tensor:
        return self.sequences[idx]


class LSTMAutoencoder(nn.Module):
    def __init__(self, n_features: int, hidden: int = LSTM_HIDDEN, bottleneck: int = BOTTLENECK):
        super().__init__()
        self.encoder = nn.LSTM(n_features, hidden, batch_first=True)
        self.bottleneck_in = nn.Linear(hidden, bottleneck)
        self.bottleneck_out = nn.Linear(bottleneck, hidden)
        self.decoder = nn.LSTM(hidden, hidden, batch_first=True)
        self.out = nn.Linear(hidden, n_features)
        self.seq_len = SEQ_LEN

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        _, (h, _) = self.encoder(x)
        z = self.bottleneck_in(h.squeeze(0))
        h2 = self.bottleneck_out(z).unsqueeze(0)
        seq_len = x.size(1)
        decoder_in = h2.permute(1, 0, 2).expand(-1, seq_len, -1)
        dec_out, _ = self.decoder(decoder_in, (h2, torch.zeros_like(h2)))
        return self.out(dec_out)


def _sample_sequences(
    df: pd.DataFrame,
    feature_cols: list[str],
    seq_len: int = SEQ_LEN,
    seed: int = SEED,
    max_seqs: int | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    df = df.sort_values(["TAG", "t_window"]).reset_index(drop=True)
    seqs: list[np.ndarray] = []
    anchors: list = []
    pos_anchors: list[int] = []
    for tag, group in df.groupby("TAG", sort=False):
        feat = group[feature_cols].fillna(0.0).astype(float).to_numpy()
        labels = group["y_dontgo_12h"].astype(int).to_numpy()
        ts = group["t_window"].to_numpy()
        n = len(feat)
        if n < seq_len:
            continue
        for i in range(seq_len, n + 1):
            seqs.append(feat[i - seq_len : i])
            anchors.append(ts[i - 1])
            pos_anchors.append(int(labels[i - 1]))
    if max_seqs is not None and len(seqs) > max_seqs:
        idx = rng.choice(len(seqs), max_seqs, replace=False)
        seqs = [seqs[k] for k in idx]
        anchors = [anchors[k] for k in idx]
        pos_anchors = [pos_anchors[k] for k in idx]
    return (
        np.array(seqs, dtype=np.float32),
        np.array(anchors),
        np.array(pos_anchors, dtype=np.int8),
    )


def fit_autoencoder(
    sequences: np.ndarray,
    n_epochs: int = 8,
    batch_size: int = 128,
    lr: float = 1e-3,
    device: str | None = None,
    seed: int = SEED,
) -> LSTMAutoencoder:
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(seed)
    n_features = sequences.shape[2]
    model = LSTMAutoencoder(n_features=n_features).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()
    ds = _SequenceDataset(sequences)
    loader = DataLoader(ds, batch_size=batch_size, shuffle=True, drop_last=True)
    model.train(True)
    history: list[float] = []
    for _ in range(n_epochs):
        running = 0.0
        n_batches = 0
        for batch in loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            recon = model(batch)
            loss = loss_fn(recon, batch)
            loss.backward()
            optimizer.step()
            running += float(loss.item())
            n_batches += 1
        history.append(running / max(1, n_batches))
    model.train(False)
    model._train_loss_history = history  # type: ignore[attr-defined]
    return model


def reconstruction_score(
    model: LSTMAutoencoder, sequences: np.ndarray, batch_size: int = 256
) -> np.ndarray:
    device = next(model.parameters()).device
    model.train(False)
    out: list[np.ndarray] = []
    with torch.no_grad():
        for i in range(0, len(sequences), batch_size):
            batch = torch.from_numpy(sequences[i : i + batch_size]).float().to(device)
            recon = model(batch)
            mse = ((recon - batch) ** 2).mean(dim=(1, 2)).cpu().numpy()
            out.append(mse)
    return np.concatenate(out) if out else np.array([])


__all__ = [
    "SEQ_LEN",
    "BOTTLENECK",
    "LSTM_HIDDEN",
    "LSTMAutoencoder",
    "_sample_sequences",
    "fit_autoencoder",
    "reconstruction_score",
]
