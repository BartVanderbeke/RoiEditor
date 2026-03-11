import os

import context as Context
from tiny_log import log
from tiny_roi_file import TinyRoiFile
from tiny_roi_manager import TinyRoiManager


class WorkbenchPersistenceMixin:
    def clean_up(self):
        if self.roi_window:
            self.roi_window.hide()
        if self.hist_plot:
            self.hist_plot.hide()
        if self.backup_timer:
            self.backup_timer.stop()
        log("ROIs will be backed up")
        if self.on_backup_rois():
            log("ROIs backed up, safe to close", type="happy")
        else:
            log("No ROIs to be backed up, safe to close", type="happy")
        for k in self.rm.keys():
            self.rm[k].deleteLater()
        self.rm.clear()

    def make_backup(self):
        log("Timed backup triggered")
        self.on_backup_rois()

    def on_save_measurements(self):
        if not self.measurements:
            log("No measurements available", type="warning")
            return False

        full_csv_name = str(self.files["msmts_csv_out"]())
        full_xlsx_name = str(self.files["msmts_xlsx_out"]())
        pc = self.files["msmts_csv_out"]()
        px = self.files["msmts_xlsx_out"]()
        if self._is_writable(full_csv_name) and self._is_writable(full_xlsx_name):
            log(f"Saving measurements to {pc.name}")
            log(f"Saving measurements to {px.name}")
            self.measurements.save_measurements_to_csv(full_name=full_csv_name, subset_name="ALL")
            self.measurements.save_measurements_to_xlsx(full_name=full_xlsx_name, subset_name="ALL")
            return True

        log(f"Cannot save measurements to {pc} or {px} in folder {px.parent}", type="error")
        self.on_fail_to_write(f"{pc},{px}")
        return False

    def _write_rois(self, cell_roi_path, nuke_roi_path):
        nuke_roi_full_name = str(nuke_roi_path)
        nukes_writable = self._is_writable(nuke_roi_full_name)
        if TinyRoiManager.has_rois(self.rm["nuke"]):
            nuke_roi_list = [None] + list(self.rm["nuke"]._name_to_roi.values())
            if nukes_writable:
                log(f"Saving Nuke ROIs to {nuke_roi_path.name}")
                TinyRoiFile.write_parallel(
                    zip_path=nuke_roi_full_name,
                    roi_list=nuke_roi_list,
                    num_threads=Context.gvars["save_rois_num_threads"],
                )
        else:
            log("No Nuke ROIs available to be saved", type="warning")

        cell_roi_full_name = str(cell_roi_path)
        cells_writable = self._is_writable(cell_roi_full_name)
        if cells_writable:
            log(f"Saving Cell ROIs to {cell_roi_path.name}")
            cell_roi_list = [None] + list(self.rm["cell"]._name_to_roi.values())
            TinyRoiFile.write_parallel(
                zip_path=cell_roi_full_name,
                roi_list=cell_roi_list,
                num_threads=Context.gvars["save_rois_num_threads"],
            )

        ret_value = cells_writable and nukes_writable
        if not ret_value:
            log(
                f"Cannot save ROIs to {nuke_roi_path.name} or {cell_roi_path.name} in folder {cell_roi_path.parent}",
                type="error",
            )
            self.on_fail_to_write(f"{nuke_roi_path.name} or {cell_roi_path.name}")

        return ret_value

    def on_backup_rois(self):
        if not TinyRoiManager.has_rois(self.rm["cell"]):
            log("No Cell ROIs available", type="warning")
            return False
        return self._write_rois(self.files["zip_backup"](), self.files["nukezip_backup"]())

    def on_save_rois(self):
        if not TinyRoiManager.has_rois(self.rm["cell"]):
            log("No Cell ROIs available", type="warning")
            return False
        return self._write_rois(self.files["zip_out"](), self.files["nukezip_out"]())

    @staticmethod
    def _is_writable(path):
        try:
            if os.path.exists(path):
                with open(path, "a"):
                    pass
            else:
                dir_path = os.path.dirname(path) or "."
                testfile = os.path.join(dir_path, ".write_test_tmp")
                with open(testfile, "w"):
                    pass
                os.remove(testfile)
            return True
        except (IOError, PermissionError):
            return False
