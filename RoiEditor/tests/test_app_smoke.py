from PyQt6.QtWidgets import QApplication

import context as Context
from roi_editor_control_panel import RoiEditorControlPanel
from stylesheet import overall

from RoiEditor.tests._helpers import copy_workbench_files, fail, run_qt_loop


def test_app_smoke_start_next_and_close(qapp, tmp_path):
    try:
        files = copy_workbench_files(tmp_path, "A_stitch")
        panel = RoiEditorControlPanel(parent=None)
        panel.setStyleSheet(overall)
        panel.connect_all_handlers()
        panel.show()

        panel.try_accept_name("org", files["org"])
        panel.try_accept_name("cell_label", files["cell_label"])
        panel.try_accept_name("cell_zip", files["cell_zip"])
        panel.rb_pixel_is_unit.setChecked(True)

        def update(step: int) -> None:
            if step == 0:
                panel.on_click_browse_next()
                if panel.workbench is None:
                    fail("Control panel did not create a workbench after Next")
                if panel.workbench.roi_window is None:
                    fail("Workbench did not create an ROI window")
                panel.workbench.on_backup_rois = lambda: False
            elif step == 1:
                panel.on_finish()
            elif step == 2:
                visible = [
                    (type(w).__name__, w.windowTitle())
                    for w in QApplication.topLevelWidgets()
                    if w.isVisible()
                ]
                if visible:
                    fail(f"Visible windows remain after closing: {visible}")

        def cleanup() -> None:
            for widget in list(QApplication.topLevelWidgets()):
                widget.close()

        Context.gvars["selected_unit_and_scale"] = {
            "length": {"scaler": 1.0, "unit": "px"},
            "area": {"scaler": 1.0, "unit": "px"},
            "source": "pytest",
        }
        run_qt_loop(qapp, update=update, repeats=3, interval_ms=250, cleanup=cleanup)
    except Exception as exc:
        fail(f"{type(exc).__name__}: {exc}")
