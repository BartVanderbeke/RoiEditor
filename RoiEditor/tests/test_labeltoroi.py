import cv2
import label_to_roi
from roi import Roi
from tiny_roi_manager import TinyRoiManager

from RoiEditor.tests._helpers import compare_text, data_path, fail


EXPECTED = """L158     |  33 punten | state: ROI_STATE_DELETED | tags: ['DELETED.edge.image']
L159     |  38 punten | state: ROI_STATE_DELETED | tags: ['DELETED.edge.image']
L160     |  55 punten | state: ROI_STATE_DELETED | tags: ['DELETED.edge.image']
L158     |  33 punten | state: ROI_STATE_DELETED | tags: ['DELETED.edge.image']
L159     |  38 punten | state: ROI_STATE_DELETED | tags: ['DELETED.edge.image']
L160     |  55 punten | state: ROI_STATE_DELETED | tags: ['DELETED.edge.image']
L326     |  49 punten | state: ROI_STATE_ACTIVE | tags: []
L327     |  82 punten | state: ROI_STATE_ACTIVE | tags: []
L328     |  51 punten | state: ROI_STATE_ACTIVE | tags: []"""


def test_labeltoroi():
    try:
        label_to_roi.get_edge_labels = label_to_roi.get_edge_labels.py_func
        manager = TinyRoiManager()
        lines = []
        for image_name in ("A_stitch_cp_masks.png", "A_stitch_cp_masks.png", "C_stitch_cp_masks.png"):
            label_image = cv2.imread(str(data_path(image_name)), cv2.IMREAD_UNCHANGED)
            label_to_roi.process_label_image(manager, label_image)
            for name, roi in list(manager.iter_all())[-3:]:
                lines.append(f"{name:8s} | {roi.n:3d} punten | state: {Roi.state_to_str(roi.state)} | tags: {sorted(roi.tags)}")
        compare_text("\n".join(lines), EXPECTED, "label_to_roi")
    except Exception as exc:
        fail(f"{type(exc).__name__}: {exc}")
