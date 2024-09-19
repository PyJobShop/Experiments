from pathlib import Path
from .Problem import ProblemVariant
from .machine import MachineInstance
from .project import ProjectInstance

from pyjobshop import ProblemData


def read(loc: Path, problem: ProblemVariant) -> ProblemData:
    """
    Reads a problem instance from file and returns a ProblemData instance.
    """
    parse_methods = {
        ProblemVariant.JSP: MachineInstance.parse_jsp,
        ProblemVariant.FJSP: MachineInstance.parse_fjsp,
        ProblemVariant.PMP: MachineInstance.parse_pmp,
        ProblemVariant.HFSP: MachineInstance.parse_hfsp,
        ProblemVariant.NPFSP: MachineInstance.parse_npfsp,
        ProblemVariant.NW_PFSP: MachineInstance.parse_nw_pfsp,
        # Permutation machine scheduling
        ProblemVariant.PFSP: MachineInstance.parse_pfsp,
        ProblemVariant.SDST_PFSP: MachineInstance.parse_sdst_pfsp,
        ProblemVariant.TCT_PFSP: MachineInstance.parse_tct_pfsp,
        ProblemVariant.TT_PFSP: MachineInstance.parse_tt_pfsp,
        # Project scheduling problems have instance-format specific parsers.
        ProblemVariant.RCPSP: ProjectInstance.parse_patterson,
        ProblemVariant.MMRCPSP: ProjectInstance.parse_psplib,
        ProblemVariant.RCMPSP: ProjectInstance.parse_mplib,
    }

    parse_method = parse_methods.get(problem)
    if parse_method is None:
        raise ValueError(f"Unsupported problem type: {problem}")

    instance = parse_method(loc)
    return instance.data()
