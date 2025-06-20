"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

This module implements the calculation of Feret values for the ROIs.
The algorithms are borrowed from the Fiji Java implementation

"""
import numpy as np
from math import atan2, pi
import numpy.typing as npt
import cv2
from numba import njit

from .TinyLog import log
feret_index ={
        "Feret": 0,
        "FeretAngle": 1,
        "AngleShifted": 2,
        "MinFeret": 3,
        "FeretX": 4,
        "FeretY": 5,
        "FeretRatio": 6,
    }
feret_msmts = ["Feret", "FeretAngle", "AngleShifted","MinFeret", "FeretX", "FeretY", "FeretRatio"]
feret_quantities = ["length","angle","angle","length","length","length",""]
feret_units = ["px","deg","deg","px","px","px",""]
feret_scalers = [1.0,1.0,1.0,1.0,1.0,1.0,1.0]

def get_values(x_points:npt.NDArray[np.int_], y_points:npt.NDArray[np.int_]):
    assert len(x_points) == len(y_points), "size of x_points and y_points must be the same"
    assert len(x_points) > 2, "Too few points for Feret calculations"

    x_points = np.array(x_points,dtype=np.float32)
    y_points = np.array(y_points,dtype=np.float32)
    points = np.stack((x_points, y_points), axis=1)

    hull_pts = cv2.convexHull(points).squeeze()

    p1 = hull_pts
    p2 = np.roll(hull_pts, -1, axis=0)
    dxy = p2 - p1
    dx, dy = dxy[:, 0], dxy[:, 1]
    h = np.hypot(dx, dy)
    sin_a = -dy / h
    cos_a = dx / h

    RTs = np.stack([
        np.stack([cos_a, sin_a], axis=1),
        np.stack([-sin_a, cos_a], axis=1)
    ], axis=2)  # vorm: (n, 2, 2)

    rotated = np.array([hull_pts @ R.T for R in RTs], dtype=np.float32)
    x_proj = rotated[:, :, 0]
    y_proj = rotated[:, :, 1]

    lengths = x_proj.max(axis=1) - x_proj.min(axis=1)
    widths = y_proj.max(axis=1) - y_proj.min(axis=1)

    idx_max = np.argmax(lengths)
    idx_min = np.argmin(widths)

    max_diameter = lengths[idx_max]
    min_width = widths[idx_min]

    # Herbereken Feret-puntparen
    proj = x_proj[idx_max]
    i_max = np.argmax(proj)
    i_min = np.argmin(proj)
    pt1 = hull_pts[i_max]
    pt2 = hull_pts[i_min]

    if (pt1[0] < pt2[0]) or (pt1[0] == pt2[0] and pt1[1] < pt2[1]):
        feret = pt1
        vec = pt2 - pt1
    else:
        feret = pt2
        vec = pt1 - pt2

    angle_of_max =np.degrees(np.arctan2(vec[1], vec[0]) ) % 180
    if min_width >= 1:
        feret_ratio = max_diameter/min_width
    else:
        feret_ratio = max_diameter
        log("ROI with zero min width in Feret calculations","warning")
    angle_shifted = (angle_of_max + 90.0) % 180

    #return np.array([max_diameter, angle_of_max,angle_shifted, min_width, feret_x, feret_y,feret_ratio])
    out = np.empty(7, dtype=np.float32)
    out[0] = max_diameter
    out[1] = angle_of_max
    out[2] = angle_shifted
    out[3] = min_width
    out[4] = feret[0]
    out[5] = feret[1]
    out[6] = feret_ratio
    return out


@njit(nogil=True)
def arrange(pt1, pt2):
    if (pt1[0] < pt2[0]) or (pt1[0] == pt2[0] and pt1[1] < pt2[1]):
        feret = pt1
        vec = pt2 - pt1
    else:
        feret = pt2
        vec = pt1 - pt2
    return feret, vec


def get_values2(x_points: npt.NDArray[np.int_], y_points: npt.NDArray[np.int_]):
    assert len(x_points) == len(y_points), "size of x_points and y_points must be the same"
    assert len(x_points) > 2, "Too few points for Feret calculations"

    x_points = np.array(x_points, dtype=np.float32)
    y_points = np.array(y_points, dtype=np.float32)
    points = np.stack((x_points, y_points), axis=1)

    hull_pts = cv2.convexHull(points)

    # Gebruik minAreaRect als snelle Feret-berekening
    rect = cv2.minAreaRect(hull_pts)
    (cx, cy), (width, height), angle = rect

    max_diameter = max(width, height)
    min_width = min(width, height)

    # Corrigeer hoek zoals in originele code (altijd tussen 0 en 180)
    angle_of_max = angle
    if width < height:
        angle_of_max = (angle + 90) % 180
    else:
        angle_of_max = angle % 180

    # Benadering van startpunt: linker-onderhoek van rechthoek
    feret_x, feret_y = cx, cy

    feret_ratio = max_diameter/min_width
    angle_shifted = (angle_of_max + 90.0) % 180

    return np.array([max_diameter, angle_of_max,angle_shifted, min_width, feret_x, feret_y,feret_ratio])
