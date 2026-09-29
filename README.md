# Prescription drugs at the core of darknet drug markets

This repository contains the code used for the figures, tables and numerical results reported in the manuscript. Products are connected when they are disproportionately offered by the same vendors across four darknet markets crawled in 2021 and early 2022.

The repository intentionally excludes exploratory and unreported analyses, raw marketplace files and generated outputs.

## Data

The raw crawl is not public because it contains sensitive marketplace level information. The public Zenodo record contains derived source data for every reported figure and table, analysis results, product space networks and documentation. Those files allow the reported results to be inspected without exposing marketplace records, but they do not permit the complete reconstruction of the analysis from the original crawl. Requests for the restricted data are considered by the data provider under an appropriate data use agreement, as described in the manuscript. Derived data underlying the reported figures, tables and models are available at https://doi.org/10.5281/zenodo.23037050

The product category mapping is included in this repository.

The analysis was run with Python 3.12. Create an environment and install the pinned dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
jupyter lab
```

1. `01_product_space.ipynb` constructs the four product spaces and Supplementary Figure S3.
2. `02_figure_1_core_share.ipynb` creates Figure 1 and the label permutation results in Supplementary Table S1.
3. `03_figure_2_degree_vs_reviews.ipynb` creates Figure 2.
4. `04_centrality_models.ipynb` creates the models reported in Supplementary Tables S3 and S4.
5. `05_prescription_neighborhoods.ipynb` creates the within category and cross category tie summaries reported in the Results.
6. `06_supplementary_market_figures.ipynb` creates Supplementary Figures S1 and S2.

Two supporting scripts reproduce the remaining reported results:

```bash
python scripts/01_degree_preserving_null.py --randomizations 5000
python scripts/02_vendor_portfolio_overlap.py
```

The first script creates the degree preserving bipartite null reported in Supplementary Table S2. The second creates the prescription vendor overlap counts reported in the Results.

## License

The code is released under the MIT License. The data distributed through Zenodo are governed by the terms stated in that record.
