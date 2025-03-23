import numpy as np

from indexes import dense, sparse
from stats import gini


# that's some fast vectorized code :)


def adaptive_fusion(
    hits_dense: list[dense.Hit], hits_sparse: list[sparse.Hit]
) -> list[tuple[int, float]]:
    ids = list({h.id for h in hits_dense} | {h.id for h in hits_sparse})
    idx = {i: n for n, i in enumerate(ids)}

    sd = np.zeros(len(ids))
    ss = np.zeros(len(ids))
    for h in hits_dense:
        sd[idx[h.id]] = h.score
    for h in hits_sparse:
        ss[idx[h.id]] = h.score

    max_d, max_s = sd.max(), ss.max()
    sd /= max_d if max_d else 1
    ss /= max_s if max_s else 1

    g_d, g_s = gini(sd.tolist()), gini(ss.tolist())
    total = g_d + g_s

    if total:
        w_d = (g_d / total) * (max_d / (max_d + max_s + 1e-6))
        w_s = (g_s / total) * (max_s / (max_d + max_s + 1e-6))
    else:
        w_d = w_s = 0.5

    w_d, w_s = np.clip([w_d, w_s], 0.2, 0.8)
    w_d, w_s = w_d / (w_d + w_s), w_s / (w_d + w_s)

    fused = w_d * np.exp(sd) + w_s * np.exp(ss) + np.sqrt(sd * ss)

    # Normalize into [0,1]
    MAX_FUSED = np.e + 1
    fused /= MAX_FUSED
    fused = np.clip(fused, 0.0, 1.0)

    order = np.argsort(-fused)
    return [(ids[i], float(fused[i])) for i in order]
