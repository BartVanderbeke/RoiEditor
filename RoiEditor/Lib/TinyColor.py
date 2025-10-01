"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.cm import get_cmap
from PyQt6.QtGui import QColor,QBrush
import numpy as np
from TinyLog import log

# Colormap: green → yellow → orange → red
cmap = LinearSegmentedColormap.from_list("green_yellow_orange_red", [
    (0.0, "#00ff00"),
    (0.33, "#ffc800"),
    (0.67, "#ff8000"),
    (1.0, "#ff2000")
])


def values_to_qbrush_dict(rois, values, vmin, vmax):
    rgba = cmap(values)[:, :3]
    rgb = (rgba * 255).astype(np.uint8)
    return {roi: QBrush(QColor(*c)) for roi, c in zip(rois, rgb)}
