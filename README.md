# Time and cohort analysis of publication patterns in SSH

[![DOI](https://zenodo.org/badge/149768483.svg)](https://zenodo.org/badge/latestdoi/149768483)

This repository is an accompaniment to [our article in *Frontiers in Research metrics and Analytics*](https://doi.org/10.3389/frma.2018.00038), in which we carry out a cohort analysis of publication patterns in the social sciences and humanities.

## Contents

The data can be found in directory `data`. Running the notebook `cohort-analysis.ipynb` reproduces the findings of the paper. The file `cohort.py` contains the core functions of the cohort analysis.

## Requirements

Python 3.6 is required. The following packages are used:
* pandas 0.23
* matplotlib 2.2
* seaborn 0.9

The easiest way to install all requirements is by using [Conda](https://conda.io/docs/). Run the following to create a conda environment named `cohort` that contains everything you need:

```
conda env create -f environment.yml
```
