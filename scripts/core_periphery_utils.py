"""Core-periphery estimators shared by the analysis scripts."""

from __future__ import annotations

import networkx as nx
import numpy as np
from scipy.optimize import minimize


def compute_borgatti_everett_core_score(
    graph: nx.Graph,
    *,
    weight: str = "weight",
    random_seed: int = 42,
    random_starts: int = 3,
) -> tuple[dict | None, float | None]:
    """Estimate continuous Borgatti--Everett coreness by correlation maximization.

    The fitted vector ``c`` maximizes the Pearson correlation between the
    off-diagonal entries of the observed weighted adjacency matrix and the
    corresponding entries of the ideal continuous core matrix ``c c'``.
    Scores are non-negative and rescaled so the largest score is one. The
    diagonal is excluded because these are non-reflexive networks: adjacency
    zeros on the diagonal denote unavailable self-ties, not observed absences.
    """
    if graph.number_of_nodes() == 0:
        return None, None

    nodes = list(graph.nodes())
    if graph.number_of_edges() == 0 or len(nodes) < 2:
        return dict.fromkeys(nodes, 0.0), 0.0

    adjacency = nx.to_numpy_array(
        graph,
        nodelist=nodes,
        weight=weight,
        dtype=float,
    )
    upper = np.triu_indices(len(nodes), k=1)
    observed = adjacency[upper]
    observed_centered_vector = observed - observed.mean()
    observed_centered = np.zeros_like(adjacency)
    observed_centered[upper] = observed_centered_vector
    observed_centered[(upper[1], upper[0])] = observed_centered_vector
    observed_norm = float(np.linalg.norm(observed_centered))
    observed_norm /= np.sqrt(2.0)
    if observed_norm == 0.0:
        return dict.fromkeys(nodes, 0.0), 0.0

    n_nodes = len(nodes)

    def objective_and_gradient(core: np.ndarray) -> tuple[float, np.ndarray]:
        # Evaluate the centered norm of the off-diagonal entries of B = c c'.
        core_sum = float(core.sum())
        core_sq_sum = float(core @ core)
        core_fourth_sum = float(np.sum(core**4))
        n_pairs = n_nodes * (n_nodes - 1) / 2.0
        ideal_sum = (core_sum**2 - core_sq_sum) / 2.0
        ideal_centered_norm_sq = (
            (core_sq_sum**2 - core_fourth_sum) / 2.0
            - ideal_sum**2 / n_pairs
        )
        if ideal_centered_norm_sq <= 1e-20:
            return 1.0, np.zeros_like(core)

        ideal_centered_norm = float(np.sqrt(ideal_centered_norm_sq))
        numerator = float(core @ observed_centered @ core) / 2.0
        correlation = numerator / (observed_norm * ideal_centered_norm)

        numerator_gradient = observed_centered @ core
        ideal_norm_sq_gradient = (
            2.0 * core_sq_sum * core
            - 2.0 * core**3
            - (2.0 * ideal_sum / n_pairs) * (core_sum - core)
        )
        norm_gradient = ideal_norm_sq_gradient / (2.0 * ideal_centered_norm)
        correlation_gradient = (
            numerator_gradient * ideal_centered_norm
            - numerator * norm_gradient
        ) / (observed_norm * ideal_centered_norm**2)
        return -correlation, -correlation_gradient

    eigenvalues, eigenvectors = np.linalg.eigh(adjacency)
    eigenvector_start = np.abs(eigenvectors[:, int(np.argmax(eigenvalues))])
    strength_start = adjacency.sum(axis=1)
    rng = np.random.default_rng(random_seed)
    starts = [eigenvector_start, strength_start]
    starts.extend(rng.random(n_nodes) for _ in range(random_starts))

    best_result = None
    bounds = [(1e-8, 1.0)] * n_nodes
    for start in starts:
        start = np.asarray(start, dtype=float)
        if float(start.max()) <= 0.0:
            continue
        start = start / float(start.max())
        result = minimize(
            objective_and_gradient,
            start,
            method="L-BFGS-B",
            jac=True,
            bounds=bounds,
            options={
                "maxiter": 2000,
                "ftol": 1e-12,
                "gtol": 1e-9,
                "maxls": 40,
            },
        )
        if best_result is None or result.fun < best_result.fun:
            best_result = result

    if best_result is None or not np.isfinite(best_result.fun):
        raise RuntimeError("Borgatti--Everett optimization failed to produce a finite solution")

    core = np.clip(best_result.x, 0.0, None)
    if float(core.max()) > 0.0:
        core = core / float(core.max())
    correlation = float(-objective_and_gradient(core)[0])
    return dict(zip(nodes, core)), correlation
