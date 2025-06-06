"""RoiEditor

Author: Bart Vanderbeke
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

from .Roi import Roi
from .Feret import feret_index
from .TinyLog import log
from .Feret import get_values

from PyQt6.QtCore import QObject
class TinyRoiManager(QObject):

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

    def __init__(self, filtered_label_image: np.ndarray=None,parent=None):
        super().__init__(parent=parent)
        self._name_to_roi: dict[str, Roi] = {}
        #self._lock = threading.Lock()
        #self._counter = 0
        self.filtered_label_image=filtered_label_image
        self._use_label_image: bool= self.filtered_label_image is not None

    def _on_destroyed(self, obj):
        print("Roi manager is being deleted")

    # def reset(self,filtered_label_image: np.ndarray=None):
    #     self._name_to_roi.clear()
    #     self.filtered_label_image=filtered_label_image

    # def attach(self,filtered_label_image: np.ndarray):
    #     self.filtered_label_image=filtered_label_image

    @classmethod
    def is_valid(cls,rm: "TinyRoiManager"):
        return rm is not None and len(rm._name_to_roi)>0

    @property
    def num_of_rois(self):
        return len(self._name_to_roi)
    
    def as_array(self):
        arr:  NDArray[Any]=np.ndarray(self._name_to_roi.values())
        return arr

    def add_from_list_unchecked(self,rois):
        self._name_to_roi ={roi.name: roi for roi in rois if roi}

        if self._use_label_image:
            labels_to_clear = [int(roi.name[1:]) for roi in rois if roi and roi.state == Roi.ROI_STATE_DELETED]
            if labels_to_clear:
                mask = np.isin(self.filtered_label_image, labels_to_clear)
                self.filtered_label_image[mask] = 0 

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
        labels_to_clear: list[int] =[]
        for roi in self.iter_rois_or_names(rois_or_names):
            if roi:
                roi.state = Roi.ROI_STATE_DELETED
                if roi.reason_of_selection:
                    roi.tags.add(roi.reason_of_selection)
                    roi.reason_of_selection = ""
                label = int(roi.name[1:])
                labels_to_clear.append(label)
        if labels_to_clear and self._use_label_image:
            mask = np.isin(self.filtered_label_image, labels_to_clear)
            self.filtered_label_image[mask] = 0   

    def delete_selected(self,reason_of_deletion=None):
        labels_to_clear: list[int] =[]
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
        if self._use_label_image and labels_to_clear:
            mask = np.isin(self.filtered_label_image, labels_to_clear)
            self.filtered_label_image[mask] = 0
   

    def toggle(self, rois_or_names):
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
        log(f"Set rectangle: ({rect_xmin},{rect_ymin}) ({rect_xmax},{rect_ymax})")

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

    def set_state(self, rois_or_names, new_state):
        for name in self._resolve_names(rois_or_names):
            roi = self._name_to_roi.get(name)
            if roi:
                roi.state = new_state
                roi.reason_of_selection = ""

    def get_measurements_by_filter(self, filter: Optional[Callable[[Roi], None]] = None) -> dict[str, list[float]]:
        keys = ["Area"] + list(feret_index.keys())+["Roi"]
        result = {key: [] for key in keys}
        filter = filter or (lambda _: True)
        for _, roi in self.iter_by_filter(filter):
            result["Area"].append(roi.area)
            ferets = roi.feret_values
            for feret_name, index in feret_index.items():
                result[feret_name].append(ferets[index])
            result["Roi"].append(roi)
        for key in keys:
            result[key]=np.array(result[key])
        return result

    def get_measurements_by_state(self, state: int = None) -> dict[str, list[float]]:
        keys = ["Area"] + list(feret_index.keys())
        result = {key: [] for key in keys}
        state = state or Roi.ROI_STATE_ACTIVE
        for _, roi in self.iter_by_state(state):
            result["Area"].append(roi.area)
            ferets = roi.feret_values()
            for feret_name, index in feret_index.items():
                result[feret_name].append(ferets[index])

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

    def get_sample(self):
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

            roi.feret_values=get_values(roi.xpoints, roi.ypoints)
            #_ = roi.feret_values
        
    def idx_to_name(self,idx) -> str:
        max_digits: int = len(str(self.num_of_rois))
        return f"L{idx:0{max_digits}d}"
    
    def name_to_idx(name: str) -> int:
        return int(name[1:])
    