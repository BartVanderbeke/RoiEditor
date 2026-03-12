import shutil
import time
import zipfile
from pathlib import Path

import cv2
import numpy as np
import pytest
from PyQt6.QtCore import QThreadPool, QTimer
from PyQt6.QtWidgets import QWidget

from roi import Roi
from tiny_roi_file import TinyRoiFile
from tiny_roi_manager import TinyRoiManager


TESTS_DIR = Path(__file__).resolve().parent
DATA_DIR = TESTS_DIR / "TestData"


def fail(message: str) -> None:
    pytest.fail(message, pytrace=False)


def compare_text(actual: str, expected: str, label: str) -> None:
    if actual.strip() != expected.strip():
        fail(f"{label} mismatch\nEXPECTED:\n{expected}\n\nACTUAL:\n{actual}")


def data_path(name: str) -> Path:
    return DATA_DIR / name


def zip_name_for(stem: str) -> str:
    return f"{stem}_roiset.zip" if stem == "A_stitch" else f"{stem}_rois.zip"


def load_label(stem: str) -> np.ndarray:
    label = cv2.imread(str(data_path(f"{stem}_cp_masks.png")), cv2.IMREAD_UNCHANGED)
    if label is None:
        fail(f"Failed to load label image for {stem}")
    return label


def load_manager(stem: str) -> tuple[TinyRoiManager, np.ndarray]:
    label = load_label(stem)
    rois = TinyRoiFile.read(str(data_path(zip_name_for(stem))), label)
    manager = TinyRoiManager()
    for roi in rois:
        if roi:
            manager.add_unchecked(roi)
    return manager, label


def wait_for_zip(path: Path, timeout_s: float = 10.0) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if path.exists():
            try:
                with zipfile.ZipFile(path, "r") as handle:
                    handle.namelist()
                return
            except zipfile.BadZipFile:
                pass
        time.sleep(0.1)
    fail(f"Timed out waiting for zip file: {path}")


class DummyParent(QWidget):
    def eatAllEvents(self):
        pass

    def allowAllEvents(self):
        pass


def copy_workbench_files(tmp_path: Path, stem: str) -> dict[str, str | None]:
    org_name = f"{stem}.tiff"
    label_name = f"{stem}_cp_masks.png"
    zip_name = zip_name_for(stem)
    org_path = tmp_path / org_name
    label_path = tmp_path / label_name
    zip_path = tmp_path / zip_name
    shutil.copy2(data_path(org_name), org_path)
    shutil.copy2(data_path(label_name), label_path)
    shutil.copy2(data_path(zip_name), zip_path)
    return {
        "org": str(org_path),
        "cell_label": str(label_path),
        "cell_zip": str(zip_path),
        "nuke_label": None,
        "nuke_zip": None,
    }


def set_roi_states(manager: TinyRoiManager, offset: int = 0) -> None:
    states = [
        Roi.ROI_STATE_ACTIVE,
        Roi.ROI_STATE_SELECTED,
        Roi.ROI_STATE_DELETED,
        Roi.ROI_STATE_ACTIVE,
        Roi.ROI_STATE_SELECTED,
    ]
    for index, (_, roi) in enumerate(manager.iter_all()):
        roi.state = states[(index + offset) % len(states)]


def pixel_scale() -> dict[str, dict[str, str | float]]:
    return {
        "length": {"scaler": 1.0, "unit": "px"},
        "area": {"scaler": 1.0, "unit": "px"},
        "source": "pytest",
    }


def run_qt_loop(
    qapp,
    update=None,
    repeats: int = 0,
    interval_ms: int = 1000,
    cleanup=None,
    close_after_ms: int = 200,
) -> None:
    errors: list[Exception] = []
    timer = None

    def stop() -> None:
        try:
            if cleanup is not None:
                cleanup()
            QThreadPool.globalInstance().clear()
            QThreadPool.globalInstance().waitForDone(5000)
        except Exception as exc:
            errors.append(exc)
        qapp.quit()

    if update is None:
        QTimer.singleShot(close_after_ms, stop)
    else:
        timer = QTimer()
        counter = {"value": 0}

        def tick() -> None:
            try:
                update(counter["value"])
            except Exception as exc:
                errors.append(exc)
            counter["value"] += 1
            if counter["value"] >= repeats or errors:
                timer.stop()
                QTimer.singleShot(0, stop)

        timer.timeout.connect(tick)
        timer.start(interval_ms)

    qapp.exec()

    if errors:
        error = errors[0]
        fail(f"{type(error).__name__}: {error}")
