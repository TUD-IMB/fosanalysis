
r"""
Contains modules for compensating physical influences on the strain measurements.
Those are:
- creep and shrinkage,
- fiber slippage,
- temperature,
- tension stiffening,
- other influences (to be extended).

The base class of all of those is \ref compensation.compensator.Compensator.

\author Bertram Richter
\date 2023
"""

from . import compensator
from . import shrinking
from . import tensionstiffening
