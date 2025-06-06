import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from RoiEditor.Lib.Feret import feret_msmts,get_values,get_values2
from RoiEditor.Lib.StopWatch import StopWatch
from RoiEditor.Lib.TinyRoiFile import TinyRoiFile

def test_feret():
    base_path = os.path.dirname(__file__)
    test_path = os.path.join(base_path, "TestData")+'/'


    StopWatch.start("warm up")
    StopWatch.stop("warm up")
    title_line = ["Name"] + feret_msmts
    num_threads = 12


    base_name = test_path+"A_Stitch_RoiSet"
    zip_path = base_name + ".zip"
    StopWatch.start("starting roi read")
    rois = TinyRoiFile.read_parallel(zip_path, num_threads=num_threads)
    StopWatch.stop("roi read")
    results =[]
    print(f"#rois: {len(rois)}")
    StopWatch.start("Feret")
    for roi in rois:
        if roi:
            xpoints = roi.xpoints
            ypoints = roi.ypoints
            set1 = get_values(xpoints, ypoints)
            results.append([roi.name] + list(set1))
            #print(roi.name + ": ", set1)
    StopWatch.stop("Feret")
    import csv
    csv_path = base_name + "_feret.csv"
    with open(csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(title_line)
        for row in results:
            formatted_row = [row[0]] + [f"{v:.6f}".replace('.', ',') for v in row[1:]]
            writer.writerow(formatted_row)

    print(f"CSV saved to {csv_path}")

    base_name = test_path+"A_Stitch_RoiSet"
    zip_path = base_name + ".zip"
    StopWatch.start("starting roi read")
    rois = TinyRoiFile.read_parallel(zip_path, num_threads=num_threads)
    StopWatch.stop("roi read")
    results =[]
    print(f"#rois: {len(rois)}")
    StopWatch.start("Feret")
    for roi in rois:
        if roi:
            xpoints = roi.xpoints
            ypoints = roi.ypoints
            set1 = get_values2(xpoints, ypoints)
            results.append([roi.name] + list(set1))
            #print(roi.name + ": ", set1)
    StopWatch.stop("Feret")
    import csv
    csv_path = base_name + "_feret2.csv"
    with open(csv_path, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Name", "Feret", "FeretAngle", "MinFeret", "FeretX", "FeretY"])
        for row in results:
            formatted_row = [row[0]] + [f"{v:.6f}".replace('.', ',') for v in row[1:]]
            writer.writerow(formatted_row)

    print(f"CSV saved to {csv_path}")

if __name__ == "__main__":
    test_feret()    