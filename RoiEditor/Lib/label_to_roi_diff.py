"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
import numpy as np
import cv2
from numba import njit

from roi import Roi
from tiny_roi_manager import TinyRoiManager
from tiny_log import log

state_and_tags = {0: (Roi.ROI_STATE_ACTIVE,set()),
        1: (Roi.ROI_STATE_DELETED, set(["DELETED.edge.image"])),
        2: (Roi.ROI_STATE_DELETED,set(["DELETED.small"])),
        3: (Roi.ROI_STATE_DELETED, set(["DELETED.edge.image"]))
}


@njit(cache=True)
def _remove_internal_edges_jit(label_img):
    result = label_img.copy()
    height, width = label_img.shape

    for y in range(height):
        for x in range(width - 1):
            if label_img[y, x] != label_img[y, x + 1]:
                result[y, x] = 0
                result[y, x + 1] = 0

    for y in range(height - 1):
        for x in range(width):
            if label_img[y, x] != label_img[y + 1, x]:
                result[y, x] = 0
                result[y + 1, x] = 0

    return result


@njit(cache=True)
def _to_binary_u8_jit(label_img):
    height, width = label_img.shape
    out = np.zeros((height, width), dtype=np.uint8)

    for y in range(height):
        for x in range(width):
            if label_img[y, x] > 0:
                out[y, x] = np.uint8(255)

    return out


@njit(cache=True)
def _get_edge_labels_jit(label_image):
    max_label = int(np.max(label_image))
    if max_label <= 0:
        return np.empty((0,), dtype=np.int32)

    seen = np.zeros(max_label + 1, dtype=np.uint8)
    height, width = label_image.shape

    for x in range(width):
        top_value = int(label_image[0, x])
        bottom_value = int(label_image[height - 1, x])
        if top_value > 0:
            seen[top_value] = 1
        if bottom_value > 0:
            seen[bottom_value] = 1

    for y in range(height):
        left_value = int(label_image[y, 0])
        right_value = int(label_image[y, width - 1])
        if left_value > 0:
            seen[left_value] = 1
        if right_value > 0:
            seen[right_value] = 1

    count = 0
    for label in range(1, max_label + 1):
        if seen[label] != 0:
            count += 1

    out = np.empty((count,), dtype=np.int32)
    idx = 0
    for label in range(1, max_label + 1):
        if seen[label] != 0:
            out[idx] = label
            idx += 1

    return out


def remove_internal_edges(label_img):
    """
        creates openings between adjacent labels or
        transitions from background to a label
        so findContours can be applied to the complete image
    """
    return _remove_internal_edges_jit(label_img).astype(np.uint8)

def erase_label_edges(label_img):
    """
        creates openings between adjacent labels by using a diff,
        so findContours can be applied to the complete image
    """
    return _remove_internal_edges_jit(label_img)

def process_label_image(rm: TinyRoiManager, label_image: np.ndarray, remove_edges: bool = True, remove_small: bool = True, size_threshold: int = 100) -> None:
    """ this implementation first vreates a gap with background value around each ROI
        so the area does *not* exactly match the area of the cellpose label
        This implementation is about 2x faster
    Parameters:
    - label_image: 2D NumPy-array with integer labels (0 = background)
    - remove_edges: do labels at the image edge have to be excluded?
    - remove_small: do small labels < size_threshold have to be excluded?
    - size_threshold:
    """    
    edge_set= set()
    if remove_edges:
        edge_set = set(get_edge_labels(label_image))

    lbl_img = remove_internal_edges(label_image)
    lbl_img = _to_binary_u8_jit(lbl_img)
    
    contours, _ = cv2.findContours(lbl_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    max_label = int(np.max(label_image))
    roi_array = np.full(shape=max_label+1,fill_value=None,dtype=Roi)
    max_digits=len(str( len(roi_array) ))
    #corr = np.sqrt(1.00215)

    if not contours:
        log(f"label image does not contain contours!", type="warning")
        return None
    for contour in contours:
        # a=cv2.contourArea(contour)
        # p=cv2.arcLength(contour,True)
        # if not (a and p):
            # continue
        # s= np.sqrt(1+p/a)*corr

        coords = np.array(contour.squeeze()).reshape(-1, 2)

        M = cv2.moments(contour)
        m00 =M['m00']
        if not m00:
            continue
        centroid=[M['m10']/m00,M['m01']/m00]
        cx = int(centroid[0])
        cy = int(centroid[1])

        # scale coords to scale area
        # coords = centroid + s * (coords - centroid)
        # contour = coords.reshape(-1, 1, 2).astype(np.float32)

        xpoints = np.array(coords[:, 0],dtype=np.int_)
        ypoints = np.array(coords[:, 1],dtype=np.int_)
        n = len(xpoints)

        label_value = label_image[cy,cx]
        if label_value ==0:
            continue
        if coords.ndim != 2 or len(coords) < 3:
            log(f"Contour is no polygon for {str(label_value)} : ndim= {coords.ndim}, #coords= {len(coords)}, #contours={len(contours)}",type="warning")
            continue

        left, top, w, h = cv2.boundingRect(contour)
        right= left + w
        bottom = top + h

        area=cv2.contourArea(contour)

        is_on_edge = label_value in edge_set
        is_small = remove_small and area < size_threshold
        key = int(is_on_edge) * 1 + int(is_small) * 2
        (state, tags) = state_and_tags[key]
        roi_name: str = f"L{label_value:0{max_digits}d}"

        roi = Roi(
            xpoints=xpoints,
            ypoints=ypoints,
            name=roi_name,
            state=state,
            tags = tags,
            bounds =(top,left,bottom,right),
            center =(cx,cy),
            n=n,
            area=area
        )
        roi_array[label_value]=roi
    # roi_0_idx=0
    # roi_0_name =f"L{roi_0_idx:0{max_digits}d}"
    # roi_0 = Roi(name=roi_0_name,xpoints=np.empty((0,)).astype(int),ypoints=np.empty((0,)).astype(int),state=Roi.ROI_STATE_ACTIVE)
    # roi_array[0]=roi_0
    rm.add_from_list_unchecked(roi_array)

def get_edge_labels(label_image: np.ndarray) -> np.ndarray:
    return _get_edge_labels_jit(label_image)
