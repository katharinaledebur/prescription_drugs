"""Prescription vendor portfolio overlap reported in the Results."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "notebooks"), str(ROOT / "scripts")]

import dnm_viz_utils as dvu  # noqa: E402
from listing_proxy_utils import listing_proxy  # noqa: E402


DATA = ROOT / "data_outputs/master_clean.parquet"
OUTPUT = ROOT / "outputs/vendor_portfolio_overlap.csv"
MARKETS = ["WhiteHouse Market", "Dark0de", "ToRReZ", "Versus"]


def main() -> None:
    rows = pd.read_parquet(DATA)
    drugs = rows[
        rows["Product Category"].eq("Drugs") & rows["Website"].isin(MARKETS)
    ].copy()
    mapping = dvu.load_category2_most_common_mapping(drugs)
    drugs["vendor"] = drugs["ID_Num"].fillna("").astype(str).str.strip()
    drugs["product"] = drugs["Category 3"].fillna("").astype(str).str.strip()
    drugs["category2"] = drugs["product"].map(mapping).fillna("Unknown")
    drugs["listing"] = listing_proxy(drugs)
    drugs = drugs[
        drugs["vendor"].ne("")
        & drugs["product"].ne("")
        & drugs["listing"].ne("")
        & drugs["category2"].ne("Unknown")
    ].drop_duplicates(["Website", "listing"])

    vendor_categories = (
        drugs.drop_duplicates(["Website", "vendor", "category2"])
        .groupby(["Website", "vendor"])["category2"]
        .agg(lambda values: set(values))
        .reset_index(name="categories")
    )
    prescription = vendor_categories[
        vendor_categories["categories"].map(lambda values: "Prescription" in values)
    ].copy()
    prescription["also_nonprescription"] = prescription["categories"].map(
        lambda values: any(value != "Prescription" for value in values)
    )

    summary = (
        prescription.groupby("Website")
        .agg(
            prescription_vendors=("vendor", "size"),
            mixed_category_vendors=("also_nonprescription", "sum"),
        )
        .reset_index()
        .rename(columns={"Website": "market"})
    )
    summary["prescription_only_vendors"] = (
        summary["prescription_vendors"] - summary["mixed_category_vendors"]
    )
    summary["mixed_category_share"] = (
        summary["mixed_category_vendors"] / summary["prescription_vendors"]
    )
    total = pd.DataFrame(
        [
            {
                "market": "All markets",
                "prescription_vendors": summary["prescription_vendors"].sum(),
                "mixed_category_vendors": summary["mixed_category_vendors"].sum(),
                "prescription_only_vendors": summary["prescription_only_vendors"].sum(),
                "mixed_category_share": summary["mixed_category_vendors"].sum()
                / summary["prescription_vendors"].sum(),
            }
        ]
    )
    OUTPUT.parent.mkdir(exist_ok=True)
    pd.concat([summary, total], ignore_index=True).to_csv(OUTPUT, index=False)
    print(pd.concat([summary, total], ignore_index=True).to_string(index=False))


if __name__ == "__main__":
    main()

