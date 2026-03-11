import numpy as np

from PolygonEditor import PolygonEditor
from Roi import Roi
from RoiSelect import select_outer_rois_vdb5
from TinyLog import log
from TinyRoiManager import TinyRoiManager
from HistogramFrame import HistogramFrame as QHF


class WorkbenchActionsMixin:
    def on_delete_key_pressed(self, argument):
        for trm in self.rm.values():
            trm.delete_selected()
        self.on_any_change("DELETE key pressed")

    def on_escape_key_pressed(self, argument):
        for trm in self.rm.values():
            trm.unselect_all()
        self.on_any_change("ESCAPE key pressed")

    def on_f1_key_pressed(self, argument):
        log("F1 key pressed: No function: use right-click and drag for rectangle select", type="warning")

    def on_tagged_delete(self, tag):
        for trm in self.rm.values():
            trm.delete_selected(tag)
        self.on_any_change(f"Function key pressed for tagged delete: {tag}")

    def on_add_nucleus_here(self, roi: Roi, position: tuple[int, int]):
        if roi and roi.name[0] == "N":
            if roi.state == Roi.ROI_STATE_DELETED:
                log(f"Restoring a deleted nucleus {roi.name}", type="warning")
            else:
                log(f"An existing nucleus {roi.name} was clicked", type="info")
            roi.state = Roi.ROI_STATE_ACTIVE
            roi.tags = {x for x in roi.tags if not x.startswith("DELETED")}
            editor = PolygonEditor(self.background_qimage, window_width=150, roi=roi, parent=self.roi_window)
            roi = editor.run()
            self.on_any_change()
            return
        assert not roi or roi.name[0] == "L"
        if self.rm["nuke"] is None:
            log("No nucleus ROI manager", type="error")
            return
        new_nucleus_name = self.rm["nuke"].first_free_name()

        nuke_roi: Roi = Roi(
            xpoints=np.array([position[0]], dtype=float),
            ypoints=np.array([position[1]], dtype=float),
            name=new_nucleus_name,
            bounds=(position[1], position[0], position[1], position[0]),
            center=position,
            n=1,
            area=0,
            state=Roi.ROI_STATE_ACTIVE,
            tags=set(),
            parent=roi,
        )
        self.rm["nuke"].add(nuke_roi)
        if roi:
            log(f"Creating new nucleus {new_nucleus_name} as child of {roi.name}", type="info")
            roi.children.append(nuke_roi)
            if roi.state == Roi.ROI_STATE_DELETED:
                nuke_roi.state = Roi.ROI_STATE_DELETED
                nuke_roi.tags.add("DELETED.WITH_PARENT")
        else:
            log(f"Creating new nucleus {new_nucleus_name} on background", type="info")
        self.on_any_change(f"New nucleus {new_nucleus_name} added to parent {roi.name}", rebuild=True)

    def on_select_outliers(self):
        if not self.measurements:
            log("No measurements available (yet)", type="warning")
            return
        if not QHF.is_histogram_populated(self.hist_plot):
            log("Histogram/selected measurement not (yet) available", type="warning")
            return

        selected_measurement = self.hist_plot.selected_measurement
        outliers = self.measurements.stats["ACTIVE"][selected_measurement]["outliers"]

        self.rm["cell"].select(
            rois_or_names=outliers,
            reason_of_selection=selected_measurement + ".outlier",
            additive=True,
        )
        self.on_any_change(f"outliers selected for: {selected_measurement}")

    def on_select_outer(self):
        if not TinyRoiManager.has_rois(self.rm["cell"]) or self.images["cell_label"] is None:
            log("No ROIs or no label image", type="warning")
        select_outer_rois_vdb5(rm=self.rm["cell"], label_image=self.images["cell_label"])
        self.on_any_change("outer edge selected")

