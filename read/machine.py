from dataclasses import dataclass
from collections import defaultdict
from pathlib import Path
from typing import Iterator
from pyjobshop import Model, ProblemData
from itertools import product, pairwise


def _read(loc: Path) -> Iterator[list[int]]:
    with open(loc) as fh:
        return iter([list(map(int, line.strip().split())) for line in fh])


TaskData = list[tuple[int, int]]  # machine idx, duration


@dataclass
class MachineInstance:
    """
    Helper class to parse machine scheduling instance data from
    Naderi et al. (2023).
    """

    num_machines: int
    jobs: list[list[TaskData]]  # also defines precedence constraints
    permutation: list[tuple[int, int]] | None = None  # tuples of machine idcs
    no_wait: bool = False
    setup_times: list[list[list[int]]] | None = None
    objective: str = "makespan"
    due_dates: list[int] | None = None
    num_machines_per_stage: list[int] | None = None
    num_factories: int | None = None
    num_machines_per_factory: int | None = None

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

        job2tasks = [[] for _ in range(self.num_jobs)]
        for job_idx in range(self.num_jobs):
            due_date = self.due_dates[job_idx] if self.due_dates else None
            job = (
                # Only create explicit jobs if we don't minimize makespan.
                model.add_job(due_date=due_date)
                if self.objective != "makespan"
                else None
            )

            for task_data in self.jobs[job_idx]:
                task = model.add_task(job=job)
                job2tasks[job_idx].append(task)

                for mach_idx, duration in task_data:
                    model.add_mode(task, machines[mach_idx], duration)

            for pred, succ in pairwise(job2tasks[job_idx]):
                # Assume linear routing of tasks as presented in the job data.
                if self.no_wait:
                    model.add_end_before_start(pred, succ)  # e(pred) <= s(succ)
                    model.add_start_before_end(succ, pred)  # s(succ) <= e(pred)
                else:
                    model.add_end_before_start(pred, succ)

        if self.permutation is not None:
            for idx1, idx2 in self.permutation:
                # The tasks are the ones on the same machine index (or stage_idx
                # if we have a distributed flow shop).
                if self.num_machines_per_factory:
                    stage_idx1 = idx1 % self.num_machines_per_factory
                    stage_idx2 = idx2 % self.num_machines_per_factory
                else:
                    stage_idx1 = idx1
                    stage_idx2 = idx2

                tasks1 = [tasks[stage_idx1] for tasks in job2tasks]
                tasks2 = [tasks[stage_idx2] for tasks in job2tasks]
                machine1 = machines[idx1]
                machine2 = machines[idx2]
                print(stage_idx1, stage_idx2, idx1, idx2)
                model.add_same_sequence(machine1, machine2, tasks1, tasks2)

            # add modes
            modes_by_resource = defaultdict(list)
            for mode in model.modes:
                modes_by_resource[mode.resources[0]].append(mode)

            for idx1, idx2 in self.permutation:
                for mode1 in modes_by_resource[idx1]:
                    for mode2 in modes_by_resource[idx2]:
                        if mode1.task + 1 == mode2.task:
                            model.add_mode_dependency(mode1, [mode2])

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

        # TODO add super machine in addition?

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
        # TODO might add permutation here for CP Optimizer?
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
        instance.permutation = list(pairwise(range(instance.num_machines)))
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
            num_machines,
            jobs,
            permutation=list(pairwise(range(num_machines))),
            setup_times=setup_times,
        )

    @classmethod
    def parse_tct_pfsp(cls, loc: Path):
        instance = cls.parse_pfsp(loc)
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
            permutation=list(pairwise(range(num_machines))),
            objective="total_tardiness",
            due_dates=due_dates,
        )

    @classmethod
    def parse_dpfsp(cls, loc: Path):
        lines = _read(loc)
        num_jobs = next(lines)[0]
        num_machines_per_factory = next(lines)[0]
        num_factories = next(lines)[0]
        processing_times = [next(lines) for _ in range(num_jobs)]

        jobs = [[] for _ in range(num_jobs)]
        for job_idx in range(num_jobs):
            for stage_idx in range(num_machines_per_factory):
                # Every factory consists of `num_machines_per_stage` machines,
                # this stage index refers to the k-th machine within the factory.
                modes = []
                for factory_idx in range(num_factories):
                    machine_idx = stage_idx + factory_idx * num_machines_per_factory
                    duration = processing_times[job_idx][stage_idx]
                    modes.append((machine_idx, duration))

                jobs[job_idx].append(modes)

        permutations = []
        for factory_idx in range(num_factories):
            for idx1, idx2 in pairwise(range(num_machines_per_factory)):
                # This creates tuples for every two consecutive machines
                # per factory with the _actual_ machine index.
                base_idx = factory_idx * num_machines_per_factory
                permutations.append((base_idx + idx1, base_idx + idx2))

        return MachineInstance(
            num_machines_per_factory * num_factories,
            jobs,
            permutation=permutations,
            num_factories=num_factories,
            num_machines_per_factory=num_machines_per_factory,
        )
