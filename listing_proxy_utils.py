"""Build consistent listing identifiers across the four markets."""
from __future__ import annotations

import pandas as pd


MARKETS = ("WhiteHouse Market", "Dark0de", "ToRReZ", "Versus")


def clean_text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def listing_proxy(df: pd.DataFrame) -> pd.Series:
    """
    Return a market-specific identifier for distinct observed listings.

    `Pages` is listing-level on Dark0de and Versus. On WhiteHouse Market and
    ToRReZ it points to vendor profile or feedback pages, so vendor ID plus
    normalized product title is used as a listing proxy.
    """
    index = df.index
    empty = pd.Series("", index=index)
    website = clean_text(df["Website"]) if "Website" in df.columns else empty
    pages = clean_text(df["Pages"]) if "Pages" in df.columns else empty
    vendor = clean_text(df["ID_Num"]) if "ID_Num" in df.columns else empty
    product = clean_text(df["Productname"]) if "Productname" in df.columns else empty
    category3 = clean_text(df["Category 3"]) if "Category 3" in df.columns else empty

    valid_pages = pages.ne("") & ~pages.str.lower().isin({"nan", "none"})
    fallback = website + " | " + vendor + " | " + product.str.casefold() + " | " + category3
    profile_page_markets = website.isin({"WhiteHouse Market", "ToRReZ"})

    out = pages.where(valid_pages, fallback)
    out = out.where(~profile_page_markets, fallback)
    return out.astype(str).str.strip()


def deduplicate_listings(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["_listing_proxy"] = listing_proxy(out)
    out = out[out["_listing_proxy"].ne("")]
    return out.drop_duplicates(["Website", "_listing_proxy"]).copy()
