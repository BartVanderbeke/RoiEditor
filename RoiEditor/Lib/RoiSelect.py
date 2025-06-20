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

from .TinyRoiManager import TinyRoiManager 
from .TinyLog import log


def select_outer_rois_vdb(rm: TinyRoiManager, step: int = 10):
    """
        selects the outer edge of the cloud of ROIs by binning them
        according to the angle of the gravity point of the ROI
        relative to the gravity point of the cloud
        In each bin the furthest one is considered to be on the edge
    """
    if not len(rm):
        log("select_outer_rois_vdb: No ROIs in ROI Manager",type="warning")
        return

    # Lijst met (x, y, roi) tuples
    roi_centers = [(roi.center[0], roi.center[1], roi) for _,roi in rm]

    coords = np.array([(x, y) for x, y, _ in roi_centers])
    x_avg = coords[:, 0].mean()
    y_avg = coords[:, 1].mean()

    num_bins = 360 // step
    furthest_in_bin = [(-1, None)] * num_bins

    for x, y, roi in roi_centers:
        dx = x - x_avg
        dy = y - y_avg
        r = np.hypot(dx, dy)
        theta_deg = int(np.degrees(np.atan2(dy, dx))) % 360
        theta_bin_deg = (theta_deg // step) % num_bins

        if r > furthest_in_bin[theta_bin_deg][0]:
            furthest_in_bin[theta_bin_deg] = (r, roi)

    to_be_selected_rois = list({roi for r, roi in furthest_in_bin if roi is not None})
    rm.select(to_be_selected_rois, reason_of_selection="edge.section", additive=True)
    log(f"Selected {len(to_be_selected_rois)} ROIs over {num_bins} bins.")

def select_outer_rois_vdb3(rm: TinyRoiManager, step: int = 10):
    """
    selects the outer edge of the cloud of ROIs by binning them
    according to the angle of the furthest corner of the bounding box of the ROI
    relative to the gravity point of the cloud
    In each bin the furthest one is considered to be on the edge
    """
    if not len(rm):
        log("select_outer_rois_vdb: No ROIs in ROI Manager",type="warning")
        return

    # Eerst zwaartepunt bepalen op basis van centerpunten
    centers = np.array([roi.center for _,roi in rm])
    x_avg = centers[:, 0].mean()
    y_avg = centers[:, 1].mean()

    # Dan voor elke ROI het verst verwijderde hoekpunt bepalen
    def furthest_corner(roi):
        top, left, bottom, right = roi.bounds
        corners = [
            (left, top),
            (right, top),
            (right, bottom),
            (left, bottom)
        ]
        (x,y) = max(corners, key=lambda pt: np.hypot(pt[0] - x_avg, pt[1] - y_avg))
        # Maximaliseer afstand tot (x_avg, y_avg)
        return (x,y,roi)

    # Lijst met (x, y, roi) waar (x, y) het hoekpunt is
    corner_points = [furthest_corner(roi) for _,roi in rm]

    # Bin-invulling zoals voorheen
    num_bins = 360 // step
    furthest_in_bin = [(-1, None)] * num_bins

    for x, y, roi in corner_points:
        dx = x - x_avg
        dy = y - y_avg
        r = np.hypot(dx, dy)
        theta_deg = int(np.degrees(np.atan2(dy, dx))) % 360
        theta_bin_deg = (theta_deg // step) % num_bins

        if r > furthest_in_bin[theta_bin_deg][0]:
            furthest_in_bin[theta_bin_deg] = (r, roi)

    to_be_selected_rois = list({roi for r, roi in furthest_in_bin if roi is not None})
    rm.select(to_be_selected_rois, reason_of_selection="edge.section", additive=True)
    log(f"Selected {len(to_be_selected_rois)} ROIs over {num_bins} bins.")


def select_outer_rois_vdb4(rm: TinyRoiManager, step: int = 10):
    """
        selects the outer edge by dilating the cloud of ROIs
        and then considering the difference between original label image
        and dilated to be the edge
    """
    if not len(rm):
        log("select_outer_rois_vdb4: No ROIs in ROI Manager",type="warning")
        return

    centers = np.array([roi.center for _,roi in rm])
    x_avg = centers[:, 0].mean()
    y_avg = centers[:, 1].mean()

    # Bepaal het verst verwijderde punt uit alle polygon-punten
    def furthest_shape_point(roi):
        points = zip(roi.xpoints, roi.ypoints)
        x, y = max(points, key=lambda pt: np.hypot(pt[0] - x_avg, pt[1] - y_avg))
        return (x, y, roi)

    # Bereken voor elke ROI het punt dat het verst ligt van het zwaartepunt
    furthest_points = [furthest_shape_point(roi) for _,roi in rm]

    num_bins = 360 // step
    furthest_in_bin = [(-1, None)] * num_bins

    for x, y, roi in furthest_points:
        dx = x - x_avg
        dy = y - y_avg
        r = np.hypot(dx, dy)
        theta_deg = int(np.degrees(np.atan2(dy, dx))) % 360
        theta_bin_deg = (theta_deg // step) % num_bins

        if r > furthest_in_bin[theta_bin_deg][0]:
            furthest_in_bin[theta_bin_deg] = (r, roi)

    to_be_selected_rois = list({roi for r, roi in furthest_in_bin if roi is not None})
    rm.select(to_be_selected_rois, reason_of_selection="edge.section", additive=True)
    log(f"select_outer_rois_vdb4: Selected {len(to_be_selected_rois)} ROIs over {num_bins} bins.")



def select_outer_rois_vdb5(rm: TinyRoiManager, filtered_label_image: np.ndarray):
    if not len(rm):
        log("select_outer_rois_vdb5: No ROIs in ROI Manager",type="warning")
        return
    assert filtered_label_image is not None
    # Step 1: binary image of all ROis
    binary_mask = (filtered_label_image > 0).astype(np.uint8) * 255

    # Step 2: morphological closing (dilate + erode): fill the gaps
    kernel = np.ones((5, 5), dtype=np.uint8)
    closed_mask = cv2.erode(cv2.dilate(binary_mask, kernel, iterations=5), kernel, iterations=5)

    # Step 3: outer contour of all ROis
    contours, _ = cv2.findContours(closed_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    outer_mask = np.zeros_like(closed_mask)
    cv2.drawContours(image=outer_mask, contours=contours, contourIdx=-1, color=255, thickness=10)

    # Step 4: get the label values for labels intersecting with contour
    roi_labels_on_edge = np.unique(filtered_label_image[outer_mask > 0])
    roi_labels_on_edge = roi_labels_on_edge[roi_labels_on_edge > 0]  # verwijder achtergrond

    # Step 5: convert label idx to actual ROIs
    selected_rois =[]
    for label in roi_labels_on_edge:
        roi =rm.get_roi(rm.idx_to_name(label))
        if roi:
            selected_rois.append(roi)
        else:
            log(f"No roi found for label: {label}/{rm.idx_to_name(label)}",type="warning")

    selected_rois = np.array(selected_rois)

    #selected_rois = np.array([rm.get_roi(rm.idx_to_name(label)) for label in roi_labels_on_edge])

    # Step 6: select ROIs
    rm.select(selected_rois, reason_of_selection="edge.outer", additive=True)
    log(f"Selected {len(selected_rois)} ROIs from outer contour.")
