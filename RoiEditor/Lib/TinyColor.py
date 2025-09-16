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
    (0.33, "#ffff00"),
    (0.67, "#ff8000"),
    (1.0, "#ff0000")
])


def values_to_qbrush_dict(rois, values, vmin, vmax):
    if values.size == 0:
        return {}

    if vmax == vmin:
        log(f"Warning: vmax ({vmax}) == vmin ({vmin}). All values set to 0.", type="info", log_level=1000)
        normed = np.zeros_like(values, dtype=float)
    else:
        normed = (values - vmin) / (vmax - vmin)

    rgba = cmap(normed)[:, :3]
    rgb = (rgba * 255).astype(np.uint8)
    return {roi: QBrush(QColor(*c)) for roi, c in zip(rois, rgb)}
