import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from RoiEditor.Lib.TinyRoiManager import TinyRoiManager
from RoiEditor.Lib.NumpyToRoi import process_label_image
from RoiEditor.Lib.StopWatch  import StopWatch

def  test_numpytoroi():
    base_path = os.path.dirname(__file__)
    test_path = os.path.join(base_path, "TestData")+'/'
    npy_path = test_path+'A_stitch_seg.npy'

    StopWatch.start("dummy")
    StopWatch.stop("dummy")
    StopWatch.start("dummy")
    StopWatch.stop("dummy")

    rm=TinyRoiManager()

    data = np.load(npy_path, allow_pickle=True).item()
    StopWatch.start("starting numpy read")
    process_label_image(rm, data, remove_edges=True, remove_small=True, size_threshold= 100)
    StopWatch.stop("numpy read")
    rois = np.array(list(rm.iter_all()))
    print(f"num_of_rois read: {len(rois)}")
    last_3 = rois[-3:]
    for _, roi in last_3:
        if roi:
            print(f"{roi.name}: {roi.n} points, bounds={roi.bounds}")


if __name__ == "__main__":
    test_numpytoroi()