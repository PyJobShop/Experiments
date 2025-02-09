"""
One-off script to obtain instance statistics.
"""
import os
import sys
from pathlib import Path
import tqdm as tqdm

import pandas as pd
from tqdm.contrib.concurrent import process_map

from read import read, ProblemVariant

sys.path.append(os.path.abspath("read"))


def get_instance_stats(loc: Path):
    """
    Returns statistics about the instance.
    """
    problem = loc.parents[0].name  # bit hacky, but data is organized in this way
    data = read(loc, problem)
    return data.num_modes, data.num_resources, data.num_tasks


def main():
    data = []
    instances = [
        loc
        for problem in ProblemVariant
        for loc in (Path("data/instances") / problem.value).glob("*.txt")
    ]
    results = process_map(
        get_instance_stats,
        instances,
        max_workers=8,
        chunksize=10,
    )

    for loc, res in zip(instances, results):
        problem = loc.parents[0].name
        data.append([problem, loc.name, *res])

    columns = ["problem", "instance", "num_modes", "num_resources", "num_tasks"]
    df = pd.DataFrame(data, columns=columns)
    df = df.sort_values(["problem", "instance"])

    out_loc = "data/stats.csv"
    df.to_csv(out_loc, index=False)


if __name__ == "__main__":
    main()
