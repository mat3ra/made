"""
Routines for calculating conventional cell vectors from primitive cell vectors.
Python equivalent of src/js/cell/conventional_cell.ts.

Following Setyawan, W., & Curtarolo, S. (2010). doi:10.1016/j.commatsci.2010.05.010
"""

from typing import Dict, List

Matrix3x3 = List[List[float]]

UNIT_MATRIX: Matrix3x3 = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]

# (Conventional cell vectors) = (PRIMITIVE_TO_CONVENTIONAL_CELL_MULTIPLIER matrix) * (Primitive cell vectors),
# vectors as rows.
PRIMITIVE_TO_CONVENTIONAL_CELL_MULTIPLIERS: Dict[str, Matrix3x3] = {
    "CUB": UNIT_MATRIX,
    "FCC": [[-1, 1, 1], [1, -1, 1], [1, 1, -1]],
    "BCC": [[0, 1, 1], [1, 0, 1], [1, 1, 0]],
    "TET": UNIT_MATRIX,
    "BCT": [[0, 1, 1], [1, 0, 1], [1, 1, 0]],
    "ORC": UNIT_MATRIX,
    "ORCF": [[-1, 1, 1], [1, -1, 1], [1, 1, -1]],
    "ORCI": [[0, 1, 1], [1, 0, 1], [1, 1, 0]],
    "ORCC": [[1, -1, 0], [1, 1, 0], [0, 0, 1]],
    "HEX": UNIT_MATRIX,
    "RHL": UNIT_MATRIX,
    "MCL": UNIT_MATRIX,
    "MCLC": [[1, -1, 0], [1, 1, 0], [0, 0, 1]],
    "TRI": UNIT_MATRIX,
}
