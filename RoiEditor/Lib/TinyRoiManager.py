"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
from typing import Optional, Any
from numpy.typing import NDArray
import numpy as np
from typing import Optional, Callable

from Roi import Roi
from Feret import feret_index
from TinyLog import log
from Feret import get_values, feret_msmts, feret_quantities, feret_units, feret_scalers


from PyQt6.QtCore import QObject
class TinyRoiManager(QObject):


    __measurement_names = ["Area"] + feret_msmts + ["Central Nuclei"] +["Color"]
    __quantities = ["area"] + feret_quantities + ["count"] + ["color"]
    __units = ["px"] + feret_units + ["#"] + [""]
    __scalers = [1.0*1.0] + feret_scalers + [1.0] + [1.0]
    __msmt_info = dict()

    for idx in range(len(__measurement_names)):
        __info = { "quantity": __quantities[idx],
                   "unit": __units[idx],
                   "scaler": __scalers[idx] }
        __msmt_info[__measurement_names[idx]] = __info

    TOGGLE: dict[int,int] = {Roi.ROI_STATE_DELETED: Roi.ROI_STATE_DELETED,
                             Roi.ROI_STATE_SELECTED: Roi.ROI_STATE_ACTIVE,
                             Roi.ROI_STATE_ACTIVE: Roi.ROI_STATE_SELECTED
    }

    DELETE_SELECTED: dict[int,int] = {Roi.ROI_STATE_DELETED: Roi.ROI_STATE_DELETED,
                             Roi.ROI_STATE_ACTIVE: Roi.ROI_STATE_ACTIVE,
                             Roi.ROI_STATE_SELECTED: Roi.ROI_STATE_DELETED
    }
    DESELECT: dict[int,int] = {Roi.ROI_STATE_DELETED: Roi.ROI_STATE_DELETED,
                             Roi.ROI_STATE_ACTIVE: Roi.ROI_STATE_ACTIVE,
                             Roi.ROI_STATE_SELECTED: Roi.ROI_STATE_ACTIVE
    }

    def __init__(self,prefix: str = "L", parent=None):
        super().__init__(parent=parent)
        self._name_to_roi: dict[str, Roi] = dict()
        self.prefix = prefix


    @staticmethod
    def measurement_names():
        return TinyRoiManager.__measurement_names

    @staticmethod
    def measurement_info():
        return TinyRoiManager.__msmt_info

    @staticmethod
    def quantities():
        return TinyRoiManager.__quantities
    @staticmethod
    def units():
        return TinyRoiManager.__units

    @staticmethod
    def scalers():
        return TinyRoiManager.__scalers

    @staticmethod
    def has_rois(rm: "TinyRoiManager"):
        return rm is not None and len(rm._name_to_roi)>0

    @property
    def num_of_rois(self):
        return len(self._name_to_roi)
    
    def first_free_name(self) -> str:
        if self._name_to_roi == {}:
            return f"{self.prefix}0001"
        max_key_str = max(self._name_to_roi.keys(), key=lambda k: int(k[1:]))
        first_free = int(max_key_str[1:]) + 1
        name = self.idx_to_name(first_free)
        return name
    
    def as_array(self):
        arr:  NDArray[Any]=np.ndarray(self._name_to_roi.values())
        return arr

    def add_from_list_unchecked(self,rois):
        self._name_to_roi ={roi.name: roi for roi in rois if roi}

    def add(self, rois):
        if not isinstance(rois, (list, set)):
            rois = [rois]

        for roi in rois:
            if roi:
                self._name_to_roi[roi.name] = roi

    def add_unchecked(self, roi):
        if roi:
            self._name_to_roi[roi.name] = roi

    def delete(self, rois_or_names):
        labels_to_clear: list[int] =list()
        for roi in self.iter_rois_or_names(rois_or_names):
            if roi:
                roi.state = Roi.ROI_STATE_DELETED
                if roi.reason_of_selection:
                    roi.tags.add(roi.reason_of_selection)
                    roi.reason_of_selection = ""
                label = int(roi.name[1:])
                labels_to_clear.append(label)
                roi_active_children = [c for c in roi.children if c.state != Roi.ROI_STATE_DELETED]
                if len(roi_active_children) > 0:
                    kids = "child" if len(roi_active_children)==1 else "children"
                    log(f"Deleting {len(roi_active_children)} {kids} of {roi.name}", type="info", log_level=1000)
                    for child in roi_active_children:
                        child.state = Roi.ROI_STATE_DELETED
                        child.tags.add("DELETED.WITH_PARENT")

    def delete_selected(self,reason_of_deletion=None):
        labels_to_clear: list[int] =list()
        for roi in self._name_to_roi.values():
            if roi.state == Roi.ROI_STATE_SELECTED:
                roi.state = Roi.ROI_STATE_DELETED
                if reason_of_deletion:
                    roi.tags.add(reason_of_deletion)
                elif roi.reason_of_selection:
                    roi.tags.add(roi.reason_of_selection)
                roi.reason_of_selection = ""
                label = int(roi.name[1:])
                labels_to_clear.append(label)
                if roi.children:
                    roi_active_children = [c for c in roi.children if c.state != Roi.ROI_STATE_DELETED]
                else:
                    roi_active_children = []
                if len(roi_active_children) > 0:
                    kids = "child" if len(roi_active_children)==1 else "children"
                    log(f"Deleting {len(roi_active_children)} {kids} of {roi.name}", type="info", log_level=1000)
                    for child in roi_active_children:
                        child.state = Roi.ROI_STATE_DELETED
                        child.tags.add("DELETED.WITH_PARENT")
   

    def toggle_selection(self, rois_or_names):
        for roi in self.iter_rois_or_names(rois_or_names):
            roi.state = self.TOGGLE[roi.state]
            roi.reason_of_selection = ""

    def select(self, rois_or_names, reason_of_selection=None,additive=False):
        if not additive:
            for roi in self._name_to_roi.values():
                roi.state = self.DESELECT[roi.state]
                roi.reason_of_selection=""
        for roi in self.iter_rois_or_names(rois_or_names):
            if roi:
                roi.state = Roi.ROI_STATE_SELECTED
                roi.reason_of_selection = reason_of_selection

    def select_within(self, rectangle, additive=False):
        """Select all ROIs whose bounding rectangles are fully within the given rectangle."""
        if not additive:
            for roi in self._name_to_roi.values():
                roi.state = self.DESELECT[roi.state]
        rect_xmin = int(rectangle.x())
        rect_ymin = int(rectangle.y())
        rect_xmax = int(rectangle.x() + rectangle.width())
        rect_ymax = int(rectangle.y() + rectangle.height())
        log(f"Set rectangle: ({rect_xmin},{rect_ymin}) ({rect_xmax},{rect_ymax})", type="debug", log_level=1000)

        for roi in self._name_to_roi.values():
            if roi.state != Roi.ROI_STATE_ACTIVE:
                continue
            (top, left, bottom, right) = roi.bounds
            if (rect_xmin <= left and
                rect_ymin <= top and
                rect_xmax >= right and
                rect_ymax >= bottom):
                roi.state = Roi.ROI_STATE_SELECTED
                roi.reason_of_selection = ""

    def unselect_all(self):
        for roi in self._name_to_roi.values():
            roi.state = self.DESELECT[roi.state]
            roi.reason_of_selection = ""

    # def set_state(self, rois_or_names, new_state):
    #     for name in self._resolve_names(rois_or_names):
    #         roi = self._name_to_roi.get(name)
    #         if roi:
    #             roi.state = new_state
    #             roi.reason_of_selection = ""
    # @staticmethod
    # def get_measurement_names() -> list[str]:
    #     return ["Area"] + list(feret_index.keys()) + ["Central Nuclei"] +["Color"]

    def get_measurements_by_filter(self, filter: Optional[Callable[[Roi], bool]] = None) -> dict[str, NDArray[Any]]:
        keys = TinyRoiManager.measurement_names() + ["Roi"]
        _result = {key: [] for key in keys}
        result = {key: np.array([]) for key in keys}
        filter = filter or (lambda _: True)
        for _, roi in self.iter_by_filter(filter):
            _result["Area"].append(roi.area)
            _result["Color"].append(roi.color)
            ferets = roi.feret_values
            for feret_name, index in feret_index.items():
                _result[feret_name].append(ferets[index])
            _result["Roi"].append(roi)
            if roi.children:
                num_central_nuclei = sum(1 for c in roi.children if c.state != Roi.ROI_STATE_DELETED)
            else:
                num_central_nuclei = 0
            _result["Central Nuclei"].append(num_central_nuclei)
   
        for key in keys:
            result[key]=np.array(_result[key])

        return result

    def get_roi(self, name):
        return self._name_to_roi.get(name)

    def get_state(self, name):
        roi = self._name_to_roi.get(name)
        return roi.state if roi else None

    def get_tags(self, name):
        roi = self._name_to_roi.get(name)
        return roi.tags if roi else set()

    def set_tags(self, name, tags):
        roi = self._name_to_roi.get(name)
        if roi:
            roi.tags = set(tags)

    def get_all_names(self, exclude_deleted=False):
        return [
            name for name, roi in self._name_to_roi.items()
            if not exclude_deleted or roi.state != Roi.ROI_STATE_DELETED
        ]

    def list_rois(self):
        return list(self._name_to_roi.values())

    def __len__(self):
        return len(self._name_to_roi)

    def __iter__(self):
        for name, roi in self._name_to_roi.items():
            if roi.state != Roi.ROI_STATE_DELETED:
                yield name, roi

    def iter_all(self):
        return iter(self._name_to_roi.items())

    def iter_by_state(self, target_state):
        for name, roi in self._name_to_roi.items():
            if roi.state == target_state:
                yield name, roi

    def iter_by_filter(self, filter_fn):
        for name, roi in self._name_to_roi.items():
            if filter_fn(roi):
                yield name, roi

    def map_over_rois(self, func):
        return [func(roi) for roi in self._name_to_roi.values() if roi.state != Roi.ROI_STATE_DELETED]

    def get_sample(self) -> Roi | None:
        for roi in self._name_to_roi.values():
            return roi
        return None

    def iter_rois_or_names(self, rois_or_names):
        if not isinstance(rois_or_names, (list, np.ndarray, tuple)):
            rois_or_names = np.array([rois_or_names])
        if not len(rois_or_names)>0:
            return None
        if isinstance(rois_or_names[0],str):
            names = rois_or_names
            for name in names:
                roi = self._name_to_roi.get(name)
                if roi:
                    yield roi
                else:
                    log("Unexpected empty ROI encountered",type ="warning")                    
        if isinstance(rois_or_names[0],Roi):
            rois= rois_or_names
            for roi in rois:
                if roi:
                    yield roi
                else:
                    log("Unexpected empty ROI encountered",type ="warning")

    def _resolve_names(self, rois_or_names):
        if not isinstance(rois_or_names, (list, set,np.ndarray)):
            rois_or_names = [rois_or_names]
        return [
            r.name if hasattr(r, "name") else r
            for r in rois_or_names
        ]


    def force_feret(self):
        for roi in self._name_to_roi.values():

            roi.feret_values=get_values(roi._xpoints, roi._ypoints)
            #_ = roi.feret_values
        
    def idx_to_name(self,idx) -> str:
        key = next(iter(self._name_to_roi), "X0000")
        max_digits: int = len(key)-1
        return f"{self.prefix}{idx:0{max_digits}d}"
    
    @staticmethod
    def name_to_idx(name: str) -> int:
        return int(name[1:])
    

