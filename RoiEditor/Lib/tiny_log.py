"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
import inspect
import numpy as np

class classproperty:
    """A decorator that behaves like @property but on the class itself."""

    def __init__(self, fget):
        self.fget = fget
        self.fset = None

    def __get__(self, instance, owner):
        return self.fget(owner)

    def __set__(self, instance, value):
        if self.fset is None:
            raise AttributeError("can't set attribute")
        owner = type(instance) if instance is not None else instance
        if owner is None:
            raise TypeError("Cannot set classproperty without owner class.")
        self.fset(owner, value)

    def setter(self, fset):
        """Define the setter function."""
        self.fset = fset
        return self


            # '30': 'black',
            # '31': 'red',
            # '32': 'green',
            # '33': 'orange',         # yellow/orange
            # '34': 'blue',
            # '35': 'magenta',
            # '36': 'cyan',
            # '37': 'lightgrey',      # grayish white
            # '90': 'gray',
            # '91': 'lightcoral',     # red
            # '92': 'lightgreen',
            # '93': 'khaki',          # bright yellow?
            # '94': 'lightskyblue',
            # '95': 'plum',           # pink
            # '96': 'lightcyan',
            # '97': 'white'

class TinyLog:

    LOG_LVL_NORMAL = 128
    LOG_NEVER=0

    TYPE_TO_COLOR = {
        "info": "\033[97m",     # lightgray
        "warning": "\033[33m",  # orange
        "error": "\033[31m",    # red
        "happy": "\033[92m",    # light green
        "debug": "\033[36m"     # cyan
    }

    TYPE_TO_ICON = {
        "info": "ℹ️",
        "warning": "⚠",
        "error": "❌",
        "happy": "😊",
        "debug": "🐞"
    }

    PRINT_ALWAYS={"error","warning"}

    _only_print_what_has_lower_level_than: np.uint8=LOG_LVL_NORMAL

    @classproperty
    def log_level(cls):
        return cls._only_print_what_has_lower_level_than

    @log_level.setter
    def log_level(cls, value: np.uint8):
        cls._only_print_what_has_lower_level_than = value

    @staticmethod
    def will_print(this_log_level: np.uint8) -> bool:
        return this_log_level < TinyLog._only_print_what_has_lower_level_than


    @staticmethod
    def shorten(text: str, max_len: int) -> str:
        if len(text) <= max_len:
            return text
        if max_len <= 3:
            return '.' * max_len
        return text[:max_len-3] + '...'
    
    @staticmethod
    def log(*args, sep='', end='\n', file=None, flush=False, type: str = "info",log_level: np.uint8 =LOG_LVL_NORMAL-1):
        if log_level <= 0:
            #print(f"Used log_level must be uint8>0")
            log_level=1
        if not (type in TinyLog.PRINT_ALWAYS or TinyLog.will_print(log_level)):
            #print(f"Not printing since print's log level {log_level} >= set log level {TinyLog._only_print_what_has_lower_level_than}")
            return
        
        COLOR = TinyLog.TYPE_TO_COLOR.get(type, "\033[97m")
        RESET = "\033[0m"
        ICON = TinyLog.TYPE_TO_ICON.get(type, "")

        caller_str =""
        caller_name = inspect.stack()[2].function
        if caller_name != '<module>':  # '<module>' --> __main__
            caller_short = TinyLog.shorten(caller_name, 16)

            caller_str = f"[{caller_short}]"

        message = " ".join(map(str, args))  # geen sep!
        message = f"{ICON} {message}"
        if message:
            caller_padded = "" #caller_str.ljust(20)
            full_line = f"{COLOR}{caller_padded}{message}{RESET}"
            print(full_line , sep=sep, end=end, file=file, flush=flush)


def log(*args, sep=' ', end='\n', file=None, flush=False, type: str = "info",log_level: np.uint8 =TinyLog.LOG_LVL_NORMAL-1):
    TinyLog.log(*args, sep=sep, end=end, file=file, flush=flush, type=type ,log_level = log_level)

def set_log_level(level:np.uint8):
    TinyLog.log_level=level
def get_log_level() -> np.uint8:
    return TinyLog.log_level

TinyLog.log("")


