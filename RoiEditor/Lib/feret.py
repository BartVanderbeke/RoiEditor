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
import numpy.typing as npt
import cv2
from numba import njit

from tiny_log import log
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


@njit(cache=True)
def _arrange_points(pt1_x: np.float32, pt1_y: np.float32, pt2_x: np.float32, pt2_y: np.float32):
    if (pt1_x < pt2_x) or (pt1_x == pt2_x and pt1_y < pt2_y):
        feret_x = pt1_x
        feret_y = pt1_y
        vec_x = pt2_x - pt1_x
        vec_y = pt2_y - pt1_y
    else:
        feret_x = pt2_x
        feret_y = pt2_y
        vec_x = pt1_x - pt2_x
        vec_y = pt1_y - pt2_y
    return feret_x, feret_y, vec_x, vec_y


@njit(cache=True)
def _feret_from_hull_jit(hull_pts):
    n = hull_pts.shape[0]
    lengths = np.empty(n, dtype=np.float32)
    widths = np.empty(n, dtype=np.float32)
    edge_cos = np.empty(n, dtype=np.float32)
    edge_sin = np.empty(n, dtype=np.float32)

    idx_max = 0
    idx_min = 0
    best_len = np.float32(-1.0)
    best_width = np.float32(1.0e30)

    for i in range(n):
        j = i + 1
        if j >= n:
            j = 0

        p1_x = hull_pts[i, 0]
        p1_y = hull_pts[i, 1]
        p2_x = hull_pts[j, 0]
        p2_y = hull_pts[j, 1]

        dx = p2_x - p1_x
        dy = p2_y - p1_y
        h = np.sqrt(dx * dx + dy * dy)
        if h <= 1.0e-12:
            h = 1.0

        cos_a = dx / h
        sin_a = -dy / h
        edge_cos[i] = cos_a
        edge_sin[i] = sin_a

        min_x = np.float32(1.0e30)
        max_x = np.float32(-1.0e30)
        min_y = np.float32(1.0e30)
        max_y = np.float32(-1.0e30)

        for k in range(n):
            x = hull_pts[k, 0]
            y = hull_pts[k, 1]
            x_rot = x * cos_a + y * sin_a
            y_rot = -x * sin_a + y * cos_a

            if x_rot < min_x:
                min_x = x_rot
            if x_rot > max_x:
                max_x = x_rot
            if y_rot < min_y:
                min_y = y_rot
            if y_rot > max_y:
                max_y = y_rot

        length = max_x - min_x
        width = max_y - min_y
        lengths[i] = length
        widths[i] = width

        if length > best_len:
            best_len = length
            idx_max = i
        if width < best_width:
            best_width = width
            idx_min = i

    max_diameter = lengths[idx_max]
    min_width = widths[idx_min]

    cos_m = edge_cos[idx_max]
    sin_m = edge_sin[idx_max]
    max_proj = np.float32(-1.0e30)
    min_proj = np.float32(1.0e30)
    i_max = 0
    i_min = 0

    for k in range(n):
        x = hull_pts[k, 0]
        y = hull_pts[k, 1]
        proj = x * cos_m + y * sin_m
        if proj > max_proj:
            max_proj = proj
            i_max = k
        if proj < min_proj:
            min_proj = proj
            i_min = k

    pt1_x = hull_pts[i_max, 0]
    pt1_y = hull_pts[i_max, 1]
    pt2_x = hull_pts[i_min, 0]
    pt2_y = hull_pts[i_min, 1]

    feret_x, feret_y, vec_x, vec_y = _arrange_points(pt1_x, pt1_y, pt2_x, pt2_y)

    angle_of_max = (np.arctan2(vec_y, vec_x) * np.float32(57.29577951308232)) % np.float32(180.0)
    angle_shifted = (angle_of_max + np.float32(90.0)) % np.float32(180.0)
    feret_ratio = max_diameter / min_width if min_width >= 1.0 else max_diameter

    out = np.empty(7, dtype=np.float32)
    out[0] = max_diameter
    out[1] = angle_of_max
    out[2] = angle_shifted
    out[3] = min_width
    out[4] = feret_x
    out[5] = feret_y
    out[6] = feret_ratio
    return out


def get_values(x_points:npt.NDArray[np.int_], y_points:npt.NDArray[np.int_]):
    assert len(x_points) == len(y_points), "size of x_points and y_points must be the same"
    assert len(x_points) > 2, "Too few points for Feret calculations"

    x_points = np.asarray(x_points, dtype=np.float32)
    y_points = np.asarray(y_points, dtype=np.float32)
    points = np.empty((len(x_points), 2), dtype=np.float32)
    points[:, 0] = x_points
    points[:, 1] = y_points

    hull_pts = cv2.convexHull(points).reshape(-1, 2).astype(np.float32, copy=False)
    hull_pts = np.ascontiguousarray(hull_pts)

    out = _feret_from_hull_jit(hull_pts)
    if out[3] < 1.0:
        log("ROI with zero min width in Feret calculations","error")
    return out


def arrange(pt1, pt2):
    feret_x, feret_y, vec_x, vec_y = _arrange_points(
        np.float32(pt1[0]),
        np.float32(pt1[1]),
        np.float32(pt2[0]),
        np.float32(pt2[1]),
    )
    feret = np.array([feret_x, feret_y], dtype=np.float32)
    vec = np.array([vec_x, vec_y], dtype=np.float32)
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
