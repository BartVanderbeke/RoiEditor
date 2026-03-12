import numpy as np
import numpy as np

from histogram_frame import HistogramFrame
from roi import Roi
from roi_measurements import RoiMeasurements

from RoiEditor.tests._helpers import fail, load_manager, run_qt_loop


def test_hist(qapp):
    try:
        manager, _ = load_manager("A_stitch")
        for _, roi in manager.iter_all():
            roi.color = np.array([0.0, 0.0, 0.0])
        msmts = RoiMeasurements(manager)
        msmts.compute_stats_subset("ALL")
        msmts.define_subset("DELETED", lambda roi: roi.state == Roi.ROI_STATE_DELETED if roi else False)
        msmts.compute_stats_subset("DELETED")
        msmts.define_subset("ACTIVE", lambda roi: roi.state == Roi.ROI_STATE_ACTIVE if roi else False)
        msmts.compute_stats_subset("ACTIVE")
        frame = HistogramFrame()
        frame.populate(msmts.measurement_names, "Area", msmts)
        frame.show()
        run_qt_loop(qapp, cleanup=frame.close)
    except Exception as exc:
        fail(f"{type(exc).__name__}: {exc}")
