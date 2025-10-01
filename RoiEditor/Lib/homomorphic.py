import numpy as np
import cv2 as cv
def homomorphic_filter(image):
    assert image.ndim == 2, "homomorphic_filter: input image must be grayscale"
    rows, cols = image.shape
    # Convert to log space
    log_image = np.log1p(np.array(image, dtype="float"))
    
    # Perform Fourier Transform
    dft = np.fft.fft2(log_image)
    dft_shift = np.fft.fftshift(dft)

    # Create a high-pass filter
    crow, ccol = rows // 2 , cols // 2
    mask = np.ones((rows, cols), dtype="float32")
    r = 30  # Radius of low-frequency region to suppress
    cv.circle(mask, (ccol, crow), r, 0, -1)

    # Apply the filter
    filtered_dft = dft_shift * mask

    # Inverse Fourier Transform
    dft_inverse = np.fft.ifftshift(filtered_dft)
    result = np.fft.ifft2(dft_inverse)
    result = np.exp(np.real(result)) - 1
    
    # Normalize result to uint8
    result = cv.normalize(result, None, 0, 255, cv.NORM_MINMAX).astype("uint8")
    
    return result

def radial_profile(fft_amp):
    """Bereken radiaal gemiddelde amplitude van een FFT-spectrum"""
    rows, cols = fft_amp.shape
    cy, cx = rows // 2, cols // 2
    y, x = np.indices((rows, cols))
    r = np.sqrt((x - cx)**2 + (y - cy)**2).astype(np.int32)

    # gemiddelde amplitude per radius
    r_max = r.max()
    radial_mean = np.bincount(r.ravel(), fft_amp.ravel()) / np.bincount(r.ravel())
    return np.arange(r_max+1), radial_mean

if __name__ == "__main__":

    import cv2
    import matplotlib.pyplot as plt

    # Inlezen van RGB-beeld
    img_rgb = cv2.imread("C:\\Users\\bimba\\OneDrive\\Documenten\\source\\repos\\RoiProject\\RoiEditor\\tests\\TestData\\6_1.tif")
    img_rgb = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2RGB)

    # Conversie naar HSV en terug naar RGB
    img_hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
    img_hsv2= img_hsv.copy()

    H2 = img_hsv2[:, :, 0]   # Alleen het H-kanaal
    S2 = img_hsv2[:, :, 1]   # Alleen het S-kanaal
    V2 = img_hsv2[:, :, 2]   # Alleen het V-kanaal

    # Pas een homomorfische filter toe op het V-kanaal
    H_filtered = homomorphic_filter(H2)

    # Stel het gefilterde V-kanaal weer in
    img_hsv2[:, :, 0] = H_filtered

    img_rgb2 = cv2.cvtColor(img_hsv2, cv2.COLOR_HSV2RGB)

    # Figuren maken: 2 boven, 1 histogram onder
    fig = plt.figure(figsize=(10, 8))

    # Links: origineel
    ax1 = plt.subplot(2, 2, 1)
    ax1.imshow(img_rgb)
    ax1.set_title("Beeld 1 (origineel RGB)")
    ax1.axis("off")

    # Rechts: HSV→RGB
    ax2 = plt.subplot(2, 2, 2)
    ax2.imshow(img_rgb2)
    ax2.set_title("Beeld 2 (HSV → RGB)")
    ax2.axis("off")

    # Histogram onderaan, 2 lijnen
    ax3 = plt.subplot(2, 1, 2)
    bins = np.arange(181)  # 0–180

    hist_H, _ = np.histogram(img_hsv[:, :, 0].ravel(), bins=bins, range=(0,181))
    hist_Hf, _ = np.histogram(H_filtered.ravel(), bins=bins, range=(0,181))

    ax3.plot(bins[:-1], hist_H, color="blue", label="H")
    ax3.plot(bins[:-1], hist_Hf, color="red", label="H filtered")

    ax3.set_title("Histogram H vs H filtered")
    ax3.set_xlabel("Hue waarde (0–255)")
    ax3.set_ylabel("Aantal pixels")
    ax3.legend()

    plt.tight_layout()
    plt.show()