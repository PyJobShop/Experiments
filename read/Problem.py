from enum import Enum


class ProblemVariant(str, Enum):
    # Non-permutation machine scheduling problems
    PMP = "Parallelmachine"
    JSP = "Jobshop"
    FJSP = "Flexiblejobshop"
    NPFSP = "Non-Flowshop"
    NW_PFSP = "Nowaitflowshop"
    HFSP = "Hybridflowshop"
    # Permutation machine scheduling problems
    PFSP = "Flowshop"
    SDST_PFSP = "Setupflowshop"
    TCT_PFSP = "TCTflowshop"
    TT_PFSP = "Tardinessflowshop"
    # Project scheduling problems
    RCPSP = "RCPSP"
    MMRCPSP = "MMRCPSP"
    RCMPSP = "RCMPSP"
