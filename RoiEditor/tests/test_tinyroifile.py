import os
import sys
import numpy as np
import cv2


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from RoiEditor.Lib.TinyRoiFile import TinyRoiFile
from RoiEditor.Lib.StopWatch  import StopWatch
from RoiEditor.Lib.Roi  import Roi

def  test_tinyroifile():


    num_threads = 1
    num_threads_write = 4

    def loop(base_name):
        global rois
        base_path = os.path.dirname(__file__)
        test_path = os.path.join(base_path, "TestData")+'/'
        zip_path = test_path+base_name+"_rois.zip"
        label_file = test_path+base_name+"_cp_masks.png"
        label_image: np.ndarray= cv2.imread(label_file, cv2.IMREAD_UNCHANGED)
        StopWatch.start("reading original")
        rois = TinyRoiFile.read_parallel(zip_path, label_image, num_threads=num_threads)
        StopWatch.stop(f"num of rois read {len(rois)}")
        StopWatch.start("writing back")
        zip_path=base_name+"_OUT.zip"
        TinyRoiFile.write_parallel(zip_path, roi_list=rois, num_threads=num_threads_write)
        StopWatch.stop(f"num of rois written {len(rois)}")
        StopWatch.start("reading copy")
        rois = TinyRoiFile.read_parallel(zip_path,label_image, num_threads=num_threads)
        StopWatch.stop(f"num of rois read {len(rois)}")
        print("********* End of Loop")
        print("")

    StopWatch.start("")
    StopWatch.stop("dummy")
    StopWatch.start("")
    StopWatch.stop("dummy")


    base_name = "A_Stitch"
    loop(base_name)
    base_name = "B_Stitch"
    loop(base_name)
    base_name = "C_stitch"
    loop(base_name)

    last_3 = rois[-3:]
    for roi in last_3:
        if roi:
            print(f"{roi.name}: {roi.n} points, bounds={roi.bounds}, state={Roi.state_to_str(roi.state)}")

if __name__ == "__main__":
    test_tinyroifile()