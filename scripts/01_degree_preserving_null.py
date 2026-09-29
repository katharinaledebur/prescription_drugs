"""Degree preserving bipartite null model reported in Supplementary Table S2."""

from __future__ import annotations

import argparse
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

from core_periphery_utils import compute_borgatti_everett_core_score
from listing_proxy_utils import listing_proxy


ROOT = Path(__file__).resolve().parents[1]
DATA_PARQUET = ROOT / "data_outputs/master_clean.parquet"
MAPPING_XLSX = ROOT / "prescription_reports/category3_to_category2_mapping.xlsx"
OUTPUT = ROOT / "outputs"
MARKETS = ["WhiteHouse Market", "Dark0de", "ToRReZ", "Versus"]


def load_data() -> tuple[pd.DataFrame, dict[str, str]]:
    data = pd.read_parquet(DATA_PARQUET)
    drugs = data[
        data["Website"].isin(MARKETS) & data["Product Category"].eq("Drugs")
    ].copy()
    mapped = pd.read_excel(
        MAPPING_XLSX,
        sheet_name="All Markets Summary",
        usecols=["Category 3", "Category 2 (most common)"],
    ).dropna()
    mapped["Category 3"] = mapped["Category 3"].astype(str).str.strip()
    mapped["Category 2 (most common)"] = (
        mapped["Category 2 (most common)"].astype(str).str.strip()
    )
    mapping = mapped.set_index("Category 3")["Category 2 (most common)"].to_dict()
    return drugs, mapping


def vendor_product_counts(data: pd.DataFrame) -> pd.DataFrame:
    rows = data.dropna(subset=["ID_Num", "Category 3"]).copy()
    rows["ID_Num"] = rows["ID_Num"].astype(str).str.strip()
    rows["Category 3"] = rows["Category 3"].astype(str).str.strip()
    rows["_listing"] = listing_proxy(rows)
    rows = rows[rows["_listing"].notna() & rows["_listing"].ne("")]
    return (
        rows.groupby(["ID_Num", "Category 3"], sort=False)["_listing"]
        .nunique()
        .rename("n_listings")
        .reset_index()
        .query("n_listings > 0")
    )


def revealed_matrix(counts: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    vendors = counts["ID_Num"].drop_duplicates().tolist()
    products = counts["Category 3"].drop_duplicates().tolist()
    vendor_index = {vendor: i for i, vendor in enumerate(vendors)}
    product_index = {product: j for j, product in enumerate(products)}
    matrix = np.zeros((len(vendors), len(products)), dtype=float)
    for row in counts.itertuples(index=False):
        matrix[vendor_index[row.ID_Num], product_index[row._1]] = row.n_listings
    row_sum = matrix.sum(axis=1, keepdims=True)
    column_sum = matrix.sum(axis=0, keepdims=True)
    total = matrix.sum()
    rca = np.divide(
        matrix * total,
        row_sum * column_sum,
        out=np.zeros_like(matrix),
        where=(row_sum > 0) & (column_sum > 0) & (total > 0),
    )
    return (rca >= 1).astype(np.int8), products


def proximity(matrix: np.ndarray) -> np.ndarray:
    values = matrix.astype(float)
    ubiquity = values.sum(axis=0)
    overlap = values.T @ values
    denominator = np.maximum(ubiquity[:, None], ubiquity[None, :])
    phi = np.divide(
        overlap,
        denominator,
        out=np.zeros_like(overlap),
        where=denominator > 0,
    )
    np.fill_diagonal(phi, 0)
    return phi


def product_space(products: list[str], phi: np.ndarray) -> nx.Graph:
    graph = nx.Graph()
    graph.add_nodes_from(products)
    rows, columns = np.where(np.triu(phi, k=1) > 0)
    for i, j in zip(rows, columns):
        graph.add_edge(products[i], products[j], weight=float(phi[i, j]))
    component = max(nx.connected_components(graph), key=len)
    return graph.subgraph(component).copy()


def core_share(graph: nx.Graph, mapping: dict[str, str], seed: int) -> float:
    scores, _ = compute_borgatti_everett_core_score(
        graph, random_seed=seed, random_starts=1
    )
    total = sum(scores.values())
    return sum(
        score
        for product, score in scores.items()
        if mapping.get(str(product)) == "Prescription"
    ) / total


def curveball(matrix: np.ndarray, rng: np.random.Generator, trades: int) -> np.ndarray:
    rows = [set(np.flatnonzero(row)) for row in matrix]
    nonempty = np.array([i for i, row in enumerate(rows) if row], dtype=int)
    for _ in range(trades):
        a, b = rng.choice(nonempty, size=2, replace=False)
        common = rows[a] & rows[b]
        only_a = list(rows[a] - rows[b])
        only_b = list(rows[b] - rows[a])
        if not only_a or not only_b:
            continue
        pool = only_a + only_b
        rng.shuffle(pool)
        rows[a] = common | set(pool[: len(only_a)])
        rows[b] = common | set(pool[len(only_a) :])
    randomized = np.zeros_like(matrix)
    for i, columns in enumerate(rows):
        randomized[i, list(columns)] = 1
    if not np.array_equal(randomized.sum(axis=0), matrix.sum(axis=0)):
        raise RuntimeError("Product degrees changed during randomization")
    if not np.array_equal(randomized.sum(axis=1), matrix.sum(axis=1)):
        raise RuntimeError("Vendor degrees changed during randomization")
    return randomized


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--randomizations", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    data, mapping = load_data()
    summaries = []
    distributions = []
    for market_index, market in enumerate(MARKETS):
        counts = vendor_product_counts(data[data["Website"].eq(market)])
        observed_matrix, products = revealed_matrix(counts)
        observed = core_share(
            product_space(products, proximity(observed_matrix)),
            mapping,
            args.seed + market_index,
        )
        rng = np.random.default_rng(args.seed + market_index)
        current = observed_matrix.copy()
        values = []
        trades = max(1000, 10 * len(current))
        for iteration in range(args.randomizations):
            current = curveball(current, rng, trades)
            value = core_share(
                product_space(products, proximity(current)),
                mapping,
                args.seed + iteration + 1,
            )
            values.append(value)
            distributions.append(
                {"market": market, "iteration": iteration + 1, "null_core_share": value}
            )
        values_array = np.asarray(values)
        summaries.append(
            {
                "market": market,
                "observed_share": observed,
                "null_mean": values_array.mean(),
                "null_q025": np.quantile(values_array, 0.025),
                "null_q975": np.quantile(values_array, 0.975),
                "empirical_p": (1 + np.count_nonzero(values_array >= observed))
                / (len(values_array) + 1),
                "n_randomizations": len(values_array),
            }
        )
        print(f"{market}: completed {args.randomizations} randomizations", flush=True)

    OUTPUT.mkdir(exist_ok=True)
    pd.DataFrame(summaries).to_csv(
        OUTPUT / "supplementary_table_s2_degree_preserving_null.csv", index=False
    )
    pd.DataFrame(distributions).to_csv(
        OUTPUT / "supplementary_table_s2_null_distribution.csv", index=False
    )


if __name__ == "__main__":
    main()

