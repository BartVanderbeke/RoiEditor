""" script that identifies all imports and can install all uninstalled dependencies
"""
import os
import sys
import subprocess

module_to_pip = {
    'pathlib': None,         # standaardmodule
    'PIL': 'Pillow',
    're': None,              # standaardmodule
    'sys': None,             # standaardmodule
    'concurrent': None,      # standaardmodule
    'json': None,            # standaardmodule
    'tifffile': 'tifffile',
    'math': None,            # standaardmodule
    'threading': None,       # standaardmodule
    'matplotlib': 'matplotlib',
    'random': None,          # standaardmodule
    'skimage': 'scikit-image',
    'os': None,              # standaardmodule
    'numpy': 'numpy',
    'numba': 'numba',
    'struct': None,          # standaardmodule
    'xml': None,             # standaardmodule
    'typing': None,          # standaardmodule (vanaf Python 3.5)
    'datetime': None,        # standaardmodule
    'csv': None,             # standaardmodule
    'cv2': 'opencv-python',
    'pyqtgraph': 'pyqtgraph',
    'zipfile': None,         # standaardmodule
    'PyQt6': 'PyQt6',
    'xlsxwriter': 'xlsxwriter',
    'inspect': None          # standaardmodule
}


def find_imports_in_file(filepath):
    imports = set()
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith("import "):
                line = line[len("import "):]
                parts = line.split(',')
                for part in parts:
                    mod = part.strip().split()[0]  # Negeer "as x"
                    imports.add(mod.split('.')[0])
            elif line.startswith("from "):
                parts = line.split()
                if len(parts) >= 2:
                    imports.add(parts[1].split('.')[0])
    return imports


def is_builtin_module(modname):
    try:
        __import__(modname)
        return True
    except ImportError:
        return False

def main(target_dir):
    all_imports = set()
    all_modules_in_dir = set()
    script_path = os.path.abspath(__file__)

    #for root, _, files in os.walk(target_dir):
    for file in os.listdir(target_dir):
        if file.endswith('.py'):
            path = os.path.abspath(os.path.join(target_dir, file))
            if path == script_path:
                continue  # sla dit script zelf over
            all_imports.update(find_imports_in_file(path))
            basename = os.path.splitext(os.path.basename(file))[0]
            all_modules_in_dir.update([basename])

    print("Gevonden imports:", all_imports)
    print("Gevonden modules in folder",all_modules_in_dir)
    deps = all_imports - all_modules_in_dir
    print("Externe afhankelijkheden", deps)

    missing = [m for m in deps if not is_builtin_module(m)]
    if not missing:
        print("Alle modules zijn al geïnstalleerd.")
        return

    print("Niet gevonden modules, probeer te installeren:", missing)

    for mod in missing:
        try:
            pip_name = module_to_pip.get(mod, None)
            if pip_name:
                print(f"probeer te installeren: {mod} met pip: {pip_name}")
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', module_to_pip[mod]])
            else:
                print(f"mm, raar, {mod}  is een standaardmodule")
        except subprocess.CalledProcessError:
            print(f"FOUT bij installeren van module: {mod}")

if __name__ == '__main__':
    main('./lib/')
