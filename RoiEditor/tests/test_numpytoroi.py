import numpy as np

from numpy_to_roi import process_label_image
from tiny_roi_manager import TinyRoiManager

from RoiEditor.tests._helpers import compare_text, data_path, fail


EXPECTED = """num_of_rois read: 159
L158: 25 points, bounds=(887, 14, 915, 50)
L159: 21 points, bounds=(889, 194, 915, 251)
L160: 35 points, bounds=(897, 114, 915, 171)"""


def test_numpytoroi():
    try:
        manager = TinyRoiManager()
        data = np.load(data_path("A_stitch_seg.npy"), allow_pickle=True).item()
        process_label_image(manager, data, remove_edges=True, remove_small=True, size_threshold=100)
        rois = np.array(list(manager.iter_all()), dtype=object)
        lines = [f"num_of_rois read: {len(rois)}"]
        for _, roi in rois[-3:]:
            lines.append(f"{roi.name}: {roi.n} points, bounds={roi.bounds}")
        compare_text("\n".join(lines), EXPECTED, "numpy_to_roi")
    except Exception as exc:
        fail(f"{type(exc).__name__}: {exc}")
