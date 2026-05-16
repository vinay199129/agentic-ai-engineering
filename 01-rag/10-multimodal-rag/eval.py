"""Eval for multimodal-rag: recall@k for text-only vs joint embedding."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

_HERE = Path(__file__).resolve()
for _p in (_HERE.parent, *_HERE.parents):
    if (_p / "shared").exists() and (_p / "pyproject.toml").exists():
        sys.path.insert(0, str(_p))
        os.chdir(_p)
        break

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from shared.embedders import cosine_topk, hash_embed  # noqa: E402
from shared.loaders import load_corpus, load_golden_qa  # noqa: E402

KS = (1, 3, 5)
PCT = re.compile(r"(\d+(?:\.\d+)?)\s*%")
FIG_DIR = Path(__file__).parent / "figures"


def render_fig(doc) -> Path:  # type: ignore[no-untyped-def]
    nums = [float(m) for m in PCT.findall(doc.abstract)][:4] or [1.0]
    while len(nums) < 4:
        nums.append(nums[-1] * 0.8)
    rng = np.random.default_rng(abs(hash(doc.arxiv_id)) % (2**32))
    jitter = rng.uniform(-1.0, 1.0, size=4)
    vals = np.array(nums) + jitter
    fig, ax = plt.subplots(figsize=(3.2, 2.0), dpi=110)
    ax.bar(["A", "B", "C", "D"], vals, color="#4C72B0")
    ax.set_title(doc.arxiv_id + " — synthetic chart", fontsize=8)
    ax.tick_params(labelsize=7)
    fig.tight_layout()
    out = FIG_DIR / f"{doc.arxiv_id}.png"
    fig.savefig(out, dpi=110)
    plt.close(fig)
    return out


def img_embed(path: Path, dims: int = 256) -> np.ndarray:
    raw = path.read_bytes()
    out = np.zeros(dims, dtype=np.float32)
    buf = raw
    for i in range(dims):
        buf = hashlib.sha256(buf).digest()
        out[i] = (buf[0] / 255.0) * 2 - 1
    n = float(np.linalg.norm(out)) or 1.0
    return out / n


def main() -> None:
    docs = load_corpus()
    qa = [q for q in load_golden_qa() if q.source_ids]
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig_paths = {d.arxiv_id: render_fig(d) for d in docs}
    img_vecs = np.stack([img_embed(fig_paths[d.arxiv_id]) for d in docs])
    txt_vecs = hash_embed([d.title + ". " + d.abstract for d in docs], dims=256, seed=0)
    joint = (txt_vecs + img_vecs) / 2.0
    joint /= np.linalg.norm(joint, axis=1, keepdims=True)
    doc_ids = [d.arxiv_id for d in docs]

    def recall(matrix: np.ndarray, k: int) -> float:
        hits = 0
        for q in qa:
            qv = hash_embed([q.question], dims=256, seed=0)[0]
            idx, _ = cosine_topk(qv, matrix, k=k)
            got = {doc_ids[i] for i in idx}
            if got & set(q.source_ids):
                hits += 1
        return round(hits / len(qa), 4)

    per_modality = {
        f"recall@{k}": {"text": recall(txt_vecs, k), "joint": recall(joint, k)} for k in KS
    }
    flat: dict[str, dict[str, float]] = {}
    for k in KS:
        flat[f"recall@{k}"] = per_modality[f"recall@{k}"]
    snapshot = {
        "technique": "multimodal-rag",
        "version": "0.1.0",
        "dataset": "benchmarks/golden-qa/v1",
        "run_id": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {"n_docs": len(docs), "n_questions": len(qa), **flat},
    }
    out = Path(__file__).parent / "eval-snapshot.json"
    out.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
