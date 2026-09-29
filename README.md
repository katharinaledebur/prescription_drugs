# Prescription drugs at the core of darknet drug markets

This repository contains the analysis code accompanying the study:

**“Prescription drugs at the core of darknet drug markets”**

The analyses examine the position of prescription drugs within darknet drug retail using product co-offering networks, vendor portfolios, market-level category structure, shipping reach, and null-model comparisons across four darknet markets crawled between June 2021 and January 2022.

## Repository structure

```text
.
├── CITATION.cff
├── LICENSE
├── README.md
├── requirements.txt
├── notebooks/
├── scripts/
├── prescription_reports/
```
`notebooks/` contains analysis notebooks and supporting exploratory analyses.

`scripts/` contains reusable analysis and data-processing scripts.

`prescription_reports/` contains files used to generate analysis reports and manuscript-related outputs.

`data_outputs/` contains locally generated analysis outputs. Publicly released derived data are archived separately on Zenodo.

`requirements.txt` specifies the Python dependencies used for the analyses.

`CITATION.cff` contains citation metadata for this repository.


Clone the repository:

    git clone https://github.com/katharinaledebur/prescription_drugs.git
    cd prescription_drugs

Create a Python environment and install the required packages:

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

Download the corresponding derived dataset from Zenodo:

https://doi.org/10.5281/zenodo.23037050

The Zenodo archive contains the data products required to reproduce the publicly reported figures and statistical results.


## Citation

If you use the derived dataset, please cite the Zenodo record:

Ledebur, K., Frank, R., & Haslhofer, B.  
**Data supporting “Prescription drugs at the core of darknet drug markets”.**  
Zenodo.  
https://doi.org/10.5281/zenodo.23037050

Citation information for the code repository is also provided in `CITATION.cff`.

## License

The code in this repository is released under the MIT License.

The derived dataset archived on Zenodo is released separately under CC BY 4.0.
