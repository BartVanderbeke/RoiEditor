import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import cv2
import numpy as np
import csv
import os
from pathlib import Path

# --- instellingen ---
tiff_file = "RoiEditor/TestData/infolder/dir1/6_1.tif"   # zet hier je tiff-bestand
csv_file = "pixels.csv"   # output CSV

# --- CSV voorbereiden ---
new_file = not os.path.exists(csv_file)
with open(csv_file, "a", newline="") as f:
    writer = csv.writer(f, delimiter=";")
    if new_file:
        writer.writerow(["H", "S", "V"])  # header indien nieuw bestand

# --- beeld laden (met cv2 voor HSV) ---
bgr = cv2.imread(tiff_file, cv2.IMREAD_COLOR)
if bgr is None:
    print(f"Kan bestand niet openen: {Path(tiff_file).absolute()}")
    raise FileNotFoundError()

rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

fig, ax = plt.subplots()
ax.imshow(rgb)
ax.set_title("Klik links om HSV te loggen")

def onclick(event):
    if event.inaxes != ax: 
        return
    if event.button == 1:  # linkermuisknop
        x = int(round(event.xdata))
        y = int(round(event.ydata))
        if 0 <= x < hsv.shape[1] and 0 <= y < hsv.shape[0]:
            H, S, V = hsv[y, x]
            print(f"Klik op ({x},{y}) -> H={H}, S={S}, V={V}")
            with open(csv_file, "a", newline="") as f:
                writer = csv.writer(f, delimiter=";")
                writer.writerow([H, S, V])

cid = fig.canvas.mpl_connect("button_press_event", onclick)
plt.show()
