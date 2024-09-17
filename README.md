# Experiments

This directory contains all numerical experiments for PyJobShop's paper.

Experiments related to machine scheduling can be found in the `machine/` folder and experiments related to project scheduling can be found in the `project/` folder.


``` python
# PROBLEM=Flexiblejobshop # done
# PROBLEM=Flowshop 
# PROBLEM=Hybridflowshop # done
# PROBLEM=Jobshop # done
# PROBLEM=Non-Flowshop # TODO
# PROBLEM=Nowaitflowshop # TODO 800 very large causes problem
# PROBLEM=Parallelmachine # done, extremely high gaps
# PROBLEM=Setupflowshop # done, only n<=200
# PROBLEM=TCTflowshop # done, only n<=200
# PROBLEM=Tardinessflowshop # done, only n<=200
# PROBLEM=RCPSP
# PROBLEM=MMRCPSP
PROBLEM=RCMPSP
SOLVER="ortools"
TIME_LIMIT=50
uv run benchmark.py \
data/instances/$PROBLEM/*.txt \
--problem_variant $PROBLEM \
--sol_dir data/results/$PROBLEM/$SOLVER/$TIME_LIMIT \
--time_limit $TIME_LIMIT \
--num_workers_per_instance 1 \
--num_parallel_instances 10 \
--solver $SOLVER \
--permutation_max_jobs 100

```

``` sh
PROBLEMS=(
#"Flexiblejobshop"
#"Jobshop"
#"Hybridflowshop"
#"Non-Flowshop"
"Nowaitflowshop"
#"Flowshop" 
#"Setupflowshop"
#"TCTflowshop"
#"Tardinessflowshop"
#"RCPSP"
#"MMRCPSP"
#"RCMPSP"
)

for PROBLEM in "${PROBLEMS[@]}"; do
    # Execute the uv run benchmark.py command for each problem
    uv run benchmark.py \
    data/instances/$PROBLEM/360.txt \
    --problem_variant $PROBLEM \
    --sol_dir data/results/$PROBLEM/$SOLVER/$TIME_LIMIT \
    --time_limit $TIME_LIMIT \
    --num_workers_per_instance 1 \
    --num_parallel_instances 1 \
    --solver $SOLVER \
    --config_loc configs/$SOLVER/first_feasible.toml \
    --permutation_max_jobs 100 
done

```

`
