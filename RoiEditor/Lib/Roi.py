"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
import numpy as np
from typing import Optional,Tuple
import numpy.typing as npt

import warnings
warnings.simplefilter("error")

from Feret import get_values

class Roi:
    ROI_STATE_ACTIVE = 0
    ROI_STATE_DELETED = 255
    ROI_STATE_SELECTED = +1

    ROI_STATES = {ROI_STATE_ACTIVE,ROI_STATE_SELECTED,ROI_STATE_DELETED}

    def __init__(self, xpoints: npt.NDArray[np.int_],
                 ypoints: npt.NDArray[np.int_],
                 name: Optional[str] = None,
                 state: Optional[int |None]= None,
                 tags: Optional[set[str]]= set(),
                 bounds: Optional[Tuple[int, int, int, int]] = None,  # (top, left, bottom, right)
                 center: Optional[Tuple[float, float]] = None,      # (cx, cy)
                 n: Optional[int | None]= None,
                 area: Optional[float]=None,
                 parent: Optional['Roi | str']= None,
                 children: Optional[list['Roi'] | None] = None
                 ):

        assert len(xpoints) == len(ypoints), "Aantal x- en y-punten moet gelijk zijn"
        self.xpoints: npt.NDArray[np.int_] = xpoints
        self.ypoints: npt.NDArray[np.int_] = ypoints
        self.name: str = name if name is not None else ""
        self.state: int | None = state
        self.tags: set[str] = set(tags) if tags else set()
        self.reason_of_selection: str |None = None
        self.parent: 'Roi | str | None' = parent if parent else None
        self.children: list['Roi'] = list(children) if children is not None else list()
        self._feret_values: npt.NDArray[np.float_] | None = None
        self._bounds: Tuple[int, int, int, int] | None = bounds
        self._area: float | None = area
        self._center: Tuple[float, float] | None = center
        self.n: int | None = n

        if n is None and xpoints is not None:
            self.n: int = len(xpoints)

    @property
    def area(self) -> float:
        if self._area is None:
            x = np.asarray(self.xpoints)
            y = np.asarray(self.ypoints)
            R1= np.dot(x, np.roll(y, 1))
            R2= np.dot(y, np.roll(x, 1))
            self._area = 0.5 * np.abs( R1-R2 )
        return self._area

    @property
    def bounds(self) -> Tuple[int, int, int, int]:
        if self._bounds is None:
            #(top, left, bottom, right)
            self._bounds=(np.min(self.ypoints), np.min(self.xpoints), np.max(self.ypoints), np.max(self.xpoints))
        return self._bounds
    
    @property
    def center(self) -> Tuple[int, int]:
        if self._center is None:
            # (cx,cy)
            self._center=(np.mean(self.xpoints),np.mean(self.ypoints))
        return self._center

    
    @property
    def feret_values(self):
        if not hasattr(self, '_feret_values') or self._feret_values is None:
            self._feret_values = get_values(self.xpoints, self.ypoints)
        return self._feret_values

    @feret_values.setter
    def feret_values(self, value: np.ndarray):
        self._feret_values = value

    def __repr__(self):
        return f"<Roi name={self.name} state={self.state}  tags={self.tags}>"
    
    @staticmethod
    def state_to_str(state):
        if state == Roi.ROI_STATE_DELETED:
            return "ROI_STATE_DELETED"
        elif state == Roi.ROI_STATE_SELECTED:
            return "ROI_STATE_SELECTED"
        else:
            return "ROI_STATE_ACTIVE"

    @staticmethod
    def str_to_state(state):
        if state == "ROI_STATE_DELETED":
            return Roi.ROI_STATE_DELETED
        elif state == "ROI_STATE_SELECTED":
            return Roi.ROI_STATE_SELECTED
        else:
            return Roi.ROI_STATE_ACTIVE


