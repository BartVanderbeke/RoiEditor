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
- The scaling of the image μm/pixel can be read from the original tif(f) file or set manually.
- Area & Feret measurements are computed for all ROIs.
- The stats for each measurement are shown in a histogram window
- The user can select the edge of the ROI-cloud or the outliers for each measurement for deletion.
- An outlier for a measurement is a value deviating more than 1.5 * IQR from the median.
- When the image overlay is activated, a color range from green to red indicates the distance from the median for the selected measurement for each individual ROI.
- The measurements and statistics can be written to both and .xlsx and a .csv file.
- The ROI data is backed up every 15 minutes.
