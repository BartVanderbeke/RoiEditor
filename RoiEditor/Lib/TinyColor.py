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

# Colormap: green → yellow → orange → red
cmap = LinearSegmentedColormap.from_list("green_yellow_orange_red", [
    (0.0, "#00ff00"),
    (0.33, "#ffff00"),
    (0.67, "#ff8000"),
    (1.0, "#ff0000")
])


def map_values_to_qbrush(values: np.ndarray, qbrush: np.ndarray, vmin: float, vmax: float) -> None:
    """
    Fills an existing array of  QColor-objects with new colors to associate a range of colors
    to the rrange [vmin,vmax]
    """
    assert values.shape == qbrush.shape, "Values en qcolors must have the same shape"
    assert np.all(np.isfinite(values)), "Values must be finite"
    assert np.all((values >= vmin) & (values <= vmax)), f"Values are outseide the range [{vmin}, {vmax}]!"

    normed = (values - vmin) / (vmax - vmin)
    rgba = cmap(normed)  # shape (N, 4)
    rgb = (rgba[:, :3] * 255).astype(np.uint8)

    for i, (r, g, b) in enumerate(rgb):
        qbrush[i]=QBrush(QColor(r, g, b))