import cv2

from feret import get_values, get_values2
from tiny_roi_file import TinyRoiFile

from RoiEditor.tests._helpers import compare_text, data_path, zip_name_for


EXPECTED = """A_stitch
#rois: 161
L001: 24.749, 33.690, 123.690, 21.000, 2.000, 2.000, 1.179
L160: 72.408, 11.929, 101.929, 16.688, 113.000, 897.000, 4.339
C_stitch
#rois: 329
L001: 34.000, 0.000, 90.000, 18.000, 17.000, 9.000, 1.889
L328: 42.000, 0.000, 90.000, 27.000, 295.000, 1018.500, 1.556"""


def _format_values(values) -> str:
    return ", ".join(f"{float(value):.3f}" for value in values)


def test_feret():
    lines = []
    for stem, measure in (("A_stitch", get_values), ("C_stitch", get_values2)):
        label = cv2.imread(str(data_path(f"{stem}_cp_masks.png")), cv2.IMREAD_UNCHANGED)
        rois = TinyRoiFile.read(str(data_path(zip_name_for(stem))), label)
        results = []
        for roi in rois:
            if roi:
                results.append((roi.name, measure(roi._xpoints, roi._ypoints)))
        lines.extend(
            [
                stem,
                f"#rois: {len(rois)}",
                f"{results[0][0]}: {_format_values(results[0][1])}",
                f"{results[-1][0]}: {_format_values(results[-1][1])}",
            ]
        )
    compare_text("\n".join(lines), EXPECTED, "Feret summary")
