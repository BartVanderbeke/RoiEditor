"""Extension module for the RoiMeasurements class
this module contains all methods for writing measurements to file

"""
"""RoiEditor

Author: Bart Vanderbeke
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
import threading
from types import MethodType
from io import StringIO
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name

from .Roi import Roi
from .RoiMeasurements import *
   
def attach_extension_methods(self):
    self.save_measurements_to_csv=MethodType(save_measurements_to_csv, self)
    self.save_measurements_to_xlsx=MethodType(save_measurements_to_xlsx, self)

# writing the measurements to a csv
# 1. prepare the data in memory
def _build_measurement_csv(data, measurement_names, subset_name="ALL"):

    measurements = data[subset_name]
    just_a_measurement = measurements[measurement_names[0]]
    num_of_values = len(just_a_measurement)

    buffer = StringIO()
    header = ['name'] + measurement_names + ["STATE"] + ["TAGS"]
    buffer.write(';'.join(header) + '\n')

    for row_idx in range(num_of_values):
        roi = measurements["Roi"][row_idx]
        roi_state_str = Roi.state_to_str(roi.state)
        roi_tag_str = ', '.join(roi.tags)
        row = [roi.name] + [
            f"{measurements[msmt_name][row_idx]:.3f}".replace('.', ',')
            for msmt_name in measurement_names
        ] + [roi_state_str, roi_tag_str]
        buffer.write(';'.join(row) + '\n')

    return buffer.getvalue()

# 2. flush it in 1 go to disk, there is no need to wait
#    fire & forget, but daemon=False makes sure it will happen
def _write_to_file_later(path, text_data):
    def _writer():
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text_data)
    threading.Thread(target=_writer, daemon=False).start()


def save_measurements_to_csv(self: 'RoiMeasurements.RoiMeasurements', full_name, subset_name="ALL"):
    csv_string = _build_measurement_csv(self.orig, self.measurement_names, subset_name)
    _write_to_file_later(full_name, csv_string)

def _build_measurement_xlsx_table_data(msmts, subset_name="ALL"):
    import numpy as np

    data: dict[str, np.ndarray] = msmts.orig
    measurement_names = msmts.measurement_names
    measurements = data[subset_name]
    just_a_measurement = measurements[measurement_names[0]]
    num_of_values = len(just_a_measurement)

    header_pixels_all = ['name'] + measurement_names + ['STATE', 'TAGS']
    rows_pixels_all = []

    header_pixels_act = ['name'] + measurement_names
    rows_pixels_act = []

    for row_idx in range(num_of_values):
        roi = measurements["Roi"][row_idx]
        roi_state_str = Roi.state_to_str(roi.state)
        roi_tag_str = ', '.join(roi.tags)
        row_pxl = [roi.name] + [
            measurements[msmt_name][row_idx]
            for msmt_name in measurement_names]
        if roi.state == Roi.ROI_STATE_ACTIVE:
            rows_pixels_act.append(row_pxl)
        row_pxl = row_pxl + [roi_state_str, roi_tag_str]
        rows_pixels_all.append(row_pxl)

    num_rows_pixels_all = len(rows_pixels_all) + 1  # +1 for header
    num_cols_pixels_all = len(header_pixels_all)

    num_rows_pixels_act = len(rows_pixels_act) + 1  # +1 for header
    num_cols_pixels_act = len(header_pixels_act)



    wb = {
        "pixels_ALL": {
            "table_type": "regular",
            "tbl_name": "tblPixelsAll",
            "header": header_pixels_all,
            "rows": rows_pixels_all,
            "shape": (num_rows_pixels_all, num_cols_pixels_all)
        }
    }

    wb["pixels_ACT"] = {
            "table_type": "regular",
            "tbl_name": "tblPixelsAct",
            "header": header_pixels_act,
            "rows": rows_pixels_act,
            "shape": (num_rows_pixels_act, num_cols_pixels_act)
    }

    scale_sheet = "scalers"
    scale_header = ["what"] + measurement_names
    unit_row = ["unit"]
    scaler_row = ["scaler"]
    for msmt in measurement_names:
        unit_row.append(msmts.units_and_scalers[msmt]["unit"])
        scaler_row.append(msmts.units_and_scalers[msmt]["scaler"])
    scale_rows = [unit_row, scaler_row]

    wb[scale_sheet] = {
        "table_type": "regular",
        "tbl_name": "tblScalers",
        "header": scale_header,
        "rows": scale_rows
    }

    col_defs = []
    # 1. name-column
    col_defs.append({
        'header': 'name',
        'formula': 'tblPixelsAct[@name]'
    })

    # 2. scaled values
    for col_idx, msmt in enumerate(header_pixels_all[1:-2], start=1):
        col_letter = xl_col_to_name(col_idx)  # A = 0, B = 1
        scaler_cell = f"scalers!${col_letter}$3"
        col_defs.append({
            'header': msmt,
            'formula': f"tblPixelsAct[@{msmt}] * {scaler_cell}"
        })

    content = {
            'columns': col_defs,
            'name': "tblScaledAct",
            'style': 'Table Style Medium 9'}
    

    wb["scaled_ACT"] = {
        "table_type": "fancy",
        "content": content,
        "shape":  (num_rows_pixels_act,num_cols_pixels_act)
    }


    col_headers_summary = ['stat'] + measurement_names
    row_headers_summary = ["N", "max", "min", "avg", "med", "MAD", "IQR"]

    rows_summary = [ [h] for h in row_headers_summary]
    for col in measurement_names:
        col_ref = f"tblScaledAct[{col}]"
        formulas  = {"N" :  f"=COUNT({col_ref})",
                    "max": f"=MAX({col_ref})",
                    "min": f"=MIN({col_ref})",
                    "avg": f"=AVERAGE({col_ref})",
                    "med": f"=MEDIAN({col_ref})",
                    "MAD": f"=MEDIAN(ABS({col_ref} - MEDIAN({col_ref})))",
                    "IQR": f"=QUARTILE({col_ref},3)-QUARTILE({col_ref},1)"
        }
        for row_idx,row in enumerate(row_headers_summary):
            formula = formulas[row]
            rows_summary[row_idx].append(formula)


    num_rows_summary = len(row_headers_summary) + 1  # +1 for col header
    num_cols_summary = len(measurement_names) + 1  # +1 for row header

    wb["summary_ACT"] = {
        "table_type": "regular",
        "tbl_name": "tblSummaryAct",
        "header": col_headers_summary,
        "rows": rows_summary,
        "shape": (num_rows_summary,num_cols_summary)
    }


    order = ["summary_ACT","scaled_ACT","scalers","pixels_ACT","pixels_ALL"]
    return wb,order

def _write_xlsx_later(path, wb,order):

    def _writer():
        workbook = xlsxwriter.Workbook(path)

        for sheet_name in order:
            sheet = wb[sheet_name]
            if sheet["table_type"]=="regular":
                worksheet = workbook.add_worksheet(sheet_name)

                for col, val in enumerate(sheet["header"]):
                    worksheet.write(0, col, val)

                for row_idx, row in enumerate(sheet["rows"], start=1):
                    for col_idx, val in enumerate(row):
                        if isinstance(val, float):
                            worksheet.write_number(row_idx, col_idx, val)
                        else:
                            worksheet.write(row_idx, col_idx, val)

                num_rows = len(sheet["rows"]) + 1  # +1 for header
                num_cols = len(sheet["header"])
                worksheet.add_table(0, 0, num_rows - 1, num_cols - 1, {
                    'columns': [{'header': h} for h in sheet["header"]],
                    'name': sheet["tbl_name"],
                    'style': 'Table Style Medium 9'
                })
            else:
                (num_rows,num_cols)=sheet["shape"]
                worksheet = workbook.add_worksheet(sheet_name)
                worksheet.add_table(0, 0, num_rows - 1, num_cols - 1, sheet["content"])

        workbook.close()

    threading.Thread(target=_writer, daemon=False).start()

def save_measurements_to_xlsx(self, full_name, subset_name="ALL"):
    wb,order = _build_measurement_xlsx_table_data(self,subset_name)
    _write_xlsx_later(full_name, wb,order)