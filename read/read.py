from pathlib import Path
from .Problem import Problem
from .machine import MachineInstance
from .project import ProjectInstance

from pyjobshop import ProblemData


def read(loc: Path, problem: Problem) -> ProblemData:
    """
    Reads a problem instance from file and returns a ProblemData instance.
    """
    parse_methods = {
        Problem.FJSP: MachineInstance.parse_fjsp,
        Problem.HFSP: MachineInstance.parse_hfsp,
        Problem.JSP: MachineInstance.parse_jsp,
        Problem.NPFSP: MachineInstance.parse_npfsp,
        Problem.NW_PFSP: MachineInstance.parse_nw_pfsp,
        Problem.PFSP: MachineInstance.parse_pfsp,
        Problem.SDST_PFSP: MachineInstance.parse_sdst_pfsp,
        Problem.TCT_PFSP: MachineInstance.parse_tct_pfsp,
        Problem.TT_PFSP: MachineInstance.parse_tt_pfsp,
        # Project scheduling problems have instance-format specific parsers.
        Problem.RCPSP: ProjectInstance.parse_patterson,
        Problem.MMRCPSP: ProjectInstance.parse_psplib,
        Problem.RCMPSP: ProjectInstance.parse_mplib,
    }

    parse_method = parse_methods.get(problem)
    if parse_method is None:
        raise ValueError(f"Unsupported problem type: {problem}")

    instance = parse_method(loc)
    return instance.data()
