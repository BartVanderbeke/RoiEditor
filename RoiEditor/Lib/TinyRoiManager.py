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
from Feret import get_values

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

    def __init__(self,prefix: str = "L", parent=None):
        super().__init__(parent=parent)
        self._name_to_roi: dict[str, Roi] = dict()
        self.prefix = prefix

    @staticmethod
    def is_valid(rm: "TinyRoiManager"):
        return rm is not None and len(rm._name_to_roi)>0

    @property
    def num_of_rois(self):
        return len(self._name_to_roi)
    
    def first_free_name(self) -> str:
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
                    log(f"Deleting {len(roi_active_children)} {kids} of {roi.name}")
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
                    log(f"Deleting {len(roi_active_children)} {kids} of {roi.name}")
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

    # def set_state(self, rois_or_names, new_state):
    #     for name in self._resolve_names(rois_or_names):
    #         roi = self._name_to_roi.get(name)
    #         if roi:
    #             roi.state = new_state
    #             roi.reason_of_selection = ""

    def get_measurement_names(self):
        return ["Area"] + list(feret_index.keys()) + ["central nuclei"]

    def get_measurements_by_filter(self, filter: Optional[Callable[[Roi], None]] = None) -> dict[str, list[float]]:
        keys = self.get_measurement_names() + ["Roi"]
        result = {key: [] for key in keys}
        filter = filter or (lambda _: True)
        for _, roi in self.iter_by_filter(filter):
            result["Area"].append(roi.area)
            ferets = roi.feret_values
            for feret_name, index in feret_index.items():
                result[feret_name].append(ferets[index])
            result["Roi"].append(roi)
            if roi.children:
                num_central_nuclei = sum(1 for c in roi.children if c.state != Roi.ROI_STATE_DELETED)
            else:
                num_central_nuclei = 0
            result["central nuclei"].append(num_central_nuclei)
        for key in keys:
            result[key]=np.array(result[key])
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
        return f"{self.prefix}{idx:0{max_digits}d}"
    
    def name_to_idx(name: str) -> int:
        return int(name[1:])
    
    @staticmethod
    def zip(parent_rm: "TinyRoiManager", child_rm: "TinyRoiManager"):
        if not parent_rm:
            log("Invalid Parent RoiManager provided for zipping", type="error")
            return
        if not child_rm:
            log("Invalid Child RoiManager provided for zipping", type="error")
            return
        if len(child_rm._name_to_roi)==0:
            log("Empty Child RoiManager provided for zipping", type="warning")
            return
        if len(parent_rm._name_to_roi)==0:
            log("Empty Parent RoiManager provided for zipping", type="warning")
            return
        

        for _, child_roi in child_rm.iter_all():
            if not child_roi.parent or child_roi.parent=="":
                child_roi.parent =None
                continue
            parent_roi_name: str = str(child_roi.parent)
            parent_roi = parent_rm.get_roi(parent_roi_name)  
            if not parent_roi:
                log(f"Parent ROI 'Parent {parent_roi_name}' not found for child {child_roi.name} in Parent RoiManager", type="error")
                continue
            child_roi.parent = parent_roi
            parent_roi.children.append(child_roi)
