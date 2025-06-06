import os
import sys


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
        zip_path = test_path+base_name+".zip"
        StopWatch.start("")
        rois = TinyRoiFile.read_parallel(zip_path, num_threads=num_threads)
        StopWatch.stop(f"num of rois read {len(rois)}")
        StopWatch.start("")
        zip_path=base_name+"_OUT.zip"
        TinyRoiFile.write_parallel(zip_path, roi_list=rois, num_threads=num_threads_write)
        StopWatch.stop(f"num of rois written {len(rois)}")
        StopWatch.start("")
        rois = TinyRoiFile.read_parallel(zip_path, num_threads=num_threads)
        StopWatch.stop(f"num of rois read {len(rois)}")
        print("********* End of Loop")
        print("")

    StopWatch.start("")
    StopWatch.stop("dummy")
    StopWatch.start("")
    StopWatch.stop("dummy")


    base_name = "A_Stitch_RoiSet"
    loop(base_name)
    base_name = "B_Stitch_RoiSet"
    loop(base_name)
    base_name = "C_stitch_RoiSet"
    loop(base_name)

    last_3 = rois[-3:]
    for roi in last_3:
        if roi:
            print(f"{roi.name}: {roi.n} points, bounds={roi.bounds}, state={Roi.state_to_str(roi.state)}")

if __name__ == "__main__":
    test_tinyroifile()