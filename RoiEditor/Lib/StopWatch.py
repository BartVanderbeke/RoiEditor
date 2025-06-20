"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
import time
from .TinyLog import log
class StopWatch:

    start_time = None

    @staticmethod
    def start(message=""):
        if StopWatch.start_time is not None:
            log("StopWatch already running", type="warning")
            return

        StopWatch.start_time = time.perf_counter()
        if message:
            log(message)
            
    @staticmethod
    def stop(message=""):

        if StopWatch.start_time is None:
            log("StopWatch has not been started", type="warning")
            return
        end_time = time.perf_counter()
        duration = end_time - StopWatch.start_time
        milliseconds = int(duration * 1000.0)
        if message:
            log(f"{message} finished in: {milliseconds} milliseconds")
        StopWatch.start_time = None  # reset
