from PyQt6.QtWidgets import QGraphicsTextItem

import cv2
import context as Context
from roi_select import select_outer_rois_vdb, select_outer_rois_vdb3, select_outer_rois_vdb4, select_outer_rois_vdb5
from stylesheet import overall
from workbench import Workbench

from RoiEditor.tests._helpers import DummyParent, copy_workbench_files, fail, pixel_scale, run_qt_loop


def test_roiselect(qapp, tmp_path):
    try:
        Context.gvars["show_names"] = True
        Context.gvars["show_deleted"] = True
        Context.gvars["selected_unit_and_scale"] = pixel_scale()
        _ = QGraphicsTextItem("init")
        parent = DummyParent()
        parent.setStyleSheet(overall)
        files = copy_workbench_files(tmp_path, "A_stitch")
        bench = Workbench(files, parent=parent)
        window = bench.build()
        if window is None:
            fail("Workbench failed to build in roiselect test")
        label_image = cv2.imread(files["cell_label"], cv2.IMREAD_UNCHANGED)
        selectors = [
            lambda: select_outer_rois_vdb(bench.rm["cell"], step=1),
            lambda: select_outer_rois_vdb3(bench.rm["cell"], step=1),
            lambda: select_outer_rois_vdb4(bench.rm["cell"], step=1),
            lambda: select_outer_rois_vdb5(bench.rm["cell"], label_image),
            lambda: select_outer_rois_vdb5(bench.rm["cell"], label_image),
        ]

        def update(step: int) -> None:
            selectors[step]()
            window.draw_image()

        run_qt_loop(qapp, update=update, repeats=5, cleanup=bench.clean_up)
    except Exception as exc:
        fail(f"{type(exc).__name__}: {exc}")
