import tifffile

import tifffile
from exif import dict_to_pretty_json, read_ome_metadata, retrieve_image_info, update_ome_metadata_from_json

from RoiEditor.tests._helpers import compare_text, data_path, fail


EXPECTED = """shape (710, 583, 3)
samplesperpixel 3
photometric 2
bitspersample 8
is_contiguous True
imagewidth x imagelength 583 x 710
software tifffile.py
Aantal IFD's (pages): 1
Page 0: shape=(710, 583, 3), samplesperpixel=3
pixel size: 0.645 x 0.645 micron, magnification: 10.0x"""


def test_exif(tmp_path):
    source = data_path("exif_sample.tiff")
    target = tmp_path / source.name
    target.write_bytes(source.read_bytes())

    with tifffile.TiffFile(target) as tif:
        page = tif.pages[0]
        imagewidth = page.imagewidth
        imagelength = page.imagelength
        summary = "\n".join(
            [
                f"shape {page.shape}",
                f"samplesperpixel {page.samplesperpixel}",
                f"photometric {page.photometric}",
                f"bitspersample {page.bitspersample}",
                f"is_contiguous {page.is_contiguous}",
                f"imagewidth x imagelength {imagewidth} x {imagelength}",
                f"software {page.software}",
                f"Aantal IFD's (pages): {len(tif.pages)}",
                f"Page 0: shape={page.shape}, samplesperpixel={page.samplesperpixel}",
            ]
        )

    metadata = read_ome_metadata(str(target))
    info = retrieve_image_info(metadata)
    compare_text(f"{summary}\n{info['as_string']}", EXPECTED, "EXIF summary")

    json_data = {
        "Experimenter": {"ID": "Experimenter:0", "Institution": "Katholieke Universiteit Leuven", "LastName": "Koppo"},
        "Instrument": {
            "ID": "Instrument:1",
            "Detector": {"ID": "Detector:0"},
            "Objective": {
                "ID": "Objective:1",
                "Correction": "PlanFluor",
                "LensNA": 0.3,
                "Model": "Plan Fluor 10x DIC L",
                "NominalMagnification": 10,
                "WorkingDistance": 16000.0,
            },
        },
        "Image": {
            "ID": "Image:0",
            "Name": target.name,
            "InstrumentRef": {"ID": "Instrument:1"},
            "Pixels": {
                "ID": "Pixels:0",
                "SizeX": imagewidth,
                "SizeY": imagelength,
                "SizeZ": 1,
                "SizeC": 3,
                "SizeT": 1,
                "Type": "uint8",
                "DimensionOrder": "XYCZT",
                "PhysicalSizeX": 0.645,
                "PhysicalSizeY": 0.645,
                "Channels": [{"ID": "Channel:0", "Name": "Red"}, {"ID": "Channel:1", "Name": "Green"}, {"ID": "Channel:2", "Name": "Blue"}],
                "Plane": {"TheC": 0, "TheT": 0, "TheZ": 0},
            },
        },
    }

    update_ome_metadata_from_json(json_data, str(target), str(target))
    updated = dict_to_pretty_json(read_ome_metadata(str(target)))
    if '"Institution": "Katholieke Universiteit Leuven"' not in updated:
        fail("Updated OME metadata did not contain the expected institution")
