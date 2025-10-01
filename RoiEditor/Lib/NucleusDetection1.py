#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
from math import isfinite

# ======= Bestandsnaam hier instellen =======
IMAGE_PATH = "C:\\Users\\bimba\\OneDrive\\Documenten\\source\\repos\\RoiProject\\RoiEditor\\tests\\TestData\\6_1.tif"

# ======= Helpers =======
def color_deconvolution_he(img_rgb_f32):
    """
    Ruifrok & Johnston colour deconvolution voor H&E.
    Input: float32 RGB in [0,1]
    Returns: H (hematoxyline) kanaal als float32, niet-genormaliseerd OD-coeff.
    """
    # Veelgebruikte H&E vectors (kolommen)
    H = np.array([0.650, 0.704, 0.286], dtype=np.float32)
    E = np.array([0.072, 0.990, 0.105], dtype=np.float32)
    R = np.cross(H, E).astype(np.float32)         # residuele derde as

    H /= np.linalg.norm(H) + 1e-12
    E /= np.linalg.norm(E) + 1e-12
    R /= np.linalg.norm(R) + 1e-12

    M = np.stack([H, E, R], axis=1)               # 3x3
    M_inv = np.linalg.inv(M)

    eps = 1e-6
    OD = -np.log(np.clip(img_rgb_f32, eps, 1.0))  # optische dichtheid
    C = OD.reshape(-1, 3) @ M_inv                 # mengcoëff in stain-ruimte
    C = C.reshape(img_rgb_f32.shape)              # (H, W, 3)

    H_chan = C[..., 0].astype(np.float32)         # hematoxyline
    return H_chan

def normalize_to_uint8(img_f32):
    mn, mx = float(np.min(img_f32)), float(np.max(img_f32))
    if not isfinite(mn) or not isfinite(mx) or (mx - mn) < 1e-12:
        return np.zeros_like(img_f32, dtype=np.uint8)
    out = (img_f32 - mn) / (mx - mn)
    out = np.clip(out * 255.0, 0, 255).astype(np.uint8)
    return out

def compute_centroids_by_moments(labels):
    """
    labels: int32 matrix na watershed
    returns: lijst met (x,y) float centroids voor labels >= 2
    """
    centroids = []
    max_label = int(labels.max())
    for L in range(2, max_label + 1):
        mask = (labels == L).astype(np.uint8)
        if cv.countNonZero(mask) == 0:
            continue
        m = cv.moments(mask, binaryImage=True)
        if m["m00"] > 0:
            cx = m["m10"] / m["m00"]
            cy = m["m01"] / m["m00"]
            centroids.append((float(cx), float(cy)))
    return centroids

# ======= Pipeline =======
def main():
    # 1) Inladen
    img_bgr = cv.imread(IMAGE_PATH, cv.IMREAD_COLOR)
    assert img_bgr is not None, f"Kon beeld niet lezen: {IMAGE_PATH}"
    img_rgb = cv.cvtColor(img_bgr, cv.COLOR_BGR2RGB)
    img_rgb_f32 = (img_rgb.astype(np.float32) / 255.0).copy()

    # 2) H&E deconvolutie → H-kanaal
    H_f32 = color_deconvolution_he(img_rgb_f32)
    H_u8 = normalize_to_uint8(H_f32)

    # 3) Lokaal contrast: CLAHE
    clahe = cv.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    H_clahe = clahe.apply(H_u8)

    # 4) Pseudo-CED: edge-preserving filter (snel alternatief)
    # Werkt op 3-kanaals; daarna terug naar grijs.
    H_clahe_bgr = cv.cvtColor(H_clahe, cv.COLOR_GRAY2BGR)
    H_ep_bgr = cv.edgePreservingFilter(
        H_clahe_bgr, flags=cv.RECURS_FILTER, sigma_s=50, sigma_r=0.3
    )
    H_ep = cv.cvtColor(H_ep_bgr, cv.COLOR_BGR2GRAY)

    # 5) Binaire segmentatie (Otsu). Inverteer 1e zodat "donker = nucleus" wordt foreground.
    H_inv = cv.bitwise_not(H_ep)
    _, nuclei_bin = cv.threshold(H_inv, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)

    # Ruis weg
    nuclei_bin = cv.morphologyEx(
        nuclei_bin,
        cv.MORPH_OPEN,
        cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3)),
        iterations=1,
    )

    # 6) Ontklonteren via DT + watershed
    # Sure foreground (FG) via distance transform threshold
    dist = cv.distanceTransform(nuclei_bin, distanceType=cv.DIST_L2, maskSize=3)
    dist_norm = cv.normalize(dist, None, 0, 1.0, cv.NORM_MINMAX)
    sure_fg = (dist_norm > 0.40).astype(np.uint8) * 255  # 0.3–0.6 tunen

    # Sure background (BG) via dilatatie van nuclei_bin
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3, 3))
    sure_bg = cv.dilate(nuclei_bin, kernel, iterations=2)

    # Unknown = bg - fg
    unknown = cv.subtract(sure_bg, sure_fg)

    # Markers uit connected components van sure_fg
    num_markers, markers = cv.connectedComponents(sure_fg)
    # markers moeten >0 zijn; reserveer 1 voor background
    markers = markers + 1
    # Unknown = 0
    markers[unknown == 255] = 0

    # Watershed op (licht) contrastrijk beeld; gradient helpt maar origineel werkt ook
    img_ws = img_bgr.copy()
    cv.watershed(img_ws, markers)   # markers wordt in-place geüpdatet

    # Resultaatlabels: -1 = grens, 1 = achtergrond, 2..N = objecten
    labels = markers.astype(np.int32)
    labels[labels == -1] = 0  # optioneel: grenzen als 0

    # 7) Centroids
    centroids = compute_centroids_by_moments(labels)

    # 8) Overlay tekenen (op RGB voor matplotlib)
    overlay_rgb = img_rgb.copy()
    for (x, y) in centroids:
        cv.circle(overlay_rgb, (int(round(x)), int(round(y))), 4, (0, 255, 0), -1)

    # 9) Visualisatie met matplotlib
    plt.figure(figsize=(10, 10))
    plt.imshow(overlay_rgb)
    plt.title(f"Nuclei overlay (count = {len(centroids)})")
    plt.axis("off")
    plt.show()

    # Optioneel: masks opslaan
    # cv.imwrite("nuclei_mask.png", (labels > 1).astype(np.uint8) * 255)

if __name__ == "__main__":
    main()
