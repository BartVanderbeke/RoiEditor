from roi import Roi
from tiny_roi_file import TinyRoiFile

from RoiEditor.tests._helpers import compare_text, data_path, fail, load_label, wait_for_zip


EXPECTED = """L326: 104 points, bounds=(997, 179, 1027, 221), state=ROI_STATE_ACTIVE
L327: 130 points, bounds=(1004, 219, 1040, 277), state=ROI_STATE_ACTIVE
L328: 104 points, bounds=(1005, 274, 1033, 317), state=ROI_STATE_ACTIVE"""


def test_tinyroifile(tmp_path):
    try:
        rois = None
        for stem in ("A_stitch", "C_stitch"):
            label = load_label(stem)
            zip_name = "A_stitch_roiset.zip" if stem == "A_stitch" else "C_stitch_rois.zip"
            rois = TinyRoiFile.read(str(data_path(zip_name)), label)
            out_path = tmp_path / f"{stem}_OUT.zip"
            TinyRoiFile.write_parallel(str(out_path), roi_list=rois, num_threads=4)
            wait_for_zip(out_path)
            rois = TinyRoiFile.read(str(out_path), label)
        lines = []
        for roi in rois[-3:]:
            if roi:
                lines.append(f"{roi.name}: {roi.n} points, bounds={roi.bounds}, state={Roi.state_to_str(roi.state)}")
        compare_text("\n".join(lines), EXPECTED, "TinyRoiFile roundtrip")
    except Exception as exc:
        fail(f"{type(exc).__name__}: {exc}")
