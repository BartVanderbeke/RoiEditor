from pathlib import Path
import os

from crumbs import normalize_path
from tiny_log import log


def get_timestamp_string():
    import datetime
    """Return current time as a string in yymmddHHMMSS format."""
    return datetime.datetime.now().strftime("%y%m%d%H%M%S")


class WorkbenchPathsMixin:
    def _init_paths(self, selected_files: dict[str, str | None]):
        self.files = {
            k: (lambda v=v: Path() if v is None else Path(v))
            for k, v in selected_files.items()
        }

        orgpath = Path(self.files["org"]())
        self.base_name = orgpath.stem
        self.working_dir = normalize_path(str(orgpath.parent))

        self.files["zip_out"] = lambda: Path(f"{self.working_dir}{self.base_name}_roiset.zip")
        self.files["nukezip_out"] = lambda: Path(f"{self.working_dir}{self.base_name}_nuke_roiset.zip")
        self.files["zip_backup"] = lambda: Path(
            f"{self.working_dir}/RoiBackup/{get_timestamp_string()}_{self.base_name}_roiset.zip"
        )
        self.files["nukezip_backup"] = lambda: Path(
            f"{self.working_dir}/RoiBackup/{get_timestamp_string()}_{self.base_name}_nuke_roiset.zip"
        )
        self.files["msmts_csv_out"] = lambda: Path(f"{self.working_dir}{self.base_name}_msmts.csv")
        self.files["msmts_xlsx_out"] = lambda: Path(f"{self.working_dir}{self.base_name}_msmts.xlsx")

        roi_dir = self.files["zip_backup"]().parent
        os.makedirs(roi_dir, exist_ok=True)
        log(f"ROI Backup folder: {roi_dir}", type="info")

