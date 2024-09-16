from enum import Enum


class Problem(str, Enum):
    FJSP = "Flexiblejobshop"
    PFSP = "Flowshop"
    HFSP = "Hybridflowshop"
    JSP = "Jobshop"
    NPFSP = "Non-Flowshop"
    NW_PFSP = "Nowaitflowshop"
    PMP = "Parallelmachine"
    SDST_PFSP = "Setupflowshop"
    TCT_PFSP = "TCTflowshop"
    TT_PFSP = "Tardinessflowshop"
    # Project scheduling problems
    RCPSP = "RCPSP"
    MMRCPSP = "MMRCPSP"
    RCMPSP = "RCMPSP"
