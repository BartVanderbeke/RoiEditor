"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
import os
def normalize_path(path: str) -> str:
    if path.startswith("//") or path.startswith("\\\\") :
        prefix = "//"
        rest = path[2:]
    elif path.startswith("/") or path.startswith("\\"):
        prefix = "/"
        rest = path[1:]
    else:
        prefix = ""
        rest = path

    while '\\' in rest:
        rest = rest.replace('\\', '/')

    while '//' in rest:
        rest = rest.replace('//', '/')

    result = prefix+rest

    if os.path.isdir(result) and result[-1] not in {"/","\\"}:
        result=result+"/"

    return result

def format_qobject_tree(obj , level: int = 0) -> str:
    indent = ' ' * (3 * level)
    class_name =obj.__class__.__name__
    name = obj.objectName() or class_name
    lines = []
    if not class_name.lower().startswith("q"):
        lines = [f"{indent}{name}"]
    for child in obj.children():
        lines.append(format_qobject_tree(child, level + 1))
    return '\n'.join(lines)


def format_float(value: float,digits =5) -> str:
    from math import log10, floor, pow
    if abs(value) < pow(10,digits):
        # 'digits' significant digits
        digits = (digits - 1) - floor(log10(abs(value))) if value != 0 else (digits - 1)
        digits = max(digits, 0)
        return f"{value:.{digits}f}"
    else:
        # xxxxx.x (round to 0.1, no extra zeros)
        return f"{round(value, 1):.1f}"
