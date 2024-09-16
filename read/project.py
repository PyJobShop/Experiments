from dataclasses import dataclass

from pathlib import Path
from typing import Union

import re
from pathlib import Path
from typing import Union

from pyjobshop import ProblemData, Model


@dataclass
class Resource:
    """
    Resource class.

    Parameters
    ----------
    capacity
        The available maximum capacity of the resource.
    renewable
        Whether the resource is renewable or not.
    """

    capacity: int
    renewable: bool


@dataclass
class Mode:
    """
    Mode class.

    Parameters
    ----------
    duration
        The duration of this processing mode.
    demands
        The resource demands (one per resource) of this processing mode.
    """

    duration: int
    demands: list[int]


@dataclass
class Activity:
    """
    Activity class.

    Parameters
    ----------
    modes
        The processing modes of this activity.
    successors
        The indices of successor activities.
    name
        Optional name of the activity to identify this activity. This is
        helpful to map this activity back to the original problem instance.
    """

    modes: list[Mode]
    successors: list[int]
    name: str = ""

    @property
    def num_modes(self):
        return len(self.modes)


@dataclass
class Project:
    """
    Project class.

    Parameters
    ----------
    activities
        The activities indices that belong to this project.
    release_date
        The earliest start time of this project.
    """

    activities: list[int]
    release_date: int = 0

    @property
    def num_activities(self):
        return len(self.activities)


