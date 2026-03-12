from PyQt6.QtWidgets import QGraphicsTextItem

import context as Context
from stylesheet import overall
from workbench import Workbench

from RoiEditor.tests._helpers import DummyParent, copy_workbench_files, fail, pixel_scale, run_qt_loop, set_roi_states


def test_workbench(qapp, tmp_path):
    try:
        Context.gvars["selected_unit_and_scale"] = pixel_scale()
        _ = QGraphicsTextItem("init")
        parent = DummyParent()
        parent.setStyleSheet(overall)
        bench = Workbench(copy_workbench_files(tmp_path, "A_stitch"), parent=parent)
        window = bench.build()
        if window is None:
            fail("Workbench failed to build")

        def update(step: int) -> None:
            set_roi_states(bench.rm["cell"], step)
            bench.on_any_change()

        run_qt_loop(qapp, update=update, repeats=5, cleanup=bench.clean_up)
    except Exception as exc:
        fail(f"{type(exc).__name__}: {exc}")
