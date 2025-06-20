"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

Extension module for the RoiEditorControlPanel class from RoiEditor module
this module contains all input validation methods

"""
from types import MethodType

from .Context import gvars
from .RoiEditorControlPanel import *
from .MessageBoxInvalidValues import MessageBoxInvalidValues
from .Crumbs import format_float

def attach_extension_methods(self: 'RoiEditorControlPanel'):
    self.custom_scale_validate = MethodType(custom_scale_validate, self)
    self.remove_small_validate = MethodType(remove_small_validate, self)
    self.validate_entries_and_continue = MethodType(validate_entries_and_continue, self)

    self.is_custom_scale_valid = MethodType(is_custom_scale_valid, self)
    self.is_remove_small_valid = MethodType(is_remove_small_valid, self)

def is_custom_scale_valid(self: 'RoiEditorControlPanel'):
    text= self.le_custom_scale.text()
    rng =gvars["custom_scale_range"]
    minval = rng["minval"]
    maxval = rng["maxval"]
    fallback = rng["default"]
    return try_parse_float(val=text, minval=minval, maxval=maxval, fallback=fallback)

def is_remove_small_valid(self: 'RoiEditorControlPanel'):
    text = self.tbSize.text()
    rng =gvars["roi_minimum_size_range"]
    minval = rng["minval"]
    maxval = rng["maxval"]
    fallback = rng["default"]
    return try_parse_int(val=text, minval=minval, maxval=maxval, fallback=fallback)

def custom_scale_validate(self: 'RoiEditorControlPanel',text: str):
    (ok,_) = self.is_custom_scale_valid()
    if ok:
        self.le_custom_scale.setStyleSheet("")
    else:
        self.le_custom_scale.setStyleSheet("QLineEdit { border: 1px solid red; }")

def remove_small_validate(self: 'RoiEditorControlPanel',text:str):
    (ok,_) = self.is_remove_small_valid()
    if ok:
        self.tbSize.setStyleSheet("")
    else:
        self.tbSize.setStyleSheet("QLineEdit { border: 1px solid red; }")

def validate_entries_and_continue(self: 'RoiEditorControlPanel'):
    checked_id = self.bg_unit.checkedId()
    scale_text = self.le_scale_from_file.text()
    scale_from_file = (scale_text != '') and (scale_text!='unknown')
    ok_from_file = not (checked_id==self.ID_FROM_FILE) or scale_from_file # P => Q == not P or Q
    (ok_min_size,min_size) = self.is_remove_small_valid()
    (ok_custom_scale,custom_scale) = self.is_custom_scale_valid()

    if scale_from_file:
        scaler_length = float(scale_text)
        scaler_area = float(format_float(scaler_length * scaler_length,6))
    else:
        scaler_length = None
        scaler_area = None

    self.scalers[self.ID_FROM_FILE]["length"]["scaler"]=scaler_length
    self.scalers[self.ID_FROM_FILE]["area"]["scaler"]=scaler_area

    if ok_custom_scale:
        scaler_length = float(custom_scale)
        scaler_area = float(format_float(scaler_length * scaler_length,6))
    else:
        scaler_length = None
        scaler_area = None

    self.scalers[self.ID_SPECIFIED]["length"]["scaler"]=scaler_length
    self.scalers[self.ID_SPECIFIED]["area"]["scaler"]=scaler_area

    if (ok_min_size and ok_custom_scale and ok_from_file):
        gvars["roi_minimum_size"]=min_size
        gvars["selected_unit_and_scale"]=self.scalers[checked_id]
        return True # move on
    gvars["selected_unit_and_scale"] = None
    msgbox = MessageBoxInvalidValues(self)
    _ = msgbox.exec()
    return False # go back
            

import re

def try_parse_int(val, minval, maxval, fallback):
    m = re.match(r'\s*([+-]?\d+)\s*$', str(val))
    if not m:
        return (False,fallback)
    n = int(m.group(1))
    ok  = not(n<=0 or n < minval or n > maxval)
    return (ok, n if ok else fallback)

def try_parse_float(val, minval, maxval, fallback):
    m = re.match(r'^\s*(\d+(\.\d*)?|\.\d+)([eE](-[1-6]))?\s*$', str(val))
    if not m:
        return (False, fallback)
    f = float(m.group(0))
    ok = not (f <= 0 or f < minval or f > maxval )
    return (ok, f if ok else fallback)