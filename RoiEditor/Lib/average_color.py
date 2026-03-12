"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.
"""

import numpy as np
from numba import njit

@njit(cache=True)
def _average_color_jit(image_rgb: np.ndarray, label_image: np.ndarray) -> np.ndarray:
    max_label = int(np.max(label_image))
    num_labels = max_label + 1
    sums = np.zeros((num_labels, 3), dtype=np.float64)
    counts = np.zeros(num_labels, dtype=np.int64)

    height, width = label_image.shape
    for y in range(height):
        for x in range(width):
            lbl = int(label_image[y, x])
            counts[lbl] += 1
            px = image_rgb[y, x]
            sums[lbl, 0] += float(px[0])
            sums[lbl, 1] += float(px[1])
            sums[lbl, 2] += float(px[2])

    out = np.zeros((num_labels, 3), dtype=np.float32)
    for lbl in range(num_labels):
        c = counts[lbl]
        if c > 0:
            inv = 1.0 / (float(c) * 255.0)
            out[lbl, 0] = np.float32(sums[lbl, 0] * inv)
            out[lbl, 1] = np.float32(sums[lbl, 1] * inv)
            out[lbl, 2] = np.float32(sums[lbl, 2] * inv)

    return out


def average_color(image_rgb: np.ndarray, label_image: np.ndarray) -> np.ndarray:
    if image_rgb.ndim != 3 or image_rgb.shape[2] != 3:
        raise ValueError("image_rgb must be (H, W, 3)")
    if label_image.ndim != 2 or label_image.shape != image_rgb.shape[:2]:
        raise ValueError("label_image must be (H, W) matching the image")
    return _average_color_jit(image_rgb, label_image)

def global_average_rgb(avg_colors: np.ndarray) -> np.ndarray:
    """
    Compute the global average RGB color over all labels.
    """
    avg_colors = avg_colors[1:]  # Exclude background label 0
    is_valid = (
    avg_colors is not None
    and getattr(avg_colors, "size", 0) > 0
    and getattr(avg_colors, "ndim", 0) == 2
    and getattr(avg_colors, "shape", (None, None))[-1] == 3
)
    if not is_valid:
        return np.array([0.0, 0.0, 0.0], dtype=np.float32)
    return avg_colors.mean(axis=0).astype(np.float32)


def rgb_distances(avg_colors: np.ndarray, global_rgb_avg: np.ndarray) -> np.ndarray:
    """
    Euclidean distance of each label's average RGB to the global average RGB.
    """
    is_valid = (
    avg_colors is not None
    and global_rgb_avg is not None
    and avg_colors.size > 0
    and avg_colors.ndim == 2
    and avg_colors.shape[-1] == 3
    and global_rgb_avg.shape == (3,)
)
    if not is_valid:
        return np.array([], dtype=np.float32)
    diff = avg_colors - global_rgb_avg
    return np.linalg.norm(diff, axis=1)


def distance_array(avg_colors: np.ndarray) -> np.ndarray:
    """
    Convenience wrapper:
    Compute global average RGB and distances per label in one step.
    """
    global_rgb = global_average_rgb(avg_colors)
    return rgb_distances(avg_colors, global_rgb)


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from skimage.io import imread

    # Input files
    filename = r"C:\Users\bimba\OneDrive\Documenten\source\repos\RoiProject\RoiEditor\tests\TestData\B_stitch.tiff"
    label_filename = r"C:\Users\bimba\OneDrive\Documenten\source\repos\RoiProject\RoiEditor\tests\TestData\B_stitch_cp_masks.png"

    # Load data
    bkg_image = imread(filename)
    cell_lbl_image = imread(label_filename)

    # Compute per-label averages and distances
    avg_colors = average_color(bkg_image, cell_lbl_image)
    distances = distance_array(avg_colors)

    # Stats
    mean_dist = np.mean(distances)
    median_dist = np.median(distances)
    stdev_dist = np.std(distances)

    # --- Plot ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Histogram
    ax1.hist(distances, bins=100, color="purple", alpha=0.6, edgecolor="black")
    ax1.axvline(mean_dist, color="red", linestyle="--", linewidth=2,
                label=f"Mean = {mean_dist:.3f}")
    ax1.axvline(median_dist, color="green", linestyle="-.", linewidth=2,
                label=f"Median = {median_dist:.3f}")
    ax1.axvline(mean_dist+stdev_dist, color="blue", linestyle="-.", linewidth=2,
                label=f"+stdev = {stdev_dist:.3f}")
    ax1.axvline(mean_dist-stdev_dist, color="blue", linestyle="-.", linewidth=2,
                label=f"-stdev = {stdev_dist:.3f}")
    ax1.set_xlabel("Euclidean distance to overall mean RGB")
    ax1.set_ylabel("# labels")
    ax1.set_title("Histogram color distances")
    ax1.legend()
    ax1.grid(True, linestyle="--", alpha=0.5)

    # CDF
    sorted_dist = np.sort(distances)
    cdf = np.arange(1, len(sorted_dist) + 1) / len(sorted_dist)
    ax2.plot(sorted_dist, cdf, color="blue", linewidth=2)
    ax2.axvline(mean_dist, color="red", linestyle="--", linewidth=2,
                label=f"Mean = {mean_dist:.3f}")
    ax2.axvline(median_dist, color="green", linestyle="-.", linewidth=2,
                label=f"Median = {median_dist:.3f}")
    ax2.axvline(mean_dist+stdev_dist, color="blue", linestyle="-.", linewidth=2,
                label=f"+stdev = {stdev_dist:.3f}")
    ax2.axvline(mean_dist-stdev_dist, color="blue", linestyle="-.", linewidth=2,
                label=f"-stdev = {stdev_dist:.3f}")
    ax2.set_xlabel("Euclidean distance to overall mean RGB")
    ax2.set_ylabel("Cumulative fraction")
    ax2.set_title("Cumulative distribution (CDF)")
    ax2.legend()
    ax2.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.show()
