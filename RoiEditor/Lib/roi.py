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
from nptyping import NDArray, Shape, Float64

import warnings
warnings.simplefilter("error")

from feret import get_values

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
        self._xpoints: npt.NDArray[np.int_] = xpoints
        self._ypoints: npt.NDArray[np.int_] = ypoints
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
        self._n: int | None = n
        self.color: NDArray[Shape["1, 3"], Float64] | None = None  # a row vector with 3 columns H,S and V
        self.color_dist: float | None =None

        if n is None and xpoints is not None:
            self._n = len(xpoints)

    @property
    def n(self):
        if self._n is None or self._xpoints is None or self._ypoints is None:
            self._n = None
        else:
            self._n = len(self._xpoints)
        return self._n


    @property
    def xpoints(self):
        return self._xpoints

    @property
    def ypoints(self):
        return self._ypoints

    @xpoints.setter
    def xpoints(self, value):
        self._xpoints = value
        if self._xpoints is not None and self._ypoints is not None:
            assert len(self._xpoints) == len(self._ypoints), "xpoints and yppoints must have the same length"
        self._n = None
        self._feret_values = None
        self._bounds = None
        self._area = None
        self._center = None
    

    @ypoints.setter
    def ypoints(self, value):
        self._ypoints = value
        if self._xpoints is not None and self._ypoints is not None:
            assert len(self._xpoints) == len(self._ypoints), "xpoints and yppoints must have the same length"
        self._n = None
        self._feret_values = None
        self._bounds = None
        self._area = None
        self._center = None


    @property
    def area(self) -> Optional[float]:
        if self._xpoints is None or self._ypoints is None:
            self._area = None
            return self._area
        assert self._xpoints is not None and self._ypoints is not None
        if self._area is None:
            x = np.asarray(self._xpoints)
            y = np.asarray(self._ypoints)
            R1= np.dot(x, np.roll(y, 1))
            R2= np.dot(y, np.roll(x, 1))
            self._area = 0.5 * np.abs( R1-R2 )
        return self._area

    @property
    def bounds(self) -> Tuple[int, int, int, int] | None:
        if self._bounds is None:
            #(top, left, bottom, right)
            self._bounds = (
                int(np.min(self._ypoints)),
                int(np.min(self._xpoints)),
                int(np.max(self._ypoints)),
                int(np.max(self._xpoints))
            )
        return self._bounds
    
    @property
    def center(self) -> Tuple[float, float] | None:
        if self._center is None:
            # (cx,cy)
            self._center=(float(np.mean(self._xpoints)), float(np.mean(self._ypoints)))
        return self._center

    
    @property
    def feret_values(self):
        if not hasattr(self, '_feret_values') or self._feret_values is None:
            self._feret_values = get_values(self._xpoints, self._ypoints)
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


