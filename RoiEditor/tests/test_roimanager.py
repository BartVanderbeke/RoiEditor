import os
import sys
import numpy as np
import cv2

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from RoiEditor.Lib.TinyRoiManager import TinyRoiManager
from RoiEditor.Lib.TinyRoiFile import TinyRoiFile as TRF
from RoiEditor.Lib.StopWatch import StopWatch


def test_roimanager():
    base_path = os.path.dirname(__file__)
    test_path = os.path.join(base_path, "TestData")+'/'

    base_name=test_path+"A_Stitch"
    zip_path = base_name+"_rois.zip"
    zip_out_path = base_name+"_RoiSet.zip"
    label_path = base_name+"_cp_masks.png"
    label_image: np.ndarray= cv2.imread(label_path, cv2.IMREAD_UNCHANGED)
    num_threads = 12
    num_feret_threads =1
    rm = TinyRoiManager()
    StopWatch.start("starting roi read")

    rois = TRF.read_parallel(zip_path, label_image, num_threads=num_threads)
    StopWatch.stop("roi read")
    for roi in rois:
        if roi:
            rm.add_unchecked(roi)

    StopWatch.start("Feret")
    rm.force_feret()
    StopWatch.stop("Feret")

    StopWatch.start("starting roi write")
    roi_array = [None] + [roi for _, roi in rm.iter_all()]
    TRF.write_parallel(zip_out_path, roi_list=roi_array, num_threads=num_threads)
    StopWatch.stop("roi write")

    StopWatch.start("starting roi read & add 2")
    rois = TRF.read_parallel(zip_out_path, label_image, num_threads=num_threads)
    StopWatch.stop("roi read")

    rm=TinyRoiManager()
    for roi in rois:
        if roi:
            rm.add_unchecked(roi)

    StopWatch.start("Feret")
    rm.force_feret()
    StopWatch.stop("Feret")


    last_3 = rois[-3:]
    for roi in last_3:
        if roi:
            (top, left, bottom, right)= roi.bounds
            print(f"{roi.name}: {roi.n} points, bounds=({left},{top}) to ({right},{bottom})")

    print("**** second round")
    base_name=test_path+"C_stitch"
    zip_path = base_name+"_rois.zip"
    zip_out_path = base_name+"_RoiSet.zip"
    label_path = base_name+"_cp_masks.png"
    label_image: np.ndarray= cv2.imread(label_path, cv2.IMREAD_UNCHANGED)
    num_threads = 12

    rm = TinyRoiManager()
    StopWatch.start("starting roi read")
    rois = TRF.read_parallel(zip_path, label_image, num_threads=num_threads)
    print(f"num of rois: {len(rois)}")
    for roi in rois:
        if roi:
            rm.add_unchecked(roi)
    StopWatch.stop("roi read & add 1")

    StopWatch.start("Feret")
    rm.force_feret()
    StopWatch.stop("Feret")


    StopWatch.start("starting roi write")
    roi_array = [None] + [roi for _, roi in rm.iter_all()]
    TRF.write_parallel(zip_out_path, roi_list=roi_array, num_threads=num_threads)
    StopWatch.stop("roi write")

    StopWatch.start("starting roi read 2")
    rois = TRF.read_parallel(zip_out_path, label_image, num_threads=num_threads)
    StopWatch.stop("roi read")

    rm = TinyRoiManager()
    for roi in rois:
        if roi:
            rm.add_unchecked(roi)


    StopWatch.start("Feret")
    rm.force_feret()
    StopWatch.stop("Feret")


    last_3 = rois[-3:]
    for roi in last_3:
        if roi:
            (top, left, bottom, right)= roi.bounds
            print(f"{roi.name}: {roi.n} points, bounds=({left},{top}) to ({right},{bottom})")
    # ns =[]
    # for roi in rois:
    #     if roi:
    #         print(roi.n,end=",")
    #         ns.append(roi.n)
    # print("")
    # print(np.mean(ns))

if __name__ == "__main__":
    test_roimanager()