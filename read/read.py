from pathlib import Path
from .Problem import ProblemVariant
from .machine import MachineInstance
from functools import partial

from pyjobshop import ProblemData, read as _read


def read(loc: Path, problem: ProblemVariant) -> ProblemData:
    """
    Reads a problem instance from file and returns a ProblemData instance.
    """
    machine_variants = {
        ProblemVariant.JSP: MachineInstance.parse_jsp,
        ProblemVariant.FJSP: MachineInstance.parse_fjsp,
        ProblemVariant.HFSP: MachineInstance.parse_hfsp,
        ProblemVariant.NPFSP: MachineInstance.parse_npfsp,
        ProblemVariant.NW_PFSP: MachineInstance.parse_nw_pfsp,
        # Permutation machine scheduling
        ProblemVariant.PFSP: MachineInstance.parse_pfsp,
        ProblemVariant.SDST_PFSP: MachineInstance.parse_sdst_pfsp,
        ProblemVariant.TCT_PFSP: MachineInstance.parse_tct_pfsp,
        ProblemVariant.TT_PFSP: MachineInstance.parse_tt_pfsp,
        ProblemVariant.DPFSP: MachineInstance.parse_dpfsp,
    }
    project_variants = {
        # Project scheduling problems have instance-format specific parsers,
        # which are already supported directly by PyJobShop's read function.
        ProblemVariant.RCPSP: partial(_read, instance_format="patterson"),
        ProblemVariant.MMRCPSP: partial(_read, instance_format="psplib"),
        ProblemVariant.RCMPSP: partial(_read, instance_format="psplib"),
        ProblemVariant.ASLIB: partial(_read, instance_format="aslib"),
    }

    if problem in machine_variants:
        instance = machine_variants[problem](loc)
        return instance.data()

    if problem in project_variants:
        return project_variants[problem](loc)

    raise ValueError(f"Unsupported problem type: {problem}")
