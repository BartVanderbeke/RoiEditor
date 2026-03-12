import numpy as np

from roi import Roi
from roi_measurements import RoiMeasurements

from RoiEditor.tests._helpers import compare_text, fail, load_manager


EXPECTED = """ALL 160 1441.531 1163.500 540.500
DELETED 53 1580.660 1282.500 629.500
ACTIVE 54 1399.639 1236.250 548.500
BIG 30 3131.233 2599.750 459.750
SELECTED 53 60.024 58.735 13.735"""


def test_msmts():
    try:
        manager, _ = load_manager("A_stitch")
        states = [Roi.ROI_STATE_ACTIVE, Roi.ROI_STATE_DELETED, Roi.ROI_STATE_SELECTED]
        for index, (_, roi) in enumerate(manager.iter_all()):
            roi.color = np.array([0.0, 0.0, 0.0])
            roi.state = states[index % len(states)]

        msmts = RoiMeasurements(manager)
        msmts.compute_stats_subset("ALL")
        msmts.define_subset("DELETED", lambda roi: roi.state == Roi.ROI_STATE_DELETED if roi else False)
        msmts.compute_stats_subset("DELETED")
        msmts.define_subset("ACTIVE", lambda roi: roi.state == Roi.ROI_STATE_ACTIVE if roi else False)
        msmts.compute_stats_subset("ACTIVE")
        msmts.define_subset("BIG", lambda roi: roi.area > 2000 if roi else False)
        msmts.compute_stats_subset("BIG")
        msmts.define_subset("SELECTED", lambda roi: roi.state == Roi.ROI_STATE_SELECTED if roi else False)
        msmts.compute_stats_subset("SELECTED")

        lines = []
        for subset_name, measurement_name in (
            ("ALL", "Area"),
            ("DELETED", "Area"),
            ("ACTIVE", "Area"),
            ("BIG", "Area"),
            ("SELECTED", "Feret"),
        ):
            stats = msmts.stats[subset_name][measurement_name]
            lines.append(f"{subset_name} {stats['N']} {stats['mean']:.3f} {stats['median']:.3f} {stats['mad']:.3f}")

        compare_text("\n".join(lines), EXPECTED, "Measurement summary")
    except Exception as exc:
        fail(f"{type(exc).__name__}: {exc}")
