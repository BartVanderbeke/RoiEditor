"""RoiEditor

Author: Bart Vanderbeke
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
import numpy as np

from typing import Union
from typing import Callable,Any
from PyQt6.QtGui import QBrush

from .Roi import Roi

from .TinyLog import log
from .TinyColor import map_values_to_qbrush
from .Feret import feret_msmts,feret_quantities,feret_units,feret_scalers

from .MsmtToFile import attach_extension_methods

from PyQt6.QtCore import QObject
class RoiMeasurements(QObject):
    """
        calculates the measurement values, calculates statistics
        saves the numbers to a .csv file
    """
    measurement_names_wo_area = feret_msmts

    measurement_names = ["Area"] + feret_msmts
    measurement_quantities = ["area"] + feret_quantities
    measurement_units= ["px"] + feret_units
    measurement_scalers = [1.0*1.0] + feret_scalers

    default_unit_and_scale = {"length": {"scaler": 1.0, "unit": "px"},"area": {"scaler": 1.0*1.0, "unit": "px"}}

    def __init__(self, rm, delayed_compute=False,num_bins=20,unit_and_scale: dict[str, Union[str, float]]=None, parent=None):
        super().__init__(parent)
        self.num_bins = num_bins
        self.rm = rm
        # data may be modified e.g. by applying a unit
        self.data: dict[str, dict[str, np.ndarray]] ={} # subset  --> {measurement_name -> np.array()}
        # orig remains untouched: always in pixels
        self.orig: dict[str, dict[str, np.ndarray]] ={} # subset  --> {measurement_name -> np.array()}
        self.distance: dict[str, dict[str, np.ndarray]] ={} # subset  --> {measurement_name -> np.array()}
        #self.all={"data": self.data, "distance" : self.distance}
        self.stats: dict[str, dict[str, dict[str,Any]]] = {} # subset  --> {measurement_name -> {stat  --> value}}
        self.idx: dict[str,dict[str,Roi]] ={}
        from PyQt6.QtGui import QBrush
        self.qbrush: dict[str, dict[str, QBrush]] = {} # subset  --> {measurement_name -> QBrush}
        self.subset_filter: dict[str, Callable[[Roi], bool]] = {"ALL": (lambda roi: True)}
        self.unit_and_scale = unit_and_scale if unit_and_scale else self.default_unit_and_scale
        self.units_and_scalers: dict[str, Union[str, float]] = {}
        for name, quantity,scaler,unit in zip(self.measurement_names,
                                              self.measurement_quantities,
                                              self.measurement_scalers,
                                              self.measurement_units):
            if quantity in self.unit_and_scale:
                self.units_and_scalers[name]=self.unit_and_scale[quantity]
            else:
                self.units_and_scalers[name]= {"scaler": scaler, "unit": unit}

        attach_extension_methods(self)

        self._subset_all_calculated=False
        if delayed_compute:
            return
        self.compute_stats_subset(subset_name="ALL")

    @classmethod
    def is_valid(cls,msmts: "RoiMeasurements"):
        return msmts is not None and msmts.data is not None and msmts.stats is not None

    @property
    def subset_all_calculated(self):
        return self._subset_all_calculated

    def _custom_median(self, sorted_values, start, end):
        count = end - start
        mid = start + count // 2 if count>0 else 0
        if count % 2 == 1:
            return sorted_values[mid]
        else:
            mid_minus_1 = mid-1 if mid > 0 else 0
            return 0.5 * (sorted_values[mid_minus_1] + sorted_values[mid])

    def _compute_stats(self, subset_name):
        if not subset_name in self.stats:
            self.stats[subset_name]={}
        rois= self.data[subset_name]["Roi"]
        for msmt, values in self.data[subset_name].items():
            is_a_msmt = msmt != "Roi"
            if is_a_msmt and len(values)>0:
                sorted_vals = np.sort(values)
                N = len(values)
                med = self._custom_median(sorted_vals, 0, N)
                q1 = self._custom_median(sorted_vals, 0, N // 2)
                q3 = self._custom_median(sorted_vals, (N + 1) // 2, N)
                mad = self._custom_median(np.sort(np.abs(values - med)), 0, N)
                hist, bin_edges = np.histogram(a=values, bins=self.num_bins,range=self.minmax[msmt])
                min_val = np.min(values)
                max_val = np.max(values)
                iqr =  q3 - q1
                upper_limit = med + 1.5 * iqr
                lower_limit = med - 1.5 * iqr
                outlier_mask = (values < lower_limit) | (values > upper_limit)
                outliers = rois[outlier_mask]
                num_outliers=len(outliers)
                mean = np.mean(values)
                stdev = np.std(values, ddof=1) if N>1 else 0
                unit=self.units_and_scalers[msmt]["unit"]
                
            else:
                N = 0
                med = 0
                q1 = 0
                q3 = 0
                mad = 0
                hist, bin_edges = [], []
                min_val = 0
                max_val = 0
                num_outliers = 0
                outliers = np.array([], dtype=Roi)
                mean = 0
                stdev = 0
                unit= self.units_and_scalers[msmt]["unit"] if is_a_msmt else ""
            result= {
                "mean": mean,
                "stdev": stdev,
                "median": med,
                "q1": q1,
                "q3": q3,
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
            log("No need to define subset ALL")


    def compute_stats_subset(self, subset_name: str):

        this_filter = self.subset_filter.get(subset_name, None)
        measurements = self.rm.get_measurements_by_filter(this_filter)
        if not measurements or any(len(v) == 0 for v in measurements.values()):
            log(f"Subset '{subset_name}' returned no measurements.")
        self.data[subset_name] = {}
        self.orig[subset_name]=measurements
        # apply the scaler "unit/px": px * unit/px = unit
        for msmt in self.measurement_names:
            magic_scaler = self.units_and_scalers[msmt]["scaler"]
            self.data[subset_name][msmt]=measurements[msmt] * magic_scaler
        self.data[subset_name]["Roi"]=measurements["Roi"]
        
        if subset_name=="ALL":
            self.idx[subset_name]= {roi : idx for idx,roi in enumerate(self.data[subset_name]["Roi"])}
            self.minmax={ msmt : (np.min(self.data["ALL"][msmt]),np.max(self.data["ALL"][msmt])) for msmt in self.measurement_names}
            self._subset_all_calculated=True
            length = len(self.data[subset_name]["Area"])
            self.qbrush[subset_name]= {}
            self.distance[subset_name] = {}
            self._compute_stats(subset_name)
            for msmt in self.measurement_names:
                self.qbrush[subset_name][msmt] = np.array([QBrush()] * length, dtype=object)
                range = 1.5 * (self.stats[subset_name][msmt]["q3"]-self.stats[subset_name][msmt]["q1"])
                self.distance[subset_name][msmt] = np.clip(np.abs(self.data[subset_name][msmt] - self.stats[subset_name][msmt]["median"]),0.0,range)
                vmin= np.min(self.distance[subset_name][msmt])
                vmax = np.max(self.distance[subset_name][msmt])
                map_values_to_qbrush(values=self.distance[subset_name][msmt],
                                      qbrush=self.qbrush[subset_name][msmt],
                                      vmin=vmin,
                                      vmax=vmax)
            

        else:
            self._compute_stats(subset_name)

