# Experiments

This directory contains all numerical experiments for PyJobShop's paper.

## Installation

PyJobShop version v0.0.3a at commit [beabeed](https://github.com/PyJobShop/PyJobShop/commit/beabeedd76fe7a82889dd94b72d8a1d2f1ae14b6) modified to support permutation constraints.


``` sh
uv sync
```

## Data
Data in `data/`.
- Instances
- Results

## Reproduce all benchmark results
- `benchmark.py` script interfaces with data

## Slurm
- `jobscript.py`


## Notebooks and analysis
- Found in `notebooks/`


``` sh
SOLVERS=(
"ortools"
"cpoptimizer"
)
PROBLEMS=(
"JSP"
"FJSP"
"NPFSP"
"NW-PFSP"
"PFSP"
"SDST-PFSP"
"TCT-PFSP"
"TT-PFSP"
"RCPSP"
"MMRCPSP"
"RCMPSP"
)
TIME_LIMIT=60

for SOLVER in "${SOLVERS[@]}"; do
    for PROBLEM in "${PROBLEMS[@]}"; do
        # Execute the uv run benchmark.py command for each problem
        uv run benchmark.py \
        data/instances/$PROBLEM/*.txt \
        --problem_variant $PROBLEM \
        --sol_dir tmp/data/results/$PROBLEM/$SOLVER/$TIME_LIMIT \
        --time_limit $TIME_LIMIT \
        --num_workers_per_instance 1 \
        --num_parallel_instances 10 \
        --solver $SOLVER \
        --config_loc configs/$SOLVER/first_feasible.toml \
        --permutation_max_jobs 50
    done
done
```


## Other
- `fjsp_naderi.py` replicates the FJSP model from Naderi et al. (2023)
