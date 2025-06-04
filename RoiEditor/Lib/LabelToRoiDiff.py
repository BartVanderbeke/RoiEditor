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
import matplotlib.pyplot as plt

from .Roi import Roi
from .StopWatch import *
from .TinyRoiManager import TinyRoiManager

state_and_tags = {0: (Roi.ROI_STATE_ACTIVE,set()),
        1: (Roi.ROI_STATE_DELETED, set(["edge.image"])),
        2: (Roi.ROI_STATE_DELETED,set(["small"])),
        3: (Roi.ROI_STATE_DELETED, set(["edge.image"]))
}

def remove_internal_edges(label_img):
    """
        creates openings between adjacent labels or
        transitions from background to a label
        so findContours can be applied to the complete image
    """
    img = label_img.copy()

    h1 = img[:, :-1]
    h2 = img[:, 1:]
    hor_edge = (h1 != h2) #(h1 != 0) & (h2 != 0) & (h1 != h2)

    v1 = img[:-1, :]
    v2 = img[1:, :]
    ver_edge = (v1 != v2) #(v1 != 0) & (v2 != 0) & (v1 != v2)

    img[:, :-1][hor_edge] = 0
    img[:, 1:][hor_edge] = 0
    img[:-1, :][ver_edge] = 0
    img[1:, :][ver_edge] = 0

    return img.astype(np.uint8)

def erase_label_edges(label_img):
    """
        creates openings between adjacent labels by using a diff,
        so findContours can be applied to the complete image
    """
    result = label_img.copy()

    # Horizontal transitions
    diff_h = label_img[:, :-1] != label_img[:, 1:]
    result[:, :-1][diff_h] = 0
    result[:,  1:][diff_h] = 0

    # Vertical transitions
    diff_v = label_img[:-1, :] != label_img[1:, :]
    result[:-1, :][diff_v] = 0
    result[ 1:, :][diff_v] = 0

    return result




def process_label_image(rm: TinyRoiManager, label_image: np.ndarray, remove_edges: bool = True, remove_small: bool = True, size_threshold: int = 100) -> None:
    
    height, width = label_image.shape
    edge_h: int = width-1
    edge_v: int = height-1

    edge_h = width - 1
    edge_v = height - 1

    lbl_img = remove_internal_edges(label_image)
    lbl_img = (lbl_img > 0).astype(np.uint8) * 255
    
    contours, _ = cv2.findContours(lbl_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    roi_array = np.full(shape=len(contours)+100,fill_value=None,dtype=Roi)
    max_digits=len(str( len(roi_array) ))
    corr = np.sqrt(1.00215)


    if not contours:
        print(f"label image doen not contain contours!")
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

        xpoints = np.array(coords[:, 0])
        ypoints = np.array(coords[:, 1])
        n = len(xpoints)

        label_value = label_image[cy,cx]
        if label_value ==0:
            continue
        if coords.ndim != 2 or len(coords) < 3:
            print(f"Contour is no polygon for {str(label_value)} : ndim= {coords.ndim}, #coords= {len(coords)}, #contours={len(contours)}",type="warning")
            continue

        left, top, w, h = cv2.boundingRect(contour)
        right= left + w
        bottom = top + h

        area=cv2.contourArea(contour)

        is_on_edge = remove_edges and (top <= 0 or left <= 0 or bottom >= edge_v or right >= edge_h)
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

if __name__ == "__main__":
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
        print(f"{name:8s} | {roi.n:3d} points | state: {Roi.state_to_str(roi.state)} | tags: {roi.tags}")

    label_image_path = "./TestData/C_Stitch_cp_masks.png"
    label_image = cv2.imread(label_image_path,cv2.IMREAD_UNCHANGED)
    StopWatch.start("Detection starting")
    process_label_image(rm, label_image)
    StopWatch.stop("Detection")


    rois = list(rm.iter_all())
    last_3= rois[-3:]

    for name, roi in last_3:
        print(f"{name:8s} | {roi.n:3d} points | state: {Roi.state_to_str(roi.state)} | tags: {roi.tags}")

    lbl_img = erase_label_edges(label_image)
    lbl_img = (lbl_img > 0).astype(np.uint8) * 255
    contours, _ = cv2.findContours(lbl_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    show_contours2(contours)
