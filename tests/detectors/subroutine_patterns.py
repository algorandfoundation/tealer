from typing import List

from tealer.detectors.all_detectors import CanUpdate


MULTIPLE_RETURN_POINTS = """
#pragma version 7       // B0
callsub subroutine_0
callsub subroutine_0    // B1
int 1                   // B2
return
subroutine_0:           // B3
    retsub
"""

# There is only one possible execution path B0 -> B3 -> B1 -> B3 -> B2
# 1.) In the CFG B3(subroutine_0) is connected to B1 and B2. And when traversing the CFG, detector
# considers B0 -> B3 -> B2 as a valid path and reports it.
#
# 2.) Path B0 -> B3 -> B1 -> B3 -> B2 is not reported because `subroutine_0` is called twice and
# on the second call, detectors think that they are in a loop because subroutine's blocks are
# are already in the path(after the first call).

# Before fixing bug (1) and (2)
MULTIPLE_RETURN_POINTS_VULNERABLE_PATHS_1: List[List[int]] = [
    [0, 3, 2],
]

# After fixing bug (1) and not (2)
MULTIPLE_RETURN_POINTS_VULNERABLE_PATHS_2: List[List[int]] = []

# After fixing bug (1) and (2)
MULTIPLE_RETURN_POINTS_VULNERABLE_PATHS_3: List[List[int]] = [
    [0, 3, 1, 3, 2],
]

subroutine_patterns_tests = [
    # (MULTIPLE_RETURN_POINTS, CanUpdate, MULTIPLE_RETURN_POINTS_VULNERABLE_PATHS_1),
    # (MULTIPLE_RETURN_POINTS, CanUpdate, MULTIPLE_RETURN_POINTS_VULNERABLE_PATHS_2),
    (MULTIPLE_RETURN_POINTS, CanUpdate, MULTIPLE_RETURN_POINTS_VULNERABLE_PATHS_3),
]
