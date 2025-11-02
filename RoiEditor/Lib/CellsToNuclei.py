"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
from typing import List
import numpy as np
import matplotlib.pyplot as plt
from skimage.io import imread
from skimage.color import rgb2hsv
import cv2
from skimage.morphology import opening, disk

import logging
from StopWatch import StopWatch


logging.getLogger("tifffile").setLevel(logging.ERROR)
from Roi import Roi
from TinyRoiManager import TinyRoiManager
from TinyLog import log


def __open_between_labels(label_img):
    """
        creates 2 pixel openings between adjacent labels or
        1 pixel on transitions from background to a label
    """
    img = label_img.copy()

    h1 = img[:, :-1] # all cols except last
    h2 = img[:, 1:]  # all cols except first
    vert_edge = (h1 != h2) # diff between cols is a vertical edge

    v1 = img[:-1, :] # all rows except last
    v2 = img[1:, :]  # all rows except first
    hor_edge = (v1 != v2) # diff between rows is a horizontal edge

    img[:, :-1][vert_edge] = 0
    img[:, 1:][vert_edge] = 0
    img[:-1, :][hor_edge] = 0
    img[1:, :][hor_edge] = 0

    return img

kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))

def cells_to_nuclei(bkg_image: np.ndarray, cell_lbl_image: np.ndarray, parent_rm: TinyRoiManager) -> np.ndarray:
    """
    Convert cell labels to nuclei information.

    Args:
        bkg_image: RGB background image as numpy array
        cell_lbl_image: Label image with cell segmentation as numpy array

    Returns:
        list of Roi objects (nuclei)
    """

    StopWatch.start()

    img_rgb = bkg_image.copy()

    img_hsv= cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV).astype(np.uint8)
    HH, SS, VV = img_hsv[...,0], img_hsv[...,1], img_hsv[...,2]

    # step 1: create mask for nuclei in fibers filtering on color
    # HSV are converted from the paint.net values to opencv values
    mask_nuclei = (
        (HH > 200//2) & (HH <= 300//2) & # CV2 HSV H 0..180 S 0..255 V 0..255
        (SS > int(20.0/100.0*255.0)) &
        (VV < int(235.0/100.0*255.0))
    ).astype(np.uint8)

    opened_cell_lbl_img = __open_between_labels(cell_lbl_image).astype(np.uint8)
    opened_cell_lbl_img[opened_cell_lbl_img != 0] = 255


    maskSize = cv2.DIST_MASK_PRECISE

    dist_inside  = cv2.distanceTransform(opened_cell_lbl_img,        cv2.DIST_L2, maskSize).astype(np.float32)
    dist_outside = cv2.distanceTransform(255 - opened_cell_lbl_img,  cv2.DIST_L2, maskSize).astype(np.float32)

    distmap = dist_inside - dist_outside

    min_area = 8
    _, nucleus_label_img, stats, _ = cv2.connectedComponentsWithStats(mask_nuclei, connectivity=8)
    nucleus_label_img *= np.isin(
        nucleus_label_img,
        np.where(stats[:, cv2.CC_STAT_AREA] >= min_area)[0][1:]  # skip achtergrond (0)
    )

    deleted_nuclei = 0

    binary_nucleus_label_img = (nucleus_label_img > 0).astype(np.uint8) * 255
    _contours, _ = cv2.findContours(binary_nucleus_label_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = [cnt for cnt in _contours if cv2.contourArea(cnt) > 0]

    max = np.unique(nucleus_label_img).max()
    roi_array = np.full(shape=max+1,fill_value=None,dtype=Roi)
    max_digits=len(str( len(roi_array) ))

    for contour in contours:
        coords = np.array(contour.squeeze()).reshape(-1, 2)

        M = cv2.moments(contour)
        m00 = cv2.contourArea(contour)

        cx, cy = int(M['m10']/m00), int(M['m01']/m00)


        label_value = nucleus_label_img[cy,cx]
        if label_value ==0 or coords.ndim != 2 or len(coords) < 3:
            continue

        xpoints = np.array(coords[:, 0],dtype=np.int_)
        ypoints = np.array(coords[:, 1],dtype=np.int_)
        n = len(xpoints)


        left, top, w, h = cv2.boundingRect(contour)
        right= left + w
        bottom = top + h

        area=cv2.contourArea(contour)
        roi_name: str = f"N{label_value:0{max_digits}d}"

        nuke_roi = Roi(
            xpoints=xpoints,
            ypoints=ypoints,
            name=roi_name,
            bounds =(top,left,bottom,right),
            center =(cx,cy),
            state=Roi.ROI_STATE_DELETED,
            n=n,
            area=area
        )
        roi_array[label_value]=nuke_roi

        parent_cell_idx = cell_lbl_image[cy, cx]
        parent_cell_roi = (
            parent_rm.get_roi(parent_rm.idx_to_name(parent_cell_idx))
            if parent_cell_idx > 0 and parent_rm is not None
            else None
        )
        nuke_roi.parent= None
        d = distmap[cy, cx]

        nuke_roi.parent = parent_cell_roi
        if not parent_cell_roi:
            deleted_nuclei += 1
            nuke_roi.tags.add("DELETED.OUTSIDE_CELL")
            continue

        if d < 0:
            deleted_nuclei += 1
            nuke_roi.tags.add("DELETED.OUTSIDE_CELL")
            continue

        
        # d >= 0 --> in cell
        parent_cell_roi.children.append(nuke_roi)
        if d < 2:
            deleted_nuclei += 1
            nuke_roi.tags.add("DELETED.CLOSE_TO_CELL_BORDER")
            continue

        
        if parent_cell_roi.state == Roi.ROI_STATE_DELETED:
            deleted_nuclei += 1
            nuke_roi.tags.add("DELETED.WITH_PARENT")
            continue

        nuke_roi.state = Roi.ROI_STATE_ACTIVE

    if deleted_nuclei > 0:
            if deleted_nuclei == 1:
                log(f"Deleted 1 nucleus outside of cell or on edge of cell", type="info")
            else:
                log(f"Deleted {deleted_nuclei} nuclei outside of cell or on edge of cell", type="info")

    StopWatch.stop("Building nuke ROIs")
    return roi_array

if __name__ == "__main__":

    # Input file
    filename = "C:\\Users\\bimba\\OneDrive\\Documenten\\source\\repos\\RoiProject\\RoiEditor\\tests\\TestData\\6_1.tif"
    label_filename = "C:\\Users\\bimba\\OneDrive\\Documenten\\source\\repos\\RoiProject\\RoiEditor\\tests\\TestData\\6_1_cp_masks.png"

    bkg_image = imread(filename)
    cell_lbl_image = imread(label_filename)

    roi_array = cells_to_nuclei(bkg_image, cell_lbl_image, parent_rm=None)

    fig, axes = plt.subplots(1, 1, figsize=(10, 5))
    axes.imshow(bkg_image)
    axes.axis("off")

    for nuke in roi_array[1:]:  # skip background
        if nuke is None:
            continue
        x,y = nuke.center
        axes.plot(x, y, marker="X", color= "cyan")


    plt.tight_layout()
    plt.show()
