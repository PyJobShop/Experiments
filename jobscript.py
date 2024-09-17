"""
One-off script for submitting a bunch of jobs to a SLURM cluster.

Specifically, one job is submitted for each (problem, solver, time_limit)
combination by executing the ``benchmark.py`` script.
"""

from read import ProblemVariant
from pathlib import Path
import argparse
from itertools import product
from subprocess import run

JOBSCRIPT = """#!/bin/sh
#SBATCH --job-name={job_name}
#SBATCH --time={job_time_limit}
#SBATCH --nodes=1
#SBATCH --partition=rome
#SBATCH --array=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task={job_cpus_per_task}
#SBATCH --mail-type=FAIL,END
#SBATCH --mail-user=l.lan@vu.nl
#SBATCH --out=slurm/{job_name}-%A_%a.out
#SBATCH --mem-per-cpu=2G

uv run benchmark.py \
data/instances/{problem}/*.txt \
--problem_variant {problem} \
--sol_dir {out_dir} \
--time_limit {time_limit} \
--num_workers_per_instance {num_workers_per_instance} \
--num_parallel_instances {num_parallel_instances} \
--solver {solver} \
--permutation_max_jobs {permutation_max_jobs}  >>> {out_dir}/results.txt
"""

NUM_CORES = 128
NUM_WORKERS_PER_INSTANCE = 8
NUM_PARALLEL_INSTANCES = 16
DATA_DIR = Path("data/instances")

SOLVERS = ["ortools", "cpoptimizer"]
TIME_LIMITS = [120, 900]  # 2 min, 15 min
PERMUTATION_MAX_JOBS = 200


def seconds2string(seconds: int) -> str:
    mins, seconds = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    return f"{hours:02d}:{mins:02d}:{seconds:02d}"


def main(mock: bool):
    for solver, time_limit, problem_variant in product(
        SOLVERS, TIME_LIMITS, ProblemVariant
    ):
        instance_dir = DATA_DIR / problem_variant
        num_instances = len(list(instance_dir.glob("*.txt")))
        job_name = f"{problem_variant}-{solver}-{time_limit}"
        _total_time = (num_instances / NUM_PARALLEL_INSTANCES) * time_limit
        job_time_limit = seconds2string(int(_total_time + 3600))  # 3600s buffer
        out_dir = f"data/results/{problem_variant}/{solver}/{time_limit}"
        maybe_mkdir(out_dir)

        jobscript = JOBSCRIPT.format(
            job_name=job_name,
            job_cpus_per_task=NUM_CORES,
            job_time_limit=job_time_limit,
            problem=problem_variant,
            solver=solver,
            time_limit=time_limit,
            num_workers_per_instance=NUM_WORKERS_PER_INSTANCE,
            num_parallel_instances=NUM_PARALLEL_INSTANCES,
            permutation_max_jobs=PERMUTATION_MAX_JOBS,
            out_dir=out_dir,
        )

        if mock:
            print(jobscript)
        else:
            run(["sbatch"], input=jobscript.encode())


def parse_args():
    parser = argparse.ArgumentParser(prog="batch")
    parser.add_argument("--mock", action="store_true")

    return parser.parse_args()


def maybe_mkdir(where: str):
    if where:
        dir_loc = Path(where)
        dir_loc.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main(parse_args().mock)
