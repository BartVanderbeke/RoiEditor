"""RoiEditor

Author: Bart Vanderbeke
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
from xml.etree import ElementTree as ET
from tifffile import TiffFile
import json

def read_ome_metadata(tiff_path):
    """reads OME-XML and TIFF-header info into a dictionary."""
    with TiffFile(tiff_path) as tif:
        description = tif.pages[0].description
        #basic_tags = extract_basic_tags(tif.pages[0].tags)

        if description is None:
            return None
            #return {"BasicTags": basic_tags}

        if not description.strip().startswith('<?xml'):
            return {"ImageDescription": description.strip()} #, "BasicTags": basic_tags}

        metadata = parse_ome_xml(description)

        if "Image" in metadata and "Description" in metadata["Image"]:
            desc = metadata["Image"]["Description"]
            if isinstance(desc, dict) and "text" in desc:
                metadata["Image"]["Description"] = parse_description_text(desc["text"])
        return {"OME": metadata} # "BasicTags": basic_tags}

            

# def extract_basic_tags(tags):
    # """Extract standard (non OME) tags out of a TIFF"""
    # fields = {}
    # resolution_unit_mapping = {
    #     1: "none",
    #     2: "inch",
    #     3: "centimeter"
    # }
    # for name in ("XResolution", "YResolution", "ResolutionUnit"):
    #     if name in tags:
    #         value = tags[name].value
    #         if isinstance(value, tuple) and len(value) == 2:
    #             fields[name] = value[0] / value[1]
    #         else:
    #             fields[name] = value

    # if "ResolutionUnit" in fields:
    #     fields["ResolutionUnitString"] = resolution_unit_mapping.get(fields["ResolutionUnit"], "Unknown")
    # return fields

def parse_ome_xml(xml_string):
    root = ET.fromstring(xml_string)

    def parse_element(elem):
        data = {}
        data.update(elem.attrib)
        if elem.text and elem.text.strip():
            data['text'] = elem.text.strip()
        for child in elem:
            tag = child.tag.split('}')[-1]
            child_data = parse_element(child)
            if tag not in data:
                data[tag] = child_data
            else:
                if not isinstance(data[tag], list):
                    data[tag] = [data[tag]]
                data[tag].append(child_data)
        return data

    return parse_element(root)

def parse_description_text(description_text):
    result = {}
    current_section = None

    for line in description_text.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.endswith("Settings:"):
            section_name = line.replace("Settings:", "").strip() + " Settings"
            current_section = section_name
            result[current_section] = {}
        elif ":" in line:
            key, value = map(str.strip, line.split(":", 1))
            if current_section:
                result[current_section][key] = value
            else:
                result[key] = value
        else:
            if current_section:
                result[current_section][line] = None
            else:
                result[line] = None

    return result

def retrieve_image_info(meta_data):
    ome = meta_data.get("OME", {})
    image = ome.get("Image", {})
    instrument_ref = image.get("InstrumentRef", {}).get("ID")
    nominal_magnification = None

    for instrument in ome.get("Instrument", []):
        if instrument.get("ID") == instrument_ref:
            objective = instrument.get("Objective", {})
            nominal_magnification = objective.get("NominalMagnification",None)
            break

    # Haal Pixels-data op, als die er is
    pixels = image.get("Pixels", {})
    physical_size_x = pixels.get("PhysicalSizeX",None)
    physical_size_y = pixels.get("PhysicalSizeY",None)

    if physical_size_x and physical_size_y:
        info_str = f"pixel size: {float(physical_size_x)} x {float(physical_size_y)} micron,"
    else: 
        info_str="pixel size unknown,"
    if nominal_magnification:
        info_str=info_str + f" magnification: {float(nominal_magnification)}x"
    else:
        info_str=info_str+f" magnification unknown"
    
    return {"as_string" : info_str,
            "PhysicalSizeX" : float(physical_size_x) if physical_size_x else None,
            "PhysicalSizeY" : float(physical_size_y) if physical_size_y else None,
            "NominalMagnification" : float(nominal_magnification) if nominal_magnification else None
    }

def retrieve_tiff_image_info(tiff_path):
    all_data= read_ome_metadata(tiff_path)
    return retrieve_image_info(all_data)


def dict_to_pretty_json(data):
    """Converts a dictionary to a well-formatted JSON-string."""
    return json.dumps(data, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    tiff_path = "./TestData/C_stitch.tiff"
    meta_data = read_ome_metadata(tiff_path)
    json_text= dict_to_pretty_json(meta_data)
    print (json_text)

    info_dict = retrieve_image_info(meta_data)
    print(info_dict["as_string"])