@dataclass
class ProjectInstance:
    """
    Multi-project multi-mode resource-constrained project scheduling instance.
    """

    resources: list[Resource]
    projects: list[Project]
    activities: list[Activity]

    @property
    def num_resources(self):
        return len(self.resources)

    @property
    def num_projects(self):
        return len(self.projects)

    @property
    def num_activities(self):
        return len(self.activities)

    def data(self) -> ProblemData:
        """
        Converts the instance to a ProblemData object.
        """
        model = Model()

        resources = [
            model.add_resource(capacity=res.capacity, renewable=res.renewable)
            for res in self.resources
        ]

        for project in self.projects:
            job = model.add_job(release_date=project.release_date)

            for _ in project.activities:
                model.add_task(job=job)

        for idx, activity in enumerate(self.activities):
            for mode in activity.modes:
                model.add_mode(
                    task=model.tasks[idx],
                    resources=resources,
                    duration=mode.duration,
                    demands=mode.demands,
                )

        for idx, activity in enumerate(self.activities):
            for succ in activity.successors:
                model.add_end_before_start(model.tasks[idx], model.tasks[succ])

        return model.data()

    @classmethod
    def parse_mplib(cls, loc: Union[str, Path]):
        """
        Parses a multi-project resource-constrained project scheduling problem
        instances from MPLIB.

        Parameters
        ----------
        loc
            The location of the instance.

        Returns
        -------
        Instance
            The parsed instance.
        """
        with open(loc, "r") as fh:
            # Strip all lines and ignore all empty lines.
            lines = iter(line.strip() for line in fh.readlines() if line.strip())

        num_projects = int(next(lines))
        num_resources = int(next(lines))

        capacities = list(map(int, next(lines).split()))
        resources = [Resource(capacity=cap, renewable=True) for cap in capacities]

        projects: list[Project] = []
        activities: list[Activity] = []
        id2idx: dict[str, int] = {}  # maps activity names to idcs

        for project_idx in range(1, num_projects + 1):
            num_activities, release_date = map(int, next(lines).split())
            next(lines)  # denotes used resources, implies that demand > 0

            idcs = [len(activities) + idx for idx in range(num_activities)]
            projects.append(Project(idcs, release_date))

            for activity_idx in range(1, num_activities + 1):
                line = next(lines).split()
                idx = num_resources + 2
                duration, *demands, num_successors = list(map(int, line[:idx]))
                successors = line[idx:]
                assert len(successors) == num_successors

                mode = Mode(duration, demands)
                name = f"{project_idx}:{activity_idx}"  # original activity id
                id2idx[name] = len(activities)
                activities.append(Activity([mode], successors, name))  # type: ignore

        for activity in activities:
            # Map the successors ids from {project_idx:activity_idx}, to the
            # specific activitiy indices.
            idcs = [id2idx[succ] for succ in activity.successors]  # type: ignore
            activity.successors = idcs

        return cls(resources, projects, activities)

    @classmethod
    def parse_patterson(cls, loc: Union[str, Path]):
        """
        Parses a Patterson-formatted instance. This format is used for pure
        resource-constrained project scheduling problem (RCPSP) instances.

        Parameters
        ----------
        loc
            The location of the instance.

        Returns
        -------
        ProjectInstance
            The parsed project instance.
        """
        with open(loc, "r") as fh:
            # Strip all lines and ignore all empty lines.
            lines = iter(line.strip() for line in fh.readlines() if line.strip())

        num_activities, num_resources = map(int, next(lines).split())

        # Instances without resources do not have an availability line.
        capacities = list(map(int, next(lines).split())) if num_resources else []
        resources = [Resource(capacity=cap, renewable=True) for cap in capacities]

        # Most instances are not nicely formatted since a single activity data
        # may be split over multiple lines. The way to deal with this is to iterate
        # over all values instead of parsing line-by-line.
        values = iter([val for line in lines for val in line.split()])
        activities = []

        for _ in range(num_activities):
            duration = int(next(values))
            demands = [int(next(values)) for _ in range(num_resources)]
            num_successors = int(next(values))
            successors = [int(next(values)) - 1 for _ in range(num_successors)]
            activities.append(Activity([Mode(duration, demands)], successors))

        project = Project(list(range(num_activities)))  # only one project
        return cls(resources, [project], activities)

    @classmethod
    def parse_psplib(cls, loc: Union[str, Path]):
        """
        Parses an PSPLIB-formatted instance from a file.

        Parameters
        ----------
        loc
            The location of the instance.

        Returns
        -------
        Instance
            The parsed instance.
        """
        with open(loc) as fh:
            lines = [line.strip() for line in fh.readlines() if line.strip()]

        prec_idx = _find(lines, "PRECEDENCE RELATIONS")
        req_idx = _find(lines, "REQUESTS/DURATIONS")
        avail_idx = _find(lines, "AVAILABILITIES")

        capacities = list(map(int, re.split(r"\s+", lines[avail_idx + 2])))
        renewable = [
            char == "R"
            for char in lines[avail_idx + 1].strip().split()
            if char in ["R", "N"]  # R: renewable, N: non-renewable
        ]
        resources = [
            Resource(capacity, is_renewable)
            for capacity, is_renewable in zip(capacities, renewable)
        ]
        num_resources = len(resources)

        mode_data = [
            list(map(int, re.split(r"\s+", line)))
            for line in lines[req_idx + 3 : avail_idx - 1]
        ]

        mode_idx = 0
        activities = []
        for line in lines[prec_idx + 2 : req_idx - 1]:
            _, num_modes, _, *jobs = list(map(int, re.split(r"\s+", line)))
            successors = [val - 1 for val in jobs if val]

            modes = []
            for idx in range(mode_idx, mode_idx + num_modes):
                # Mode data is parsed starting from the end of the line because
                # the data is ragged as some lines do not contain job indices.
                duration = mode_data[idx][-num_resources - 1]
                demands = mode_data[idx][-num_resources:]
                modes.append(Mode(duration, demands))
                mode_idx += 1

            activities.append(Activity(modes, successors))

        idcs = list(range(len(activities)))
        project = Project(idcs)  # only one project with all activities

        return cls(resources, [project], activities)


def _find(lines: list[str], pattern: str) -> int:
    for idx, line in enumerate(lines):
        if pattern in line:
            return idx

    raise ValueError(f"Pattern '{pattern}' not found in lines.")
