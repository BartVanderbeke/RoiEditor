"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
import zipfile
from typing import List, Optional
from typing import Final
from concurrent.futures import ThreadPoolExecutor
import numpy as np

from .Roi import Roi
from .TinyLog import log

class TinyRoiFile:
    """
        TinyRoiFile implements a reader and writer for Fiji compatible ROI/zip files
        An ROI zip file is a zip file containing .roi files: "1 .roi file == 1 ROI"
        Only the ROI_TYPE_POLYGON, ROI_TYPE_TRACED, ROI_TYPE_FREEHAND can be read or written
        TinyRoiFile imposes a naming convention for ROIs and their file: Ldddd.roi
        d=digit, the number of digits is derived from the number of Rois in the zip file
        TinyRoiFile can read ROI zip files generated by cellpose if they belong to the types described above
        TinyRoiFile adds a tags.json file to the zip in which the state and the tags of the ROI are stored
        TinyRoiFile is a stripped version of https://pypi.org/project/roifile/  (Christoph Gohlke)
    """
    HEADER_SIZE: Final[int] = 64
    ROI_TYPE_POLYGON: Final[int] = 0
    ROI_TYPE_TRACED: Final[int] = 8
    ROI_TYPE_FREEHAND: Final[int] = 7
    SUPPORTED_ROI_TYPES: Final[set[int]] = {ROI_TYPE_POLYGON, ROI_TYPE_TRACED, ROI_TYPE_FREEHAND}

    @staticmethod
    def write_parallel(zip_path: str, roi_list: List[Optional[Roi]], num_threads: int = 4) -> None:
        def encode_roi(roi: Roi) -> tuple[str, bytes]:
            top, left, bottom, right = roi.bounds

            x = (np.asarray(roi.xpoints, dtype=np.int16) - left).astype('>i2')  # big-endian int16
            y = (np.asarray(roi.ypoints, dtype=np.int16) - top ).astype('>i2')

            header = bytearray(TinyRoiFile.HEADER_SIZE)
            header[0:4] = b'Iout'
            header[6] = TinyRoiFile.ROI_TYPE_POLYGON
            header[8:10]  = int(top).to_bytes(2, byteorder='big', signed=True)
            header[10:12] = int(left).to_bytes(2, byteorder='big', signed=True)
            header[12:14] = int(bottom).to_bytes(2, byteorder='big', signed=True)
            header[14:16] = int(right).to_bytes(2, byteorder='big', signed=True)
            header[16:18] = int(roi.n).to_bytes(2, byteorder='big', signed=True)

            x_bytes = x.tobytes()
            y_bytes = y.tobytes()

            return roi.name + ".roi", header + x_bytes + y_bytes

        roi_tasks = [roi for roi in roi_list if roi]
        num_tasks = len(roi_tasks)
        chunk_size = (num_tasks + num_threads - 1) // num_threads
        chunks = [roi_tasks[i:i + chunk_size] for i in range(0, num_tasks, chunk_size)]

        results = []

        def worker(chunk):
            return [encode_roi(roi) for roi in chunk]

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for chunk_result in executor.map(worker, chunks):
                results.extend(chunk_result)


        # Step 1: construct zip in memory
        # ZIP_STORED = no compression, zip is only used for Fiji compatibility
        import io
        import json
        mem_zip = io.BytesIO()
        with zipfile.ZipFile(mem_zip, 'w', compression=zipfile.ZIP_STORED) as zipf:
            tag_json = {}
            for name, data in results:
                zipf.writestr(name, data)
            for roi in roi_list:
                if roi:
                    json_value = [Roi.state_to_str(roi.state)] + list(roi.tags)
                    tag_json[roi.name] = json_value
            json_data = json.dumps(tag_json)
            zipf.writestr("tags.json", json_data.encode("utf-8"))

        #Step 2: flush it in 1 move
        # with open(zip_path, 'wb') as f:
            # f.write(mem_zip.getvalue())

        def save_zip(path, data):
            with open(path, 'wb') as f:
                f.write(data)

        # Fire & Forget: no need to wait for data to be saved
        # daemon=False --> makes sure that the thread is not stopped when the program is stopped
        import threading
        threading.Thread(target=save_zip, args=(zip_path, mem_zip.getvalue()), daemon=False).start()

    @staticmethod
    # works on filename without extension!
    def _is_valid_roi_name(name: str):
        return (
            name.startswith("L") and
            name[1:].isdigit()
        )

    @staticmethod
    def _all_L_names(entry_list: list[str]):
        return all(TinyRoiFile._is_valid_roi_name(n) for n in entry_list)
    
    @staticmethod
    def read_parallel(zip_path: str, label_image,num_threads: int = 4) -> List[Optional[Roi]]:
        import io
        with  open(zip_path, "rb") as zipf:
                zip_bytes = zipf.read()
        zip_buffer = io.BytesIO(zip_bytes)  # ← hier komt het verschil
        with zipfile.ZipFile(zip_buffer, 'r') as zipf:
            name_list= zipf.namelist()
            roi_data_dict = {
                name[:-4]: zipf.read(name) # drop '.roi'
                for name in name_list
                if name.lower().endswith('.roi')
            }
            tag_json=None
            has_json = "tags.json" in name_list
            if has_json:
                json_tags_data=zipf.read("tags.json")
                log("json detected")
                import json
                tag_json = json.loads(json_tags_data.decode("utf-8"))


        names = list(roi_data_dict.keys())
        all_l =TinyRoiFile._all_L_names(names)

        if all_l:
            roi_indices = [int(n[1:]) for n in names]
            max_index = np.max(roi_indices)
            l = len(names)
            if l != max_index:
                log(f"Mismatch between #ROI-files and indices: #ROI-files: {l} <> max. index: {max_index} ",type="error")
                full = set(range(min(roi_indices), max(roi_indices) + 1))
                missing = sorted(full - set(roi_indices))
                log(f"Missing labels: {missing} ",type="error")
            num_to_use = max(max_index,l)+1
            roi_array=np.array([None] * (num_to_use),dtype=object) #List[Optional[Roi]] = [None] * (num_to_use)

            if has_json:
                for roi_name in names:
                    data = roi_data_dict[roi_name]
                    roi: Roi = TinyRoiFile._decode(data, roi_name)
                    idx = int(roi_name[1:]) # number
                    roi_array[idx] = roi
                    values = tag_json.get(roi_name, None)
                    if values:
                        roi.state = Roi.str_to_state(values[0])
                        roi.tags = set(values[1:])
            else:
                for roi_name in names:
                    data = roi_data_dict[roi_name]
                    roi = TinyRoiFile._decode(data,roi_name)
                    idx = int(roi_name[1:])
                    roi_array[idx] = roi
        else:
            roi_dict = {}
            for name in names:
                data = roi_data_dict[name]
                roi: Roi = TinyRoiFile._decode(data,name)
                (cx,cy) = (roi.center)
                idx = label_image[int(cy),int(cx)]
                roi_dict[idx] = roi
            kys = list(roi_dict.keys())
            max_index = np.max(kys)
            l = len(kys)
            num_to_use = max(max_index,l)+1
            max_digits = len(str(num_to_use))
            labels = [f"L{idx:0{max_digits}d}" for idx in range(num_to_use)]
            roi_array=np.array([None] * (num_to_use),dtype=object)
            for idx,roi in roi_dict.items(): 
                roi_array[idx]=roi
                roi.name=labels[idx]
            if l != max_index:
                log(f"Mismatch between #ROI-files and indices: #ROI-files: {l} <> max. index: {max_index} ",type="error")
                full = set(range(min(kys), max_index + 1))
                missing = sorted(full - set(kys))
                log(f"Missing labels: {missing} ",type="error")
        return roi_array
    
    @staticmethod
    def _decode(data: bytes, name: str = "") -> Optional[Roi]:
        if data[0:4] != b'Iout':
            log(f"{name} is not a valid ROI file (missing 'Iout' signature)", type="error")
            return None

        roi_type: int = data[6]
        if roi_type not in TinyRoiFile.SUPPORTED_ROI_TYPES:
            log(f"File {name} contains a not supported ROI type: {roi_type}", type="error")
            return None

        
        top, left, bottom, right, n = np.frombuffer(data, dtype='>i2', count=5, offset=8)

        HEADER_SIZE=TinyRoiFile.HEADER_SIZE
        x = np.frombuffer(data[HEADER_SIZE : HEADER_SIZE + 2 * n], dtype='>i2').astype(np.int32)
        y = np.frombuffer(data[HEADER_SIZE + 2 * n : HEADER_SIZE + 4 * n], dtype='>i2').astype(np.int32)

        xpoints = x + left
        ypoints = y + top

        center=(np.mean(xpoints),np.mean(ypoints))

        return Roi(xpoints, ypoints, name=name, state=Roi.ROI_STATE_ACTIVE, center = center, bounds=(top, left, bottom, right), n=n)

