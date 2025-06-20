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

from .Roi import Roi
from .StopWatch import *
from .TinyRoiManager import TinyRoiManager
from .TinyLog import log

state_and_tags = {0: (Roi.ROI_STATE_ACTIVE,set()),
        1: (Roi.ROI_STATE_DELETED, set(["edge.image"])),
        2: (Roi.ROI_STATE_DELETED,set(["small"])),
        3: (Roi.ROI_STATE_DELETED, set(["edge.image"]))
}

def process_label_image(rm: TinyRoiManager, data: dict, remove_edges: bool = True, remove_small: bool = True, size_threshold: int = 100) -> None:
    """this implementation starts from the outlines image in the dictionary saved by cellpose
        so the area does *not* exactly match the area of the cellpose label
        This implementation is about 2x faster
        Parameters:
        - dict: image dictionary read from the cellpose npy output
        - remove_edges: do labels at the image edge have to be excluded?
        - remove_small: do small labels < size_threshold have to be excluded?
        - size_threshold:
       
        the cellpose 'masks' touch each other so there is no gap in between them
        this function starts from the 'outlines' image:first the 'outlines' are dilated to completely
        fill the gaps between ROIs. Inverting the modified outlines reveals the ROIs as isolated islands.
        Now findContours can find all ROI contours in 1 call
        The areas of the ROIs calculated with this method are smaller than the area of ROIs identifies starting from 
        the masks.
        
    """
    masks = data["masks"]
    outlines = data["outlines"]

    edge_set= set()
    if remove_edges:
        edge_set = set(get_edge_labels(masks))

    assert outlines.ndim == 2, "Outlines is not a 2D array"

    # Step 1: make outlines binary
    outlines_bin = (outlines > 0).astype(np.uint8) * 255
    # Stap 2: dilate outlines
    kernel = np.ones((3, 3), dtype=np.uint8)
    dilated_outlines = cv2.dilate(outlines_bin, kernel, iterations=3)
    eroded_outlines = cv2.erode(dilated_outlines, kernel, iterations=3)
    
    # Stap 3: make masks binary
    masks_bin = np.where(masks > 0, 255, 0).astype(np.uint8)
    # Stap 4: verwijder alle punten in masks_bin die overlappen met dilated outlines
    cleaned = cv2.bitwise_and(masks_bin, cv2.bitwise_not(eroded_outlines))
    # Stap 5: zoek contouren
    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    roi_array = np.full(shape=len(contours)+100,fill_value=None,dtype=Roi)
    max_digits=len(str( len(roi_array) ))
    corr = np.sqrt(1.00215)


    if not contours:
        print(f"label file has no contours!")
        return None
    for contour in contours:
        a=cv2.contourArea(contour)
        p=cv2.arcLength(contour,True)
        if not (a and p):
            continue
        s= np.sqrt(1+p/a)*corr

        coords = np.array(contour.squeeze()).reshape(-1, 2)

        M = cv2.moments(contour)
        centroid=[M['m10']/M['m00'],M['m01']/M['m00']]
        cx = int(centroid[0])
        cy = int(centroid[1])

        # scale coords to scale area
        #coords = centroid + s * (coords - centroid)
        contour = coords.reshape(-1, 1, 2).astype(np.float32)

        xpoints = np.array(coords[:, 0],dtype=np.int_)
        ypoints = np.array(coords[:, 1],dtype=np.int_)
        n = len(xpoints)

        label_value = masks[cy,cx]
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
    rm.add_from_list_unchecked(roi_array)

def get_edge_labels(label_image: np.ndarray) -> np.ndarray:

  top = label_image[0, :]
  bottom = label_image[-1, :]
  left = label_image[:, 0]
  right = label_image[:, -1]
  
  border_values = np.concatenate([top, bottom, left, right])
  
  unique_labels = np.unique(border_values)
  unique_labels = unique_labels[unique_labels != 0]
  
  return unique_labels