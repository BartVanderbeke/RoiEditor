
import os
import sys
import numpy as np
import cv2
from skimage.io import imread

import matplotlib.pyplot as plt
import math

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from RoiEditor.Lib.TinyRoiManager import TinyRoiManager
from RoiEditor.Lib.LabelToRoiDiff import process_label_image
from RoiEditor.Lib.StopWatch import StopWatch
from RoiEditor.Lib.Roi import Roi


def show_contours(contours):
    n = len(contours)
    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(3 * cols, 3 * rows))
    axes = np.array(axes).reshape(-1) 
    i=0
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

def test_labeltoroidiff():
    base_path = os.path.dirname(__file__)
    test_path = os.path.join(base_path, "TestData")+'/'

    StopWatch.start("dummy")
    StopWatch.stop("dummy")
    StopWatch.start("dummy")
    StopWatch.stop("dummy")
    rm = TinyRoiManager()
    label_image_path = test_path+"A_stitch_cp_masks.png"
    label_image = cv2.imread(label_image_path,cv2.IMREAD_UNCHANGED)
    StopWatch.start("Detection starting")
    process_label_image(rm, label_image)
    StopWatch.stop("Detection")

    rois = list(rm.iter_all())
    last_3= rois[-3:]

    label_image_path = test_path+"B_stitch_cp_masks.png"
    label_image = cv2.imread(label_image_path,cv2.IMREAD_UNCHANGED)
    StopWatch.start("Detection starting")
    process_label_image(rm, label_image)
    StopWatch.stop("Detection")

    rois = list(rm.iter_all())
    last_3= rois[-3:]

    for name, roi in last_3:
        print(f"{name:8s} | {roi.n:3d} punten | state: {Roi.state_to_str(roi.state)} | tags: {roi.tags}")

    label_image_path = test_path+"C_Stitch_cp_masks.png"
    label_image = cv2.imread(label_image_path,cv2.IMREAD_UNCHANGED)
    StopWatch.start("Detection starting")
    process_label_image(rm, label_image)
    StopWatch.stop("Detection")

    rois = list(rm.iter_all())
    last_3= rois[-3:]

    for name, roi in last_3:
        print(f"{name:8s} | {roi.n:3d} punten | state: {Roi.state_to_str(roi.state)} | tags: {roi.tags}")


if __name__ == "__main__":
    test_labeltoroidiff()
