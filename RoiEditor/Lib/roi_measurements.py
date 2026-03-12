"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
import numpy as np
from typing import Callable,Any
from numba import njit

from roi import Roi
from tiny_roi_manager import TinyRoiManager
from tiny_log import log
from msmt_to_file import attach_extension_methods
from average_color import distance_array
class Data2Measurement:
    
    convertor: dict[str, Callable[[Any], Any]] = { msmt : (lambda x: x) for msmt in TinyRoiManager.measurement_names()}
    convertor["Color"] = distance_array

class IqrMargin:
        margin : dict[str, float] = { msmt : 1.5 for msmt in TinyRoiManager.measurement_names()}
        margin["Color"] = 3.0

from PyQt6.QtCore import QObject

@njit(cache=True, inline="always")
def _custom_median(sorted_values, start, end):
    count = end - start
    mid = start + count // 2 if count>0 else 0
    if count % 2 == 1:
        return sorted_values[mid]
    else:
        mid_minus_1 = mid-1 if mid > 0 else 0
        return 0.5 * (sorted_values[mid_minus_1] + sorted_values[mid])


@njit(cache=True)
def _compute_stats_core(values, iqr_margin):
    sorted_vals = np.sort(values)
    n = len(values)
    med = _custom_median(sorted_vals, 0, n)
    q1 = _custom_median(sorted_vals, 0, n // 2)
    q3 = _custom_median(sorted_vals, (n + 1) // 2, n)
    mad = _custom_median(np.sort(np.abs(values - med)), 0, n)
    min_val = np.min(values)
    max_val = np.max(values)
    iqr = q3 - q1
    upper_limit = q3 + iqr_margin * iqr
    lower_limit = q1 - iqr_margin * iqr
    outlier_mask = (values < lower_limit) | (values > upper_limit)
    num_outliers = np.sum(outlier_mask)
    mean = np.mean(values)
    return n, med, q1, q3, mad, min_val, max_val, iqr, upper_limit, lower_limit, outlier_mask, num_outliers, mean


class RoiMeasurements(QObject):
    """
        calculates the measurement values, calculates statistics
        saves the numbers to a .csv file
    """


    default_unit_and_scale = {"length": {"scaler": 1.0, "unit": "px"},"area": {"scaler": 1.0*1.0, "unit": "px"}}

    def __init__(self,
                 cell_rm: TinyRoiManager,
                 nuke_rm: TinyRoiManager | None =None,
                 num_bins: int=20,
                 unit_and_scale: dict[str, Any]=default_unit_and_scale,
                 parent=None):
        super().__init__(parent)

        self.nuke_rm=nuke_rm
        self.measurement_names = TinyRoiManager.measurement_names()
        self.measurement_info = TinyRoiManager.measurement_info()

        self.num_bins = num_bins
        self.rm = cell_rm
        # data may be modified e.g. by applying a unit/scaler
        self.data: dict[str, dict[str, np.ndarray]] ={} # subset  --> {measurement_name -> np.array()}
        # orig remains untouched: always in pixels, necessary when saving to file
        self.orig: dict[str, dict[str, np.ndarray]] ={} # subset  --> {measurement_name -> np.array()}
        self.minmax: dict[str, dict[str, tuple[float,float]]] ={} # subset  --> {measurement_name -> (min,max)}

        self.stats: dict[str, dict[str, dict[str,Any]]] = {} # subset  --> {measurement_name -> {stat  --> value}}
        #from PyQt6.QtGui import QBrush
        #self.qbrush: dict[str, dict[str, QBrush]] = {} # subset  --> {measurement_name -> QBrush}
        self.subset_filter: dict[str, Callable[[Roi], bool]] = {"ALL": (lambda roi: True)}
        self.unit_and_scale = unit_and_scale
        self.units_and_scalers: dict[str, Any] = {}
        # overrule the default unit_and_scale if needed
        for name,info in  self.measurement_info.items():
            iq =info["quantity"]
            if iq in self.unit_and_scale:
                self.units_and_scalers[name]=self.unit_and_scale[iq]
            else:
                self.units_and_scalers[name]= {"scaler": info["scaler"], "unit": info["unit"]}

        self.normalized_distance: dict[str, dict[str, np.ndarray]] = {} # subset  --> {measurement_name -> np.array()}

        attach_extension_methods(self)

    def _compute_stats(self, subset_name):
        if not subset_name in self.stats:
            self.stats[subset_name]={}
        rois= self.data[subset_name]["Roi"]
        filtered = self.data[subset_name].copy()
        filtered.pop("Roi", None)
        #self.stats[subset_name]["Roi"] = dict()
        to_remove = [k for k, v in filtered.items() if len(v)==0]
        for msmt in to_remove:
            result= {
                "mean": 0,
                "stdev": 0,
                "median": 0,
                "q1": 0,
                "q3": 0,
                "iqr": 0,
                "mad": 0,
                "N": 0,
                "min": 0,
                "max": 0,
                "hist": list() ,
                "bin_edges": list(),
                "num_outliers": 0,
                "outliers": np.array([], dtype=Roi),
                "unit" : self.units_and_scalers[msmt]["unit"]
            }
            self.stats[subset_name][msmt] = result
            filtered.pop(msmt)

        for msmt, values in filtered.items():
            # dit naar njit
            N, med, q1, q3, mad, min_val, max_val, iqr, upper_limit, lower_limit, outlier_mask, num_outliers, mean = _compute_stats_core(
                values,
                IqrMargin.margin[msmt],
            )
            # einde njit
            outliers = rois[outlier_mask]
            stdev = np.std(values, ddof=1) if N>1 else 0
            hist, bin_edges = np.histogram(a=values, bins=self.num_bins,range=self.minmax["ALL"][msmt])            
            unit=self.units_and_scalers[msmt]["unit"]
            result= {
                "mean": mean,
                "stdev": stdev,
                "median": med,
                "q1": q1,
                "q3": q3,
                "iqr": iqr,
                "mad": mad,
                "N": N,
                "min": min_val,
                "max": max_val,
                "hist": hist ,
                "bin_edges": bin_edges,
                "num_outliers": num_outliers,
                "outliers": outliers,
                "unit" : unit
            }
            self.stats[subset_name][msmt] = result

    def define_subset(self, subset_name: str, filter: Callable[[Roi], bool]):
        if subset_name and subset_name != "ALL":
            self.subset_filter[subset_name] = filter
        else:
            log("No need to define subset ALL",type="warning", log_level=1000)


    def compute_stats_subset(self, subset_name: str):

        this_filter = self.subset_filter.get(subset_name, None)
        measurements = self.rm.get_measurements_by_filter(this_filter)
        self.data[subset_name] = {}
        self.orig[subset_name]=measurements # do not discard, needed when saving to file        
        self.minmax[subset_name]= { msmt : (0,0) for msmt in self.measurement_names}
        self.normalized_distance[subset_name]={}

        empty_measurements = [v.size for v in measurements.values() if v.size==0]
        if not measurements or len(empty_measurements)>0:
            log(f"Subset '{subset_name}' returned no measurements.", type="info", log_level=1000)


        # apply the scaler "unit/px": px * unit/px = unit
        # and calculate a derived measurement
        for msmt_name in self.measurement_names:
            value = measurements[msmt_name]
            value = value * self.units_and_scalers[msmt_name]["scaler"]
            value = Data2Measurement.convertor[msmt_name](value)
            self.data[subset_name][msmt_name]=value

        self.data[subset_name]["Roi"]=measurements["Roi"]

        log(f"Subset '{subset_name}' has {len(self.data[subset_name]['Roi'])} ROIs.", type="info", log_level=1000)
        if len(self.data[subset_name]['Roi'])>0:
            self.minmax[subset_name]={ msmt : (np.min(self.data[subset_name][msmt]),np.max(self.data[subset_name][msmt])) for msmt in self.measurement_names}

        self._compute_stats(subset_name)
        
        for msmt_name in self.measurement_names:
            data = self.data[subset_name][msmt_name]
            stats = self.stats[subset_name][msmt_name]

            iqr = stats["iqr"]
            max_range = IqrMargin.margin[msmt_name] * iqr
            dist = np.clip(np.abs(data - stats["median"]), 0.0, max_range)

            if dist.size == 0 or np.all(dist == 0):
                log(f"Values for measurement {msmt_name} missing or all zeros", type="info", log_level=1000)
                vmin, vmax = 0.0, 0.0
            else:
                vmin, vmax = dist.min(), dist.max()
            vrange = vmax - vmin   if vmax > vmin else 1.0

            normalized_dist = (dist - vmin) / vrange

            self.normalized_distance[subset_name][msmt_name] = normalized_dist
