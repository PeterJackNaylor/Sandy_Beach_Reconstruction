# Sandy Beach Reconstruction — 4D INR for Topographic Monitoring

Code for the paper:

> **Spatiotemporal reconstruction of 4D point clouds at different time scales through implicit neural representations for topographic monitoring applications**  
> Letard, M.; Naylor, P.; Anders, K. — *ISPRS Annals*, Track TC2: Photogrammetry (Full Paper)

This repository trains and evaluates Implicit Neural Representations (INRs) on time series of Terrestrial Laser Scanning (TLS) point clouds of a coastal sandy beach. The network learns a continuous mapping *(t, x, y) → z* (elevation), enabling 4D surface reconstruction, temporal gap-filling, and super-resolution from sparse, irregular acquisitions.

---

## Overview

A sandy beach is surveyed repeatedly with a TLS at different timescales (daily to seasonal). Each acquisition produces a dense 3D point cloud. Rather than storing discrete snapshots, we fit an INR (a small MLP) that represents the entire spatio-temporal surface implicitly. This allows:

- **Reconstruction** at any (t, x, y) query, including unobserved times
- **Temporal gap-filling** between acquisitions
- **Super-resolution** in time and space
- **Gradient analysis**: the reconstructed surfaces can be used for further analysis of spatial slopes and rates of surface change over time

Multiple architectures are compared (RFF, RFF_st, SIREN, KAN) across four temporal resolutions (daily, weekly, monthly, seasonal).

Data source: Vos et al. (2023); https://data.4tu.nl/datasets/1aac46fb-7900-4d4c-a099-d2ce354811d2/2

---

## Repository Structure

```
Sandy_Beach_Reconstruction/
├── main.nf              # Nextflow workflow: runs all model × dataset combinations
├── nextflow.config      # Cluster (PBS) and conda environment configuration
├── mathilda.yml         # Hyperparameter configuration
├── Makefile             # Shortcut: `make sand` runs the full pipeline
├── requirements.txt     # Python dependencies
├── src/
│   ├── single_run.py    # Entry point: Optuna HPO + training + evaluation
│   ├── dataloader.py    # Data loading and normalisation (TLaLoZC dataset)
│   ├── evaluations.py   # MAE/RMSE metrics, time-series plots, change analysis
│   ├── pde_model.py     # Gradient loss terms (spatial + temporal regularization)
│   ├── temp_encoding.py # Multi-scale temporal encoding
│   ├── bilinear.py      # Bilinear interpolation baseline
│   ├── data_script.py   # Preprocessing: LAS → .npy train/val/test splits
│   ├── pc_utils.py      # Point cloud utilities (roughness, downsampling)
│   └── plot_utils.py    # Visualisation helpers
└── INR4torch/           # Submodule: PyTorch PINN framework (models, training loop)
    └── pinns/
        ├── models.py           # Architecture factory (SIREN, RFF, WIRE, MFN, KAN)
        ├── density_estimation.py # Training engine with adaptive loss balancing
        ├── diff_operators.py   # Automatic differentiation utilities
        └── ...
```

---

## Models

| Name | Description |
|------|-------------|
| `RFF` | Random Fourier Features (Tancik et al., 2020) |
| `RFF_st` | RFF with separate spatial and temporal encodings |
| `SIREN` | Sinusoidal Representation Networks (Sitzmann et al., 2020) |
| `WIRE` | Wavelet-based INR with complex Gabor activations (Saragadam et al., 2023) |
| `MFN` | Multiplicative Filter Networks (Fathony et al., 2021) |
| `KAN` | Kolmogorov-Arnold Networks (Liu et al., 2024) |

---

## Data Format

Input data are `.npy` arrays of shape `(N, D)` where each row is a point:

| Columns | Description |
|---------|-------------|
| `[0]` | Days since reference date |
| `[1–10]` | Temporal encodings (sin/cos of hour, month, year, Julian date; log time deltas) |
| `[11]` | X / Easting |
| `[12]` | Y / Northing |
| `[13]` | Z / Elevation |

A companion index array labels each point as train (0), validation (1), or test (2).

Raw LAS files are preprocessed into this format using `src/data_script.py`.

---

## Installation

```bash
# Clone with submodule
git clone --recurse-submodules <repo-url>
cd Sandy_Beach_Reconstruction

# Create conda environment
conda env create -f INR4torch/environment.yml   # or use requirements.txt
conda activate inr4torch

pip install -r requirements.txt
```

**Key dependencies:** PyTorch ≥ 2.4, Optuna, py4dgeo, laspy, open3d, astropy

---

## Usage

### Full pipeline (HPC / Nextflow)

Runs 8 datasets × 4 models = 32 jobs in parallel on a PBS cluster:

```bash
make sand
# or
nextflow run main.nf -resume -profile Jupyter \
  -w /path/to/nextflow_work
```

### Single experiment

```bash
python src/single_run.py \
  --name daily_beach_temporal_RFF \
  --model_name RFF \
  --keyword daily_beach_temporal \
  --yaml_file mathilda.yml
```

By default this runs Optuna hyperparameter optimisation (200 trials). To train with fixed config, call `main_sr()` instead.

### Configuration

Edit `mathilda.yml` to adjust:

- **Architecture**: `model_name`, `hidden_layers`, `hidden_width`, `mapping_size`
- **Training**: `epochs`, `batch_size`, `lr`, `lr_decay`
- **Loss weights**: `lambda` values for `gradient_lat`, `gradient_lon`, `gradient_time`
- **Regularisation**: adaptive loss balancing (`loss_balancing`), temporal causality weighting (`causal_weight`)

---

## Outputs

Each run produces a directory `{keyword}_{model}/` containing:

```
├── used_config.yml          # Exact config used
├── *.pth / *.npz            # Best model weights and normalisation stats
├── results.csv              # MAE / RMSE on train, val, test
├── plots/                   # Loss curves and learning rate schedule
├── pc_train|validation|test/# 3D point cloud visualisations + error histograms
├── optuna/                  # Hyperparameter search diagnostics
├── multiple/                # Weights for all Optuna trials (ensemble)
├── temp_super_res/          # Temporal super-resolution plots
├── temp_gap_filling/        # Gap-filling capability visualisation
└── time_series_eval/        # Time series at sampled spatial locations
```

Results across all runs are aggregated into a single `results.csv` by `aggregate.py`.

---

## License

GPL-3.0 — see [LICENSE](LICENSE).

---

## Citation

```bibtex
@article{letard2026spatiotemporal,
  title     = {Spatiotemporal reconstruction of {4D} point clouds at different time scales
               through implicit neural representations for topographic monitoring applications},
  author    = {Letard, Mathilde and Naylor, Peter and Anders, Katharina},
  journal   = {ISPRS Annals of the Photogrammetry, Remote Sensing
               and Spatial Information Sciences},
  year      = {2026},
  note      = {Track TC2: Photogrammetry, Full Paper, Contribution ID 760}
}
```
