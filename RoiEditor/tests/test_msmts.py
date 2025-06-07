import os
import sys
import numpy as np
import cv2

from PyQt6.QtWidgets import QApplication
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from RoiEditor.Lib.Context import gvars
from RoiEditor.Lib.TinyRoiFile import TinyRoiFile
from RoiEditor.Lib.StopWatch import StopWatch
from RoiEditor.Lib.TinyRoiManager import TinyRoiManager
from RoiEditor.Lib.RoiMeasurements import RoiMeasurements
from RoiEditor.Lib.TinyLog import log
from RoiEditor.Lib.Roi import Roi

def test_msmts():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    base_path = os.path.dirname(__file__)
    test_path = os.path.join(base_path, "TestData")+'/'



    #base_name = ".\TestData\A_stitch_RoiSet"
    base_name = test_path+"C_stitch"
    zip_path = base_name + "_rois.zip"
    csv_path = base_name + ".csv"
    label_path = base_name+"_cp_masks.png"
    label_image: np.ndarray= cv2.imread(label_path, cv2.IMREAD_UNCHANGED)
    num_threads = 12

    rm = TinyRoiManager()
    StopWatch.start("starting roi read")
    rois = TinyRoiFile.read_parallel(zip_path, label_image, num_threads=num_threads)
    StopWatch.stop("roi read")
    for roi in rois:
        if roi:
            rm.add_unchecked(roi)

    StopWatch.start("Feret")
    rm.force_feret()
    StopWatch.stop("Feret")
    
    StopWatch.start("msmts all")
    msmts = RoiMeasurements(rm)
    StopWatch.stop("msmts all")

    subset_name="ALL"
    csv_path = base_name + "_"+subset_name+".csv"
    msmts.save_measurements_to_csv(full_name=csv_path, subset_name=subset_name)

    stats_all = msmts.stats["ALL"]
    area_hist = stats_all["Area"]
    plt.figure()
    plt.hist(msmts.data["ALL"]["Area"], bins=area_hist["bin_edges"])
    plt.title("Histogram of Area - ALL")
    plt.xlabel("Area")
    plt.ylabel("Count")
    plt.grid(True)
    plt.show(block=False)

    stats_all_area = msmts.stats["ALL"]["Area"]
    print("\nALL - Area stats")
    print(" ".join([k.rjust(8) for k in stats_all_area.keys() if k not in ["hist", "bin_edges","outliers"]]))
    print(" ".join([f"{v:.3f}".rjust(8) for k, v in stats_all_area.items() if k not in ["hist", "bin_edges","outliers"] and k !='unit']))


    subset_name="DELETED"
    StopWatch.start(f"msmts: {subset_name}")
    deleted_filter = lambda roi: (roi.state==Roi.ROI_STATE_DELETED) if roi else False
    msmts.define_subset(subset_name=subset_name, filter=deleted_filter)
    msmts.compute_stats_subset("DELETED")
    StopWatch.stop(f"msmts: {subset_name}")
    csv_path = base_name + "_"+subset_name+".csv"
    msmts.save_measurements_to_csv(full_name=csv_path, subset_name=subset_name)


    stats_del = msmts.stats["DELETED"]["Area"]
    print("\nDELETED - Area stats")
    print(" ".join([k.rjust(8) for k in stats_del.keys() if k not in ["hist", "bin_edges","outliers"]]))
    print(" ".join([f"{v:.3f}".rjust(8) for k, v in stats_del.items() if k not in ["hist", "bin_edges","outliers"] and k !='unit']))

    plt.figure()
    plt.hist(msmts.data["DELETED"]["Area"], bins=stats_del["bin_edges"])
    plt.title("Histogram of Area - DELETED")
    plt.xlabel("Area")
    plt.ylabel("Count")
    plt.grid(True)
    plt.show(block=False)



    subset_name="ACTIVE"
    StopWatch.start(f"msmts: {subset_name}")
    active_filter = lambda roi: (roi.state==Roi.ROI_STATE_ACTIVE) if roi else False
    msmts.define_subset(subset_name=subset_name, filter=active_filter)
    msmts.compute_stats_subset(subset_name)
    StopWatch.stop(f"msmts: {subset_name}")
    csv_path = base_name + "_"+subset_name+".csv"
    msmts.save_measurements_to_csv(full_name=csv_path, subset_name=subset_name)

    stats_del = msmts.stats[subset_name]["Area"]
    print(f"\n{subset_name} - Area stats")
    print(" ".join([k.rjust(8) for k in stats_del.keys() if k not in ["hist", "bin_edges","outliers"]]))
    print(" ".join([f"{v:.3f}".rjust(8) for k, v in stats_del.items() if k not in ["hist", "bin_edges","outliers"] and k !='unit']))

    plt.figure()
    plt.hist(msmts.data[subset_name]["Area"], bins=stats_del["bin_edges"])
    plt.title(f"Histogram of Area - {subset_name}")
    plt.xlabel("Area")
    plt.ylabel("Count")
    plt.grid(True)
    plt.show(block=False)


    subset_name="BIG"
    StopWatch.start(f"msmts: {subset_name}")
    big_filter = lambda roi: (roi.area > 2000) if roi else False
    msmts.define_subset(subset_name=subset_name, filter=big_filter)
    msmts.compute_stats_subset(subset_name)
    StopWatch.stop(f"msmts: {subset_name}")
    csv_path = base_name + "_"+subset_name+".csv"
    msmts.save_measurements_to_csv(full_name=csv_path, subset_name=subset_name)

    stats_del = msmts.stats[subset_name]["Area"]
    print("\nBIG - Area stats")
    print(" ".join([k.rjust(8) for k in stats_del.keys() if k not in ["hist", "bin_edges","outliers"]]))
    print(" ".join([f"{v:.3f}".rjust(8) for k, v in stats_del.items() if k not in ["hist", "bin_edges","outliers"] and k !='unit']))

    plt.figure()
    plt.hist(msmts.data[subset_name]["Area"], bins=stats_del["bin_edges"])
    plt.title(f"Histogram of Area - {subset_name}")
    plt.xlabel("Area")
    plt.ylabel("Count")
    plt.grid(True)
    plt.show(block=False)


    subset_name="SELECTED"
    StopWatch.start(f"msmts: {subset_name}")
    filter = lambda roi: (roi.state == Roi.ROI_STATE_SELECTED) if roi else False
    msmts.define_subset(subset_name=subset_name, filter=filter)
    msmts.compute_stats_subset(subset_name)
    StopWatch.stop(f"msmts: {subset_name}")
    csv_path = base_name + "_"+subset_name+".csv"
    msmts.save_measurements_to_csv(full_name=csv_path, subset_name=subset_name)

    stats_del = msmts.stats[subset_name]["Feret"]
    print("\nSELECTED - Area stats")
    print(" ".join([k.rjust(8) for k in stats_del.keys() if k not in ["hist", "bin_edges","outliers"]]))
    print(" ".join([f"{v:.3f}".rjust(8) for k, v in stats_del.items() if k not in ["hist", "bin_edges","outliers"] and k !='unit']))

    plt.figure()
    plt.hist(msmts.data[subset_name]["Area"], bins=stats_del["bin_edges"])
    plt.title(f"Histogram of Area - {subset_name}")
    plt.xlabel("Area")
    plt.ylabel("Count")
    plt.grid(True)
    plt.show(block=True)


if __name__ == "__main__":
        test_msmts()