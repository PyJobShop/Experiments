"""
One-off script to solve FJSP instances using Naderi's OR-Tools model
and benchmark the results.

Usage:

```
uv run fjsp_naderi.py \
--time_limit 900 \
--num_parallel_instances 8 \
--num_workers 8 >>> results.txt
```
"""
from dataclasses import dataclass
from pathlib import Path
from functools import partial
from collections import namedtuple, defaultdict
from itertools import product
from argparse import ArgumentParser

from ortools.sat.python.cp_model import CpModel, CpSolver
from read.machine import MachineInstance
from tqdm.contrib.concurrent import process_map
import numpy as np


@dataclass
class Instance:
    num_jobs: int
    num_machines: int
    num_tasks_by_job: list[int]
    durations: list[list[list[int]]]


def fjsp_naderi(instance: Instance):
    """
    Refactored FJSP model from Naderi et al. (2023).

    Parameters
    ----------
    instance
        The instance to solve.

    Returns
    -------
    objective
        The objective value of the solution.
    """
    model = CpModel()
    horizon = 100000
    interval_type = namedtuple("task_type", "start end is_present interval")

    mode_vars = {}
    machine_to_intervals = defaultdict(list)
    job_task_to_interval = [defaultdict(list) for _ in range(instance.num_jobs)]

    for job in range(instance.num_jobs):
        num_tasks = instance.num_tasks_by_job[job]

        for task in range(num_tasks):
            for machine in range(instance.num_machines):
                duration = instance.durations[job][task][machine]
                if duration == 0:
                    continue

                suffix = f"_{job}_%{task}_%{machine}"
                start = model.new_int_var(0, horizon, "start" + suffix)
                end = model.new_int_var(0, horizon, "end" + suffix)
                is_present = model.new_bool_var("is_present" + suffix)
                interval = model.new_optional_interval_var(
                    start, duration, end, is_present, "interval" + suffix
                )

                mode_vars[job, task, machine] = interval_type(
                    start=start,
                    end=end,
                    is_present=is_present,
                    interval=interval,
                )
                machine_to_intervals[machine].append(interval)
                job_task_to_interval[job][task].append(interval)

    # No overlap on machines
    for machine in range(instance.num_machines):
        model.add_no_overlap(machine_to_intervals[machine])

    # Select one mode per task
    for job in range(instance.num_jobs):
        for task in range(instance.num_tasks_by_job[job]):
            mode_presence = [
                mode_vars[job, task, machine].is_present
                for machine in range(instance.num_machines)
                if instance.durations[job][task][machine] > 0
            ]
            model.add(sum(mode_presence) == 1)

    # Precedence constraint (linear routing)
    for job in range(instance.num_jobs):
        num_tasks = instance.num_tasks_by_job[job]

        for task in range(num_tasks - 1):
            for m1, m2 in product(range(instance.num_machines), repeat=2):
                duration_pred = instance.durations[job][task][m1]
                duration_succ = instance.durations[job][task + 1][m2]

                if duration_pred > 0 and duration_succ > 0:
                    # Only add precedence between (pred, succ) if they actual modes.
                    pred = mode_vars[job, task, m1]
                    succ = mode_vars[job, task + 1, m2]
                    model.add(pred.end >= succ.start)

    # Minimizing makespan objective
    makespan = model.new_int_var(0, horizon, "makespan")
    last_tasks = []

    for job in range(instance.num_jobs):
        for machine in range(instance.num_machines):
            last = instance.num_tasks_by_job[job] - 1
            duration = instance.durations[job][last][machine]

            if duration > 0:
                last_tasks.append(mode_vars[job, last, machine].end)

    model.add_max_equality(makespan, last_tasks)
    model.minimize(makespan)

    return model


def _read(instance_loc):
    """
    Reads the instance file and returns an instance object.
    """
    data = MachineInstance.parse_fjsp(instance_loc)

    num_jobs = data.num_jobs
    num_machines = data.num_machines
    num_tasks_by_job = [len(tasks) for tasks in data.jobs]
    durations = np.zeros((num_jobs, max(num_tasks_by_job), num_machines), dtype=int)

    for job_idx, tasks in enumerate(data.jobs):
        for task_idx, task in enumerate(tasks):
            for mach_idx, duration in task:
                durations[job_idx, task_idx, mach_idx] = duration

    return Instance(
        num_jobs=num_jobs,
        num_machines=num_machines,
        num_tasks_by_job=num_tasks_by_job,
        durations=durations,
    )


def solve(instance_loc: Path, time_limit: int, display: bool, num_workers: int):
    """
    Solves an FJSP instance using Naderi's OR-Tools model.
    """
    instance = _read(instance_loc)
    model = fjsp_naderi(instance)

    cp_solver = CpSolver()
    params = {
        "max_time_in_seconds": time_limit,
        "log_search_progress": display,
        # 0 means using all available CPU cores.
        "num_workers": num_workers if num_workers is not None else 0,
    }

    for key, value in params.items():
        setattr(cp_solver.parameters, key, value)

    status_code = cp_solver.solve(model)
    status = cp_solver.status_name(status_code)
    status = status.capitalize()
    objective_value = cp_solver.objective_value

    return instance_loc.name, status, objective_value, round(cp_solver.wall_time, 3)


def benchmark(instances: list[Path], num_parallel_instances: int, **kwargs):
    """
    Solves the list of instances and prints a table of the results.
    """
    args = sorted(instances)
    func = partial(solve, **kwargs)

    if len(instances) == 1:
        results = [func(args[0])]
    else:
        results = process_map(
            func,
            args,
            max_workers=num_parallel_instances,
            unit="instance",
        )

    results = [res for res in results if res is not None]

    dtypes = [
        ("inst", "U37"),
        ("feas", "U37"),
        ("obj", float),
        ("time", float),
    ]
    data = np.asarray(results, dtype=dtypes)
    headers = ["Instance", "Status", "Obj.", "Time (s)"]

    avg_objective = data["obj"].mean()
    avg_runtime = data["time"].mean()
    num_optimal = np.count_nonzero(data["feas"] == "Optimal")
    num_feas = np.count_nonzero(data["feas"] == "Feasible") + num_optimal
    num_infeas = np.count_nonzero(data["feas"].size - num_feas)

    print("\n", tabulate(headers, data), "\n", sep="")
    print(f"     Avg. objective: {avg_objective:.2f}")
    print(f"      Avg. run-time: {avg_runtime:.2f}s")
    print(f"      Total optimal: {num_optimal}")
    print(f"       Total infeas: {num_infeas}")


def tabulate(headers: list[str], rows: np.ndarray) -> str:
    """
    Creates a simple table from the given header and row data.
    """
    # These lengths are used to space each column properly.
    lens = [len(header) for header in headers]

    for row in rows:
        for idx, cell in enumerate(row):
            lens[idx] = max(lens[idx], len(str(cell)))

    header = [
        "  ".join(f"{hdr:<{ln}s}" for ln, hdr in zip(lens, headers)),
        "  ".join("-" * ln for ln in lens),
    ]

    content = ["  ".join(f"{c!s:>{ln}s}" for ln, c in zip(lens, r)) for r in rows]

    return "\n".join(header + content)


def parse_args():
    parser = ArgumentParser()

    parser.add_argument(
        "--time_limit",
        type=int,
        default=900,
        help="Time limit for the solver.",
    )
    parser.add_argument(
        "--num_parallel_instances",
        type=int,
        default=25,
        help="Number of instances to solve in parallel.",
    )
    parser.add_argument(
        "--num_workers",
        type=int,
        default=8,
        help="Number of workers to use in parallel processing.",
    )
    parser.add_argument(
        "--display",
        action="store_true",
        help="Whether to display the solver output.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    INSTANCE_DIR = Path("data/instances/FJSP")
    instances = list(INSTANCE_DIR.glob("*.txt"))

    benchmark(instances, **vars(parse_args()))
