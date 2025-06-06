import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from RoiEditor.Lib.Exif import read_ome_metadata,dict_to_pretty_json,retrieve_image_info


def test_exif():
    base_path = os.path.dirname(__file__)
    test_path = os.path.join(base_path, "TestData")
    tiff_path = os.path.join(test_path, "C_stitch.tiff")

    meta_data = read_ome_metadata(tiff_path)
    json_text= dict_to_pretty_json(meta_data)
    print (json_text)

    info_dict = retrieve_image_info(meta_data)
    print(info_dict["as_string"])

if __name__ == "__main__":
    test_exif()