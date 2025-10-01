
import numpy as np
from TinyRoiManager import TinyRoiManager
from TinyLog import log
from Roi import Roi

def declare_orphan(child_roi: Roi):
    child_roi.parent = None
    child_roi.state = Roi.ROI_STATE_DELETED
    child_roi.tags.add("DELETED.OUTSIDE_CELL")
    
def declare_parent_deceased(child_roi: Roi):
    child_roi.state = Roi.ROI_STATE_DELETED
    child_roi.tags.add("DELETED.WITH_PARENT")

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
            declare_orphan(child_roi)
            continue
        parent_roi_name: str = str(child_roi.parent)
        parent_roi = parent_rm.get_roi(parent_roi_name)  
        if not parent_roi:
            log(f"Parent ROI 'Parent {parent_roi_name}' not found for child {child_roi.name} in Parent RoiManager", type="error")
            declare_orphan(child_roi)
            continue
        child_roi.parent = parent_roi
        parent_roi.children.append(child_roi)
        if parent_roi.state == Roi.ROI_STATE_DELETED:
            declare_parent_deceased(child_roi)


def find_parent(parent_rm: TinyRoiManager, child_rm: TinyRoiManager, parent_label_image: np.ndarray) -> None:
    for _, child_roi in child_rm.iter_all():
        child_center: tuple[float, float] = child_roi.center
        child_parent_idx = parent_label_image[int(child_center[1]), int(child_center[0])]
        if child_parent_idx == 0:
            declare_orphan(child_roi)
            continue
        parent_roi_name = parent_rm.idx_to_name(child_parent_idx)
        parent_roi: Roi | None = parent_rm.get_roi(parent_roi_name)
        if not parent_roi:
            declare_orphan(child_roi)
            continue
        parent_roi.children.append(child_roi)
        if parent_roi.state == Roi.ROI_STATE_DELETED:
            declare_parent_deceased(child_roi)

