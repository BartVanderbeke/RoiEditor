"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
from typing import Any
from .TinyLog import TinyLog

# when the keys mentioned below are hit while some ROIs are selected
# the ROIs are deleted and the ROIs are tagged with the justification for the deletion: "freeze",...
# F1 cannot be allocated, F2...F12 can be allocated

key_to_label_map: dict[str,str] = { "F5" : "freeze",            # all but the last line must end with comma
                                    "F6" : "fold",
                                    "F7" : "vessel",
                                    "F9" : "section.tear",
                                    "F10": "section.stretch"    # last line must not end with comma  
}

# gvars contains global variables
# 1. settings
# 2. global values (that still need to be moved to clean params)
gvars: dict[str, Any] = {}
gvars["show_names"]=True        # (do not) show the names of the ROIs on the image
gvars["show_deleted"]=True      # (do not) show the deleted ROIs on the image
gvars["show_overlay"]=True      # (do not) fill the ROIs with color

gvars["save_rois_num_threads"] = 12
gvars["read_parallel_num_threads"] = 2
gvars["remove_at_edge"] = True
gvars["roi_minimum_size"] = 100
gvars["remove_small"] = True
gvars["backup_interval_timer"] = 15 * 60 * 1000 # 15 minutes
gvars["log_level"] = TinyLog.LOG_LVL_NORMAL
gvars["selected_unit_and_scale"] = None


gvars["roi_minimum_size_range"] = { "minval": 49,  "default": 100, "maxval": 4999}
# the regex used for custom_scale limits to >1e-6 automatically
gvars["custom_scale_range"] = { "minval": 1e-6,  "default": 0.645, "maxval": 50.0}
 