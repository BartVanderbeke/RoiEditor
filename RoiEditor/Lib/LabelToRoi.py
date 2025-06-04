"""RoiEditor

Author: Bart Vanderbeke
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
import numpy as np
import cv2
from skimage.measure import regionprops

from .Roi import Roi
from .TinyRoiManager import TinyRoiManager
from .TinyLog import log

state_and_tags = {0: (Roi.ROI_STATE_ACTIVE,set()),
        1: (Roi.ROI_STATE_DELETED, set(["edge.image"])),
        2: (Roi.ROI_STATE_DELETED,set(["small"])),
        3: (Roi.ROI_STATE_DELETED, set(["edge.image"]))
}

def process_label_image(rm: TinyRoiManager, label_image: np.ndarray, remove_edges: bool = True, remove_small: bool = True, size_threshold: int = 100) -> None:
    """
    Parameters:
    - label_image: 2D NumPy-array with integer labels (0 = achtergrond)
    - remove_edges: do labels at the image edge have to be excluded?
    - remove_small: do small labels < size_threshold have to be excluded?
    - size_threshold:
    """
    manager: TinyRoiManager = rm
    
    # Gebruik regionprops direct op de label_image; elke unieke labelwaarde vormt een regio.
    StopWatch.start()
    regions = np.array(regionprops(label_image=label_image,cache=True))
    max_label= max(r.label for r in regions)
    max_digits: int = len(str(max_label))
    height, width = label_image.shape
    edge_h: int = width-1
    edge_v: int = height-1
    roi_array = np.full(max_label+1,None,dtype=Roi)

    for region in regions:
        idx = region.label
        if not idx:
            continue

        mask: np.ndarray = region.image.astype(np.uint8)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            log(f"No contour found for {roi_name}",type="warning")
            continue
        contour = contours[-1]
        coords = np.array(contour.squeeze())
        area=cv2.contourArea(contour)

        if coords.ndim != 2 or len(coords) < 3:
            log(f"Contour is no polygon for {roi_name} : ndim= {coords.ndim}, #coords= {len(coords)}, #contours={len(contours)}",type="warning")
            continue

        min_row, min_col, max_row, max_col = region.bbox
        bounds=(min_row, min_col,max_row,max_col)
        coords = np.add(coords, np.array([min_col, min_row]))
        is_on_edge = remove_edges and (min_row <= 0 or min_col <= 0 or max_row >= edge_v or max_col >= edge_h)
        is_small =  remove_small and area < size_threshold

        key = int(is_on_edge) * 1 + int(is_small) * 2

        coords = np.asarray(coords).reshape(-1, 2)
        xpoints = np.array(coords[:, 0].astype(int))
        ypoints = np.array(coords[:, 1].astype(int))

        M = cv2.moments(contour)
        cx = int(M['m10']/M['m00'])
        cy = int(M['m01']/M['m00']) 
        center =(cx,cy)

        n = len(xpoints)
        (state, tags) = state_and_tags[key]
        roi_name: str = f"L{region.label:0{max_digits}d}"

        roi = Roi(xpoints, ypoints, name=roi_name, state=state,tags=tags,
                  bounds=bounds,
                  center =center,
                  n=n,
                  area=area)
        roi_array[region.label]=roi
    
    manager.add_from_list_unchecked(roi_array)

import cv2
import numpy as np
import matplotlib.pyplot as plt
import math
def show_contours(contours):
    n = len(contours)
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(3 * cols, 3 * rows))
    axes = np.array(axes).reshape(-1) 

    for i, cnt in enumerate(contours):
        cnt = cnt.squeeze()
        ax = axes[i]
        if cnt.ndim == 2 and cnt.shape[0] >= 3:
            ax.plot(cnt[:, 0], cnt[:, 1], color=np.random.rand(3,), linewidth=2)
        ax.set_aspect('equal')
        ax.set_title(f"Contour {i+1}")
        ax.axis('on')

    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])

    plt.tight_layout()
    plt.show()

def show_contours2(contours):
    fig, ax = plt.subplots(1, 1)
    ax.set_aspect('equal')
    ax.set_title(f"Contours")
    ax.axis('on')

    for cnt in contours:
        cnt = cnt.squeeze()
        if cnt.ndim == 2 and cnt.shape[0] >= 3:
            ax.plot(cnt[:, 0], cnt[:, 1], color=np.random.rand(3,), linewidth=1)

    plt.tight_layout()
    plt.show()



import numpy as np
import cv2
from skimage.io import imread
from TinyRoiManager import TinyRoiManager
import LabelToRoi
import StopWatch

def main():
    StopWatch.start("dummy")
    StopWatch.stop("dummy")
    StopWatch.start("dummy")
    StopWatch.stop("dummy")
    rm = TinyRoiManager()
    label_image_path = "./TestData/A_stitch_cp_masks.png"
    label_image = cv2.imread(label_image_path,cv2.IMREAD_UNCHANGED)
    StopWatch.start("Detection starting")
    process_label_image(rm, label_image)
    StopWatch.stop("Detection")

    rois = list(rm.iter_all())
    last_3= rois[-3:]

    label_image_path = "./TestData/B_stitch_cp_masks.png"
    label_image = cv2.imread(label_image_path,cv2.IMREAD_UNCHANGED)
    StopWatch.start("Detection starting")
    process_label_image(rm, label_image)
    StopWatch.stop("Detection")

    rois = list(rm.iter_all())
    last_3= rois[-3:]

    for name, roi in last_3:
        print(f"{name:8s} | {roi.n:3d} punten | state: {Roi.state_to_str(roi.state)} | tags: {roi.tags}")

    label_image_path = "./TestData/C_Stitch_cp_masks.png"
    label_image = cv2.imread(label_image_path,cv2.IMREAD_UNCHANGED)
    StopWatch.start("Detection starting")
    process_label_image(rm, label_image)
    StopWatch.stop("Detection")

    rois = list(rm.iter_all())
    last_3= rois[-3:]

    for name, roi in last_3:
        print(f"{name:8s} | {roi.n:3d} punten | state: {Roi.state_to_str(roi.state)} | tags: {roi.tags}")


if __name__ == "__main__":
    main()
