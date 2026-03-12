from pathlib import Path

from tiny_roi_file import TinyRoiFile

from RoiEditor.tests._helpers import compare_text, fail, load_label, load_manager, wait_for_zip


EXPECTED = """A_stitch
L158: 31 points, bounds=(14,885) to (52,916)
L159: 32 points, bounds=(192,888) to (256,916)
L160: 52 points, bounds=(113,897) to (185,916)
C_stitch
L326: 104 points, bounds=(179,997) to (221,1027)
L327: 130 points, bounds=(219,1004) to (277,1040)
L328: 104 points, bounds=(274,1005) to (317,1033)"""


def test_roimanager(tmp_path):
    try:
        lines = []
        for stem in ("A_stitch", "C_stitch"):
            manager, label = load_manager(stem)
            manager.force_feret()
            out_path = Path(tmp_path) / f"{stem}_RoiSet.zip"
            roi_array = [None] + [roi for _, roi in manager.iter_all()]
            TinyRoiFile.write_parallel(str(out_path), roi_array, num_threads=4)
            wait_for_zip(out_path)
            rois = TinyRoiFile.read(str(out_path), label)
            lines.append(stem)
            for roi in rois[-3:]:
                if roi:
                    lines.append(f"{roi.name}: {roi.n} points, bounds=({roi.bounds[1]},{roi.bounds[0]}) to ({roi.bounds[3]},{roi.bounds[2]})")
        compare_text("\n".join(lines), EXPECTED, "ROI manager roundtrip")
    except Exception as exc:
        fail(f"{type(exc).__name__}: {exc}")
