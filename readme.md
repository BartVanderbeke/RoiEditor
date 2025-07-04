# ROI Editor

**ROI Editor** is an interactive Python application for managing, editing, and analyzing Regions of Interest (ROIs) in image data.
The goal of RoiEditor is to remove “bad ROIs” from microscope images and to generate the data to perform statistics on the basic ROI properties: area and the Feret-parameters.
RoiEditor 2.0 has extended editing capabilities, but lacks the erosion and multiple slice functionality of the Fiji plugin [LabelsToRois](https://labelstorois.github.io/). RoiEditor 2.0 is a standalone implementation of RoiEditor using regular Python aka CPython.
RoiEditor cannot segment ROIs in photographs. [cellpose](https://www.cellpose.org/) is used for that purpose.


## ✨ Features
- The original photograph is loaded from a .png or .tif(f) file.
- The cellpose label-data can be read from a .npy or .png file.
- The ROIs are stored in and read back from a Fiji compatible ROI zip file.
- Contrary to most ROI-handling apps or plug ins, RoiEditor never removes ROIs from the collection:
  Deleted ROIs are marked, but not removed.
- The state data and other metadata is stored in a json file in the ROI zip file.
- The scaling of the image (μm/pixel) can be read from the original tif(f) file or set manually.
- Area & Feret measurements are computed for all ROIs.
- The stats for each measurement are shown in a histogram window.
- The user can select the edge of the ROI-cloud or the outliers for each measurement for deletion.
- An outlier for a measurement is a value outside of [q1 - 1.5 * IQR,q3 + 1.5 * IQR].
- When the image overlay is activated, a color range from green to red indicates the distance from the median for the selected measurement for each individual ROI.
- The measurements and statistics are written to both and .xlsx and a .csv file.
- The ROI data is backed up every 15 minutes.
- Installers for RoiEditor, cellpose and Python are added as .bat files for installation on Windows.
- When installed using the .bat files, desktop icons/shortcuts are created for RoiEditor and cellpose.

## 🙏 Acknowledgement
The team of Prof. Katrien Koppo at KU Leuven kindly granted permission to use the sample images in the TestData folder.

RoiImage uses a trimmed down version of Pierre Raybaut's [array2d_to_qpolygonf](https://github.com/PlotPyStack/PythonQwt/blob/master/qwt/plot_curve.py#L63).<br>
TinyRoiFile is a stripped version of Christoph Gohlke's [roifile](https://pypi.org/project/roifile/).

## 🤖🧠Labeling data for Machine Learning
RoiEditor allows labeling the deleted ROIs with the reason of their deletion. When sufficient images have been processed you have a nicely labeled dataset to train a network to automatically delete 'bad ROIs'.

## ✨ Workflow
The plot below shows the integrated workflow using [cellpose](https://www.cellpose.org/) and RoiEditor.<br>
<img src=".\assets\RoiEditorWorkflow.svg" alt="cellpose and RoiEditor integrated workflow" width="600"/>
