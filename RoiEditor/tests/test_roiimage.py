from PyQt6.QtGui import QImage

from roi_image import RoiImageWindow
from roi_measurements import RoiMeasurements
from stylesheet import overall

from RoiEditor.tests._helpers import DummyParent, data_path, fail, load_manager, pixel_scale, run_qt_loop


def test_roiimage(qapp):
    try:
        manager, _ = load_manager("A_stitch")
        image = QImage(str(data_path("A_stitch.tiff")))
        msmts = RoiMeasurements(manager, unit_and_scale=pixel_scale())
        parent = DummyParent()
        parent.setStyleSheet(overall)
        window = RoiImageWindow(
            qimage=image,
            rm=manager,
            nd=None,
            msmts=msmts,
            on_any_change=lambda reason, flag=None: None,
            on_add_nucleus_here=lambda roi, here: None,
            parent=parent,
        )
        window.draw_image()
        window.show()
        measurements = ["Area", "Feret", "FeretAngle", "AngleShifted", "MinFeret"]

        def update(step: int) -> None:
            window.on_select_measurement(measurements[step % len(measurements)])

        run_qt_loop(qapp, update=update, repeats=5, cleanup=window.close)
    except Exception as exc:
        fail(f"{type(exc).__name__}: {exc}")
