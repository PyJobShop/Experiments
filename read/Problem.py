from enum import Enum


class ProblemVariant(str, Enum):
    # Non-permutation machine scheduling problems
    JSP = "JSP"
    FJSP = "FJSP"
    NPFSP = "NPFSP"
    NW_PFSP = "NW-PFSP"
    HFSP = "HFSP"
    # Permutation machine scheduling problems
    PFSP = "PFSP"
    SDST_PFSP = "SDST-PFSP"
    TCT_PFSP = "TCT-PFSP"
    TT_PFSP = "TT-PFSP"
    DPFSP = "DPFSP"
    # Project scheduling problems
    RCPSP = "RCPSP"
    MMRCPSP = "MMRCPSP"
    RCMPSP = "RCMPSP"
