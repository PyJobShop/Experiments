# Experiments

This repository contains experimental code and data for the paper submission related to **PyJobShop**.

## Installation

Before using this repository, ensure you have the following installed:
- [uv](https://docs.astral.sh/uv/) (version **0.5.4** or higher)
- CP Optimizer (version **22.1.1.0** or higher)

Install PyJobShop and all required packages by running:

```sh
uv sync
```

This command installs PyJobShop at commit [3ad1a02](https://github.com/PyJobShop/PyJobShop/commit/3ad1a02920a285c431e80786388facfa87affc52), which has been modified to support permutation constraints.
See [this](https://github.com/PyJobShop/Experiments/tree/permutation) branch for more details.

## Repository structure

The repository is organized as follows.

The `data`/ directory 
- **`bks/`**: Contains all best-known solutions.
- **`instances/`**: Contains all problem instances.
- **`results/`**: Contains all raw benchmark results (including full solutions).
  *Note: This folder is not included in the repository but can be downloaded separately from Zenodo.*
- **`bks.csv`**: Parsed best-known solutions for result analysis.
- **`stats.csv`**: Parsed instance data for result analysis.
- **`results.csv`**: Comprehensive CSV overview of all results.

The `notebooks/` directory
- **`parse_bks.ipynb`**: Notebook for parsing best-known solutions.
- **`parse_results.ipynb`**: Notebook for parsing benchmark results.
- **`analysis.ipynb`**: Notebook for performing results analysis.

Additional utilities
- **`read/read.py`**: Helper functions to read various instance formats.
- **`benchmark.py`**: Script for running benchmarks.

## Reproducing results

To reproduce all benchmark results (i.e., the `data/results/` folder), use the `benchmark.py` script which interfaces with the data. For example, to solve all FJSP instances using OR-Tools with a 10-second time limit and 8 cores per instance, run:

```sh
uv run benchmark.py data/instances/FJSP/*.txt \
  --problem_variant FJSP \
  --solver ortools \
  --time_limit 10 \
  --num_workers_per_instance 8 \
  --display
```

For more configuration options, you can view the help documentation:

```sh
uv run benchmark.py --help
```

## SLURM job script

For running all experiments on a SLURM cluster, use the `jobscript.py` file. This script submits independent SLURM jobs, each running the `benchmark.py` script for a specific problem variant. *Note: This script is tailored to our cluster hardware, so adjustments may be required for your system.*

I run the following commands:

```sh
uv run jobscript.py --solver ortools --time_limit 900
uv run jobscript.py --solver cpoptimizer --time_limit 900
```

## Post-processing results

After running the experiments, execute the following scripts to generate parsed files for data analysis:
- `notebooks/parse_bks.py`
- `notebooks/parse_results.py`
- `parse_stats.py`

## Other

- **`fjsp_naderi.py`**: Replicates the FJSP model from Naderi et al. (2023).
