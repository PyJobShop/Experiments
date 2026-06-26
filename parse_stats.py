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
from read.machine import MachineInstance

sys.path.append(os.path.abspath("read"))

# Machine-variant parsers, used to recover the true number of jobs. We cannot
# read it from ProblemData, since jobs are only created when the objective
# needs them (e.g. makespan instances report zero jobs).
MACHINE_PARSERS = {
    ProblemVariant.JSP.value: MachineInstance.parse_jsp,
    ProblemVariant.FJSP.value: MachineInstance.parse_fjsp,
    ProblemVariant.HFSP.value: MachineInstance.parse_hfsp,
    ProblemVariant.NPFSP.value: MachineInstance.parse_npfsp,
    ProblemVariant.NW_PFSP.value: MachineInstance.parse_nw_pfsp,
    ProblemVariant.PMP.value: MachineInstance.parse_pmp,
    ProblemVariant.OSP.value: MachineInstance.parse_osp,
    ProblemVariant.PFSP.value: MachineInstance.parse_pfsp,
    ProblemVariant.SDST_PFSP.value: MachineInstance.parse_sdst_pfsp,
    ProblemVariant.TCT_PFSP.value: MachineInstance.parse_tct_pfsp,
    ProblemVariant.TT_PFSP.value: MachineInstance.parse_tt_pfsp,
    ProblemVariant.DPFSP.value: MachineInstance.parse_dpfsp,
}


def get_instance_stats(loc: Path):
    """
    Returns statistics about the instance.
    """
    problem = loc.parents[0].name  # bit hacky, but data is organized in this way
    data = read(loc, problem)
    num_jobs = (
        MACHINE_PARSERS[problem](loc).num_jobs
        if problem in MACHINE_PARSERS
        else data.num_jobs
    )
    return num_jobs, data.num_machines, data.num_modes, data.num_resources, data.num_tasks


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

    columns = [
        "problem",
        "instance",
        "num_jobs",
        "num_machines",
        "num_modes",
        "num_resources",
        "num_tasks",
    ]
    df = pd.DataFrame(data, columns=columns)
    df = df.sort_values(["problem", "instance"])

    out_loc = "data/stats.csv"
    df.to_csv(out_loc, index=False)


if __name__ == "__main__":
    main()
