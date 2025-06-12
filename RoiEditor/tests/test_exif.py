import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from RoiEditor.Lib.Exif import read_ome_metadata,dict_to_pretty_json,retrieve_image_info, update_ome_metadata_from_json
import tifffile

def test_exif():
    base_path = os.path.dirname(__file__)
    test_path = os.path.join(base_path, "TestData")+ "/"
    filename=  "exif_sample.tiff"
    tiff_path = os.path.join(test_path,filename )

    with tifffile.TiffFile(tiff_path) as tif:
        shape = tif.pages[0].shape
        samplesperpixel= tif.pages[0].samplesperpixel
        photometric=tif.pages[0].photometric
        is_contiguous= tif.pages[0].is_contiguous
        imagewidth=tif.pages[0].imagewidth
        imagelength=tif.pages[0].imagelength
        software= tif.pages[0].software
        description= tif.pages[0].description
        print(f"shape {shape}")
        print(f"samplesperpixel {samplesperpixel}")
        print(f"photometric {photometric}")
        print(f"bitspersample {tif.pages[0].bitspersample}")
        print(f"is_contiguous {is_contiguous}")
        print(f"imagewidth x imagelength {imagewidth} x {imagelength}")
        print(f"software {software}")
        npages = len(tif.pages)
        print(f"Aantal IFD's (pages): {npages}")
        pages={}
        for i, page in enumerate(tif.pages):
            pages[i]={"shape": page.shape, "samplesperpixel": page.samplesperpixel } 
            print(f"Page {i}: shape={page.shape}, samplesperpixel={page.samplesperpixel}")

        data = tif.pages[0].asarray()[..., :3]  # strip alpha
        tifffile.imwrite(tiff_path, data, description=description,photometric='rgb')


    meta_data = read_ome_metadata(tiff_path)
    json_text= dict_to_pretty_json(meta_data)
    print (json_text)

    info_dict = retrieve_image_info(meta_data)
    #print(info_dict["as_string"])

    json_data = {
                "Experimenter": {
                    "ID": "Experimenter:0",
                    "Institution": "Katholieke Universiteit Leuven",
                    "LastName": "Koppo"
                },
                "Instrument": {
                    "ID": "Instrument:1",
                    "Detector": {
                    "ID": "Detector:0"
                    },
                    "Objective": {
                    "ID": "Objective:1",
                    "Correction": "PlanFluor",
                    "LensNA": 0.3,
                    "Model": "Plan Fluor 10x DIC L",
                    "NominalMagnification": 10,
                    "WorkingDistance": 16000.0
                    }
                },
                "Image": {
                    "ID": "Image:0",
                    "Name": filename,
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
                    "Channels": [
                        {"ID": "Channel:0", "Name": "Red"},
                        {"ID": "Channel:1", "Name": "Green"},
                        {"ID": "Channel:2", "Name": "Blue"}
                    ],
                    "Plane": {
                        "TheC": 0,
                        "TheT": 0,
                        "TheZ": 0
                    }
                    }
                }
                }

    #tiff_path = test_path + "exif_sample.tiff"
    output_path = tiff_path #test_path + "exif_sample_out.tiff"
    update_ome_metadata_from_json(json_data, tiff_path, output_path)


    meta_data = read_ome_metadata(tiff_path)
    json_text= dict_to_pretty_json(meta_data)
    print (json_text)

if __name__ == "__main__":
    test_exif()