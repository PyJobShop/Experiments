from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from pyjobshop import Model, ProblemData
from itertools import product


def _read(loc: Path):
    with open(loc) as fh:
        data = [list(map(int, line.strip().split())) for line in fh]

    return iter(data)


TaskData = list[tuple[int, int]]  # machine idx, duration


@dataclass
class MachineInstance:
    """
    Helper class to parse machine scheduling instance data from
    Naderi et al. (2023).
    """

    num_machines: int
    jobs: list[list[TaskData]]  # also defines precedence constraints
    permutation: bool = False
    no_wait: bool = False
    setup_times: Optional[list[list[list[int]]]] = None
    objective: str = "makespan"
    due_dates: Optional[list[int]] = None
    num_machines_per_stage: Optional[list[int]] = None

    @property
    def num_jobs(self) -> int:
        return len(self.jobs)

    @property
    def num_tasks(self) -> int:
        return sum(len(tasks) for tasks in self.jobs)

    def data(self) -> ProblemData:
        """
        Transform MachineInstance to ProblemData object.
        """
        model = Model()
        machines = [model.add_machine() for _ in range(self.num_machines)]
        model.set_permutation(self.permutation)

        job2tasks = [[] for _ in range(self.num_jobs)]
        for job_idx in range(self.num_jobs):
            due_date = self.due_dates[job_idx] if self.due_dates else None
            job = model.add_job(due_date=due_date)

            for task_data in self.jobs[job_idx]:
                task = model.add_task(job=job)
                job2tasks[job_idx].append(task)

                for mach_idx, duration in task_data:
                    model.add_processing_time(task, machines[mach_idx], duration)

            tasks = job2tasks[job_idx]
            for pred, succ in zip(tasks[:-1], tasks[1:]):
                # Assume linear routing of tasks as presented in the job data.
                if self.no_wait:
                    model.add_end_at_start(pred, succ)
                else:
                    model.add_end_before_start(pred, succ)

        if self.setup_times:
            for mach_idx in range(self.num_machines):
                for idx1, idx2 in product(range(self.num_jobs), repeat=2):
                    # For every two pair of jobs, we find the corresponding tasks which have
                    # the same machine index as the machine (because we have a flow shop).
                    task1 = job2tasks[idx1][mach_idx]
                    task2 = job2tasks[idx2][mach_idx]
                    setup_time = self.setup_times[mach_idx][idx1][idx2]
                    model.add_setup_time(machines[mach_idx], task1, task2, setup_time)

        if self.objective == "makespan":
            model.set_objective(weight_makespan=1)
        elif self.objective == "total_completion_time":
            model.set_objective(weight_total_flow_time=1)
        elif self.objective == "total_tardiness":
            model.set_objective(weight_total_tardiness=1)
        else:
            raise ValueError(f"Objective {self.objective} unknown.")

        return model.data()

    @classmethod
    def parse_fjsp(cls, loc: Path):
        lines = _read(loc)

        num_jobs = next(lines)[0]
        num_machines = next(lines)[0]
        num_tasks_per_job = next(lines)
        processing_times = [
            [next(lines) for _ in range(num_tasks)] for num_tasks in num_tasks_per_job
        ]

        jobs = [[] for _ in range(num_jobs)]
        for job_idx, num_tasks in enumerate(num_tasks_per_job):
            for task_idx in range(num_tasks):
                durations = processing_times[job_idx][task_idx]
                jobs[job_idx].append(
                    [
                        (mach_idx, duration)
                        for mach_idx, duration in enumerate(durations)
                        if duration > 0
                    ]
                )

        return MachineInstance(num_machines, jobs)

    @classmethod
    def parse_hfsp(cls, loc: Path):
        lines = _read(loc)
        num_jobs = next(lines)[0]
        _ = next(lines)
        num_machines_per_stage = next(lines)
        processing_times = [next(lines) for _ in range(num_jobs)]  # duration per stage

        stage2machines = []
        start = 0
        for stage, _num_machines in enumerate(num_machines_per_stage):
            stage2machines.append([start + idx for idx in range(_num_machines)])
            start += _num_machines

        jobs = [[] for _ in range(num_jobs)]
        for job_idx in range(num_jobs):
            durations = processing_times[job_idx]

            for stage, duration in enumerate(durations):
                tasks = [(mach_idx, duration) for mach_idx in stage2machines[stage]]
                jobs[job_idx].append(tasks)

        return MachineInstance(
            sum(num_machines_per_stage),
            jobs,
            num_machines_per_stage=num_machines_per_stage,
        )

    @classmethod
    def parse_jsp(cls, loc: Path):
        lines = _read(loc)
        num_jobs = next(lines)[0]
        num_machines = next(lines)[0]
        processing_times = [next(lines) for _ in range(num_jobs)]
        machines_idcs = [next(lines) for _ in range(num_jobs)]

        jobs = [[] for _ in range(num_jobs)]
        for job_idx in range(num_jobs):
            durations = processing_times[job_idx]
            machines = machines_idcs[job_idx]

            for mach_idx, duration in zip(machines, durations):
                jobs[job_idx].append([(mach_idx - 1, duration)])

        return MachineInstance(num_machines, jobs)

    @classmethod
    def parse_npfsp(cls, loc: Path):
        lines = _read(loc)
        num_jobs = next(lines)[0]
        num_machines = next(lines)[0]
        processing_times = [next(lines) for _ in range(num_jobs)]

        jobs = [[] for _ in range(num_jobs)]
        for job_idx in range(num_jobs):
            for mach_idx, duration in enumerate(processing_times[job_idx]):
                jobs[job_idx].append([(mach_idx, duration)])

        return MachineInstance(num_machines, jobs)

    @classmethod
    def parse_nw_pfsp(cls, loc: Path):
        instance = cls.parse_npfsp(loc)
        instance.no_wait = True
        return instance

    @classmethod
    def parse_pmp(cls, loc: Path):
        lines = _read(loc)
        num_jobs = next(lines)[0]
        num_machines = next(lines)[0]
        processing_times = [next(lines) for _ in range(num_jobs)]
        jobs = [
            [list(enumerate(processing_times[job_idx]))] for job_idx in range(num_jobs)
        ]

        return MachineInstance(num_machines, jobs)

    @classmethod
    def parse_pfsp(cls, loc: Path):
        instance = cls.parse_npfsp(loc)
        instance.permutation = True
        return instance

    @classmethod
    def parse_sdst_pfsp(cls, loc: Path):
        lines = _read(loc)
        num_jobs = next(lines)[0]
        num_machines = next(lines)[0]
        processing_times = [next(lines) for _ in range(num_jobs)]
        setup_times = [
            [next(lines) for _ in range(num_jobs)] for _ in range(num_machines)
        ]

        jobs = [[] for _ in range(num_jobs)]
        for job_idx in range(num_jobs):
            for mach_idx, duration in enumerate(processing_times[job_idx]):
                jobs[job_idx].append([(mach_idx, duration)])

        return MachineInstance(
            num_machines, jobs, permutation=True, setup_times=setup_times
        )

    @classmethod
    def parse_tct_pfsp(cls, loc: Path):
        instance = cls.parse_npfsp(loc)
        instance.permutation = True
        instance.objective = "total_completion_time"
        return instance

    @classmethod
    def parse_tt_pfsp(cls, loc: Path):
        lines = _read(loc)
        num_jobs = next(lines)[0]
        num_machines = next(lines)[0]
        due_dates = next(lines)
        processing_times = [next(lines) for _ in range(num_jobs)]

        jobs = [[] for _ in range(num_jobs)]
        for job_idx in range(num_jobs):
            for mach_idx, duration in enumerate(processing_times[job_idx]):
                jobs[job_idx].append([(mach_idx, duration)])

        return MachineInstance(
            num_machines,
            jobs,
            permutation=True,
            objective="total_tardiness",
            due_dates=due_dates,
        )
