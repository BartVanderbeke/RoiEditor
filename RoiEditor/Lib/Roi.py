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

from .Feret import get_values

class Roi:
    ROI_STATE_ACTIVE = 0
    ROI_STATE_DELETED = 255
    ROI_STATE_SELECTED = +1

    ROI_STATES = {ROI_STATE_ACTIVE,ROI_STATE_SELECTED,ROI_STATE_DELETED}

    def __init__(self, xpoints: npt.NDArray[np.int_],
                 ypoints: npt.NDArray[np.int_],
                 name: Optional[str] = None,
                 state: Optional[int]= None,
                 tags: Optional[set[str]]= set(),
                 bounds: Optional[Tuple[int, int, int, int]] = None,  # (top, left, bottom, right)
                 center: Optional[Tuple[float, float]] = None,      # (cx, cy)
                 n: Optional[int]= None,
                 area: Optional[float]=None
                 ):

        assert len(xpoints) == len(ypoints), "Aantal x- en y-punten moet gelijk zijn"
        self.xpoints: npt.NDArray[np.int_] = xpoints
        self.ypoints: npt.NDArray[np.int_] = ypoints
        self.name: str = name or "Polygon"
        self.state: Optional[int] = state
        self.tags: Optional[set[str]]= tags
        self.reason_of_selection:str=None

        if n:
            self.n=n
        else:
            self.n: int = len(xpoints)
        if bounds:
            self._bounds=bounds
        if center:
            self._center=center
        if area:
            self._area=area

    @property
    def area(self) -> float:
        if not hasattr(self, '_area') or self._area is None:
            x = np.asarray(self.xpoints)
            y = np.asarray(self.ypoints)
            R1= np.dot(x, np.roll(y, 1))
            R2= np.dot(y, np.roll(x, 1))
            self._area = 0.5 * np.abs( R1-R2 )


        return self._area

    @property
    def bounds(self) -> Tuple[int, int, int, int]:
        if not hasattr(self, '_bounds') or self._bounds is None:
            #(top, left, bottom, right)
            self._bounds=(np.min(self.ypoints), np.min(self.xpoints), np.max(self.ypoints), np.max(self.xpoints))
        return self._bounds
    
    @property
    def center(self) -> Tuple[int, int]:
        if not hasattr(self, '_box') or self._center is None:
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


