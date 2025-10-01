"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.
"""

import numpy as np


# def average_color(image_rgb: np.ndarray, label_image: np.ndarray) -> np.ndarray:
#     """
#     Calculate the average RGB color for each label in the label image.
#     """
#     if image_rgb.ndim != 3 or image_rgb.shape[2] != 3:
#         raise ValueError("Input image must be an RGB image with shape (H, W, 3).")
#     if label_image.ndim != 2 or label_image.shape != image_rgb.shape[:2]:
#         raise ValueError("Labels must be a 2D array with the same height and width as the image.")

#     num_labels = np.unique(label_image).max() + 1  # Assuming labels are 0-indexed
#     image_float = image_rgb.astype(np.float32) / 255.0

#     flat_labels = label_image.ravel()
#     flat_rgb = image_float.reshape(-1, 3)

#     means = np.zeros((num_labels, 3), dtype=np.float32)

#     for lbl in range(num_labels):
#         mask = flat_labels == lbl
#         if not mask.any():
#             means[lbl] = np.array([[0.0, 0.0, 0.0]])
#             continue
#         means[lbl] = flat_rgb[mask].mean(axis=0)

#     return means



def average_color(image_rgb: np.ndarray, label_image: np.ndarray) -> np.ndarray:
    if image_rgb.ndim != 3 or image_rgb.shape[2] != 3:
        raise ValueError("image_rgb must be (H, W, 3)")
    if label_image.ndim != 2 or label_image.shape != image_rgb.shape[:2]:
        raise ValueError("label_image must be (H, W) matching the image")

    flat_labels = label_image.reshape(-1)
    num_labels = int(flat_labels.max()) + 1  # labels 0..L

    flat = image_rgb.reshape(-1, 3)          # uint8 ok
    counts = np.bincount(flat_labels, minlength=num_labels).astype(np.float64)

    # Sums per label per kanaal (float64 voorkomt precisieverlies)
    sums_r = np.bincount(flat_labels, weights=flat[:, 0].astype(np.float64), minlength=num_labels)
    sums_g = np.bincount(flat_labels, weights=flat[:, 1].astype(np.float64), minlength=num_labels)
    sums_b = np.bincount(flat_labels, weights=flat[:, 2].astype(np.float64), minlength=num_labels)
    sums = np.stack((sums_r, sums_g, sums_b), axis=1)  # (L,3)

    # Gemiddelde in [0,1]; labels zonder pixels → 0
    out = np.zeros((num_labels, 3), dtype=np.float32)
    valid = counts > 0
    out[valid] = (sums[valid] / (counts[valid, None] * 255.0)).astype(np.float32)
    return out




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
