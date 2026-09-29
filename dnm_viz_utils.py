"""Shared paths, labels and plotting helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd

MARKETS = ["WhiteHouse Market", "Dark0de", "ToRReZ", "Versus"]
MARKET_FILE_NAMES: Dict[str, str] = {
    "WhiteHouse Market": "WhiteHouse_Market",
    "Dark0de": "Dark0de",
    "ToRReZ": "ToRReZ",
    "Versus": "Versus",
}
PANEL_BY_MARKET: Dict[str, str] = {
    "WhiteHouse Market": "A",
    "Dark0de": "B",
    "ToRReZ": "C",
    "Versus": "D",
}
CATEGORY2_MAPPING_XLSX = "prescription_reports/category3_to_category2_mapping.xlsx"
PRIMARY_CATEGORY2_COLUMN = "Category 2 (listing-proxy mode)"


def repo_root() -> Path:
    """Find the repository root from a notebook or script."""
    p = Path.cwd().resolve()
    for c in [p, *p.parents]:
        if (c / "data_outputs").is_dir() and (c / "scripts").is_dir():
            return c
    if p.name == "notebooks" and (p.parent / "data_outputs").is_dir():
        return p.parent
    return p


def load_master_drugs() -> pd.DataFrame:
    r = repo_root()
    pq, csv = r / "data_outputs/master_clean.parquet", r / "data_outputs/master_clean.csv"
    if pq.exists():
        df = pd.read_parquet(pq)
    elif csv.exists():
        df = pd.read_csv(csv, low_memory=False)
    else:
        raise FileNotFoundError(f"Need {pq} or {csv}")
    return df[df["Product Category"] == "Drugs"].copy()


def compute_review_row_mapping(df_drugs: pd.DataFrame | None = None) -> Dict[str, str]:
    """Return the older review-row-weighted category mapping."""
    if df_drugs is None:
        df_drugs = load_master_drugs()
    prod_cat = df_drugs[["Category 3", "Category 2"]].dropna()
    g = prod_cat.groupby("Category 3")["Category 2"].agg(
        lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]
    )
    return {str(k).strip(): str(v).strip() for k, v in g.items()}


def load_category_mapping(df_drugs: pd.DataFrame | None = None) -> Dict[str, str]:
    """Load the listing-weighted Category 2 mapping used in the study."""
    path = repo_root() / CATEGORY2_MAPPING_XLSX
    if not path.exists():
        raise FileNotFoundError(
            f"Primary listing-proxy category mapping not found: {path}. "
            "Run scripts/00_build_listing_proxy_category_mapping.py and rebuild the workbook."
        )
    return load_category2_excel_mapping(path, PRIMARY_CATEGORY2_COLUMN)


def load_category2_excel_mapping(
    mapping_xlsx: Path | None = None, category2_col: str = "Category 2 (most common)"
) -> Dict[str, str]:
    """Load Category 3 -> Category 2 from the mapping workbook."""
    path = mapping_xlsx or repo_root() / CATEGORY2_MAPPING_XLSX
    if not path.exists():
        raise FileNotFoundError(path)
    df = pd.read_excel(path)

    cat3_col = None
    for col in df.columns:
        col_lower = str(col).lower()
        if "category" in col_lower and ("3" in col_lower or "three" in col_lower):
            cat3_col = col

    if cat3_col is None:
        if len(df.columns) < 1:
            raise ValueError(f"Could not find Category 3 column in {path}")
        cat3_col = df.columns[0]
    if category2_col not in df.columns:
        raise ValueError(f"Could not find {category2_col!r} in {path}. Columns: {df.columns.tolist()}")

    mapping_df = df[[cat3_col, category2_col]].dropna()
    g = mapping_df.groupby(cat3_col)[category2_col].agg(
        lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]
    )
    return {str(k).strip(): str(v).strip() for k, v in g.items()}


def load_category2_most_common_mapping(df_drugs: pd.DataFrame | None = None) -> Dict[str, str]:
    """Map products with the listing-weighted workbook mapping."""
    if df_drugs is None:
        df_drugs = load_master_drugs()
    primary = load_category2_excel_mapping(category2_col=PRIMARY_CATEGORY2_COLUMN)
    out: Dict[str, str] = {}
    for cat3 in df_drugs["Category 3"].dropna().unique():
        cat3_str = str(cat3).strip()
        out[cat3_str] = primary.get(cat3_str, "Unknown")
    return out


def load_category_color_map(prod_to_cat2: Dict[str, str]) -> Dict[str, object]:
    """Return the fixed Category 2 palette used in the manuscript."""
    color_map: Dict[str, object] = {
        "Prescription": "#E377A2",
        "Benzos": "#8DD3C7",
        "Cannabis": "#FFFFB3",
        "Custom Listing": "#8DA0CB",
        "Dissociatives": "#BEBADA",
        "Ecstasy": "#FB8072",
        "Opioids": "#80B1D3",
        "Other": "#B3B3B3",
        "Paraphernalia": "#B3DE69",
        "Precursors": "#FCCDE5",
        "Psychedelics": "#BC80BD",
        "Steroids": "#CCEBC5",
        "Stimulants": "#FFED6F",
        "Tobacco": "#66C2A5",
        "Weight Loss": "#FC8D62",
        "Unknown": "#B3B3B3",
    }
    fallback = plt.get_cmap("tab20")
    for idx, cat in enumerate(sorted(set(prod_to_cat2.values()))):
        cat_str = str(cat).strip()
        if cat_str and cat_str.lower() != "nan" and cat_str not in color_map:
            color_map[cat_str] = fallback(idx % fallback.N)
    return color_map


def style_axes(ax: plt.Axes) -> None:
    ax.grid(False)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.tick_params(axis="both", direction="in")
    ax.set_axisbelow(True)


def title_left(ax: plt.Axes, s: str, *, fontsize: int = 13) -> None:
    ax.set_title(s, loc="left", fontsize=fontsize)


def panel_letter(ax: plt.Axes, letter: str) -> None:
    ax.text(-0.08, 1.02, letter, transform=ax.transAxes, ha="left", va="bottom", fontsize=18)


def import_script_module(stem: str):
    """Load scripts/<stem>.py as a module (handles leading digits in filename)."""
    import importlib.util

    path = repo_root() / "scripts" / f"{stem}.py"
    spec = importlib.util.spec_from_file_location(stem, path)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def import_module_from_path(name: str, path: Path):
    """Load an arbitrary .py path (e.g. under prescription_reports/)."""
    import importlib.util

    path = path.resolve()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
