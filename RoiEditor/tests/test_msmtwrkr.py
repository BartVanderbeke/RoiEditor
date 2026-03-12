import numpy as np

from histogram_frame import HistogramFrame
from measurement_worker import compute_and_plot
from roi_measurements import RoiMeasurements

from RoiEditor.tests._helpers import fail, load_manager, run_qt_loop, set_roi_states


def test_msmtwrkr(qapp):
    try:
        manager, _ = load_manager("A_stitch")
        for _, roi in manager.iter_all():
            roi.color = np.array([0.0, 0.0, 0.0])

        histogram = HistogramFrame()
        msmts = RoiMeasurements(manager)
        compute_and_plot(manager, histogram, msmts)

        def update(step: int) -> None:
            set_roi_states(manager, step)
            compute_and_plot(manager, histogram, msmts)

        run_qt_loop(qapp, update=update, repeats=5, cleanup=histogram.close)
    except Exception as exc:
        fail(f"{type(exc).__name__}: {exc}")
