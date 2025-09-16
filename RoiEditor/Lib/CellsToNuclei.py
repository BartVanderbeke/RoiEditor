from typing import List
import numpy as np
import matplotlib.pyplot as plt
from skimage.io import imread
from skimage.color import rgb2hsv
import cv2
from skimage.morphology import opening, disk

import logging


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


def cells_to_nuclei(bkg_image: np.ndarray, cell_lbl_image: np.ndarray, parent_rm: TinyRoiManager) -> List[Roi]:
    """
    Convert cell labels to nuclei information.

    Args:
        bkg_image: RGB background image as numpy array
        cell_lbl_image: Label image with cell segmentation as numpy array

    Returns:
        tuple containing:
            - dictionary with nuclei information
            - numpy array with nucleus labels
    """
    # to find labels in between cells we need an opened version of the label image
    opened_cell_lbl_img = __open_between_labels(cell_lbl_image)
    # to avoid nuclei in parts where cellpose did not detect cells
    # we need a closed version of the cell label image
    # closed_cell_lbl_img = include gaps between cells but do not 
    # include parts where cellpose did not detect cells
    closed_cell_lbl_img = opening(cell_lbl_image, disk(3))
    mask_closed_cell_lbl = closed_cell_lbl_img != 0 

    img_rgb = bkg_image.copy().astype(np.float32) / 255.0
    img_hsv = rgb2hsv(img_rgb)
    HH, SS, VV = img_hsv[...,0], img_hsv[...,1], img_hsv[...,2]

    # step 1: create mask for nuclei in fibers filtering on color
    # HSV are converted from the paint.net values to skimage values

    mask_nuclei_in_fiber = (
        (HH > 200.0/360.0) & (HH <= 300.0/360.0) &
        (SS >= 20.0/100.0)
    )


    mask_opened_cell_lbl = (opened_cell_lbl_img != 0).astype(np.uint8)  # 0/1
    binary255 = mask_opened_cell_lbl * 255                               # 0/255 (CV_8U)

    maskSize = cv2.DIST_MASK_PRECISE

    dist_inside  = cv2.distanceTransform(binary255,        cv2.DIST_L2, maskSize).astype(np.float32)
    dist_outside = cv2.distanceTransform(255 - binary255,  cv2.DIST_L2, maskSize).astype(np.float32)


    distmap = dist_inside - dist_outside

    # step 2: image with labels
    binary = (mask_nuclei_in_fiber.astype(np.uint8))  # 0/1 mask

    num_labels, nucleus_label_img, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
    unique_labels = np.unique(nucleus_label_img)
    unique_labels = unique_labels[unique_labels != 0]
    if not np.all(unique_labels > 0):
        log("No nuclei found in cell image", type="warning")
        return []
    # remove nuclei outside of cells
    nucleus_label_img = nucleus_label_img * mask_closed_cell_lbl

    # step 3: collect all nuclei
    min_area = 10
    #nuke_dict = {}
    max_digits: int = len(str(num_labels))
    roi_list: List[Roi] = []
    skipped_nuclei = 0
    for i in range(1, num_labels):  # skip label 0 (background)
        area = stats[i, cv2.CC_STAT_AREA]
        if area < min_area:
            skipped_nuclei += 1
            continue
        
        cx, cy = centroids[i]  # (x,y) in float
        x, y = int(cx), int(cy)
        nucleus_idx = nucleus_label_img[y, x]
        
        # Get bounding box from connectedComponents
        bbox_x = stats[i, cv2.CC_STAT_LEFT]
        bbox_y = stats[i, cv2.CC_STAT_TOP]
        bbox_w = stats[i, cv2.CC_STAT_WIDTH]
        bbox_h = stats[i, cv2.CC_STAT_HEIGHT]
        
        # Extract just this nucleus region
        nucleus_region = (nucleus_label_img == i)[bbox_y:bbox_y+bbox_h, bbox_x:bbox_x+bbox_w]
        nucleus_binary = nucleus_region.astype(np.uint8) * 255
        
        # Find contours in the small region of the bounding box: should only be one
        contours, _ = cv2.findContours(nucleus_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            skipped_nuclei += 1
            continue
            
        # Get the largest contour (should be the nucleus)
        largest_contour_at_origin = max(contours, key=cv2.contourArea)
        
        # Convert back to full image coordinates
        translated_contour = largest_contour_at_origin + np.array([bbox_x, bbox_y])
        
        # Extract polygon points
        polygon_points = translated_contour.reshape(-1, 2)
        xpoints = polygon_points[:, 0].astype(float)
        ypoints = polygon_points[:, 1].astype(float)
        if len(xpoints) < 3 or len(ypoints) < 3:
            skipped_nuclei += 1
            continue
        assert len(xpoints) == len(ypoints), "xpoints and ypoints must have the same length"
        
        # Calculate accurate bounds from polygon
        min_x, max_x = int(np.min(xpoints)), int(np.max(xpoints))
        min_y, max_y = int(np.min(ypoints)), int(np.max(ypoints))
        
        nuke_roi_name: str = f"N{nucleus_idx:0{max_digits}d}"
        center = (x, y)
        nuke_roi: Roi = Roi(
            xpoints=xpoints,
            ypoints=ypoints,
            name=nuke_roi_name,
            bounds=(min_y, min_x, max_y, max_x),
            center=center,
            n=len(xpoints),
            area=area,
            state=Roi.ROI_STATE_ACTIVE
            )
        parent_cell_idx = cell_lbl_image[y, x]
        if  parent_cell_idx > 0 and parent_rm is not None:
            parent_cell_name = parent_rm.idx_to_name(parent_cell_idx)
            parent_cell_roi = parent_rm.get_roi(parent_cell_name)
            if parent_cell_roi:
                nuke_roi.parent = parent_cell_roi
                if nuke_roi.parent.children is None:
                    nuke_roi.parent.children = list([nuke_roi])
                else:
                    nuke_roi.parent.children.append(nuke_roi)
                if nuke_roi.parent.state == Roi.ROI_STATE_DELETED:
                    nuke_roi.state = Roi.ROI_STATE_DELETED

            
        roi_list.append(nuke_roi)



        if distmap[y,x] < 0:
            nuke_roi.state = Roi.ROI_STATE_DELETED
            nuke_roi.tags.add("DELETED.OUTSIDE_CELL")
            continue
        if distmap[y,x] < 2:
            nuke_roi.state = Roi.ROI_STATE_DELETED
            nuke_roi.tags.add("DELETED.CLOSE_TO_CELL_BORDER")

    if skipped_nuclei > 0:
        if skipped_nuclei == 1:
            log(f"Skipped 1 malformed or too small nucleus", type="warning")
        else:
            log(f"Skipped {skipped_nuclei} malformed or too small nuclei", type="warning")


    return roi_list

if __name__ == "__main__":
    # Input file
    filename = "./RoiEditor/TestData/infolder/dir1/6_1.tif"
    label_filename = "./RoiEditor/TestData/infolder/dir1/6_1_cp_masks.png"

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
