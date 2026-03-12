import cv2
from label_to_roi_diff import process_label_image
from roi import Roi
from tiny_roi_manager import TinyRoiManager

from RoiEditor.tests._helpers import compare_text, data_path, fail


EXPECTED = """L158     |  31 punten | state: ROI_STATE_DELETED | tags: ['DELETED.edge.image']
L159     |  32 punten | state: ROI_STATE_DELETED | tags: ['DELETED.edge.image']
L160     |  52 punten | state: ROI_STATE_DELETED | tags: ['DELETED.edge.image']
L158     |  31 punten | state: ROI_STATE_DELETED | tags: ['DELETED.edge.image']
L159     |  32 punten | state: ROI_STATE_DELETED | tags: ['DELETED.edge.image']
L160     |  52 punten | state: ROI_STATE_DELETED | tags: ['DELETED.edge.image']
L326     |  45 punten | state: ROI_STATE_ACTIVE | tags: []
L327     |  80 punten | state: ROI_STATE_ACTIVE | tags: []
L328     |  48 punten | state: ROI_STATE_ACTIVE | tags: []"""


def test_labeltoroidiff():
    try:
        manager = TinyRoiManager()
        lines = []
        for image_name in ("A_stitch_cp_masks.png", "A_stitch_cp_masks.png", "C_stitch_cp_masks.png"):
            label_image = cv2.imread(str(data_path(image_name)), cv2.IMREAD_UNCHANGED)
            process_label_image(manager, label_image)
            for name, roi in list(manager.iter_all())[-3:]:
                lines.append(f"{name:8s} | {roi.n:3d} punten | state: {Roi.state_to_str(roi.state)} | tags: {sorted(roi.tags)}")
        compare_text("\n".join(lines), EXPECTED, "label_to_roi_diff")
    except Exception as exc:
        fail(f"{type(exc).__name__}: {exc}")
