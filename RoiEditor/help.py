import numpy as np
import matplotlib.pyplot as plt
from skimage.io import imread
from skimage.color import rgb2hed
from skimage.color import rgb2hsv
from skimage.filters import threshold_otsu
from skimage import measure
from scipy import ndimage as ndi
import cv2 as cv

import logging
logging.getLogger("tifffile").setLevel(logging.ERROR)


def remove_internal_edges(label_img):
    """
        creates openings between adjacent labels or
        transitions from background to a label
        so findContours can be applied to the complete image
    """
    img = label_img.copy()

    h1 = img[:, :-1]
    h2 = img[:, 1:]
    hor_edge = (h1 != h2)

    v1 = img[:-1, :]
    v2 = img[1:, :]
    ver_edge = (v1 != v2)

    img[:, :-1][hor_edge] = 0
    img[:, 1:][hor_edge] = 0
    img[:-1, :][ver_edge] = 0
    img[1:, :][ver_edge] = 0

    return img.astype(np.uint8)

# Input file
filename = "segment/TestData/infolder/dir1/6_1.tif"
label_filename = "segment/TestData/infolder/dir1/6_1_cp_masks.png"


# Load RGB image & label image
raw_image = imread(filename)
original_image = raw_image

bkg_image = original_image.copy()
label_image = imread(label_filename)

#lbl_img = remove_internal_edges(label_image)
lbl_img = label_image
eroded_lbl_img = remove_internal_edges(label_image)


img_rgb = bkg_image.copy().astype(np.float32) / 255.0  # normalise
img_hsv = rgb2hsv(img_rgb)  # shape (H,W,3), H[0,1], S[0,1], V[0,1]

HH, SS, VV = img_hsv[...,0], img_hsv[...,1], img_hsv[...,2]

mask_selected_by_color = (
    (HH <= 300.0/360.0) & (HH > 200.0/360.0) &
    (SS >= 20.0/100.0)
)

mask_nuclei_in_fiber = (mask_selected_by_color) # & (lbl_img > 0)

# step 1.1 displayable image before removing small spots 
bkg_plus_nuclei = bkg_image.copy()
bkg_plus_nuclei[mask_nuclei_in_fiber] = [255, 255, 0]

# step 2: image with labels
nucleus_labels_img = measure.label(mask_nuclei_in_fiber)

mask = eroded_lbl_img != 0
dist_inside = ndi.distance_transform_edt(mask)
dist_outside = ndi.distance_transform_edt(~mask)
distmap = dist_inside - dist_outside

# step 3: remove small spots
props = measure.regionprops(nucleus_labels_img)
min_area= 20
to_be_kept_inside = set()
to_be_kept_edge = set()
to_be_kept_outside = set()
removed_maleformed = set()

for p in props:
    if p.area < min_area or p.eccentricity > 0.97:
        removed_maleformed.add(p.label)
    else:
        y,x = p.centroid
        x= int(x)
        y= int(y)
        nucleus_idx = nucleus_labels_img[y, x]
        cell_idx = lbl_img[y, x]
        if distmap[y, x] < 0 :
            to_be_kept_outside.add(p.label)
        elif distmap[y, x] < 5:
            to_be_kept_edge.add(p.label)
        else:
            to_be_kept_inside.add(p.label)


# step 4: make mask of 'to_be_kept' labels
mask_is_inside = np.isin(nucleus_labels_img, list(to_be_kept_inside))
mask_is_outside = np.isin(nucleus_labels_img, list(to_be_kept_outside))
mask_is_edge = np.isin(nucleus_labels_img, list(to_be_kept_edge))
mask_is_maleformed = np.isin(nucleus_labels_img, list(removed_maleformed))

bkg_plus_nuclei2 = bkg_image.copy()
bkg_plus_nuclei2[mask_is_inside] = [255, 255, 0] # yellow
bkg_plus_nuclei2[mask_is_outside] = [254, 1, 154] # pink
bkg_plus_nuclei2[mask_is_edge] = [57, 255, 20] # green
bkg_plus_nuclei2[mask_is_maleformed] = [0, 255, 255] # cyan

fig, axes = plt.subplots(2, 2, figsize=(10, 5))
axes[0,0].imshow(bkg_plus_nuclei2)
axes[0,0].set_title("Original original_image")
axes[0,0].axis("off")

axes[0,1].imshow(bkg_plus_nuclei)
axes[0,1].set_title("nuclei inside fiber")
axes[0,1].axis("off")

axes[1,0].imshow(distmap,cmap='rainbow')
axes[1,0].set_title("distance map")
axes[1,0].axis("off")

cbar = plt.colorbar(axes[1,0].images[0], ax=axes[1,0])


plt.tight_layout()
plt.show()
