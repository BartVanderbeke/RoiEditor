import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'Lib')))
def main():
    from RoiEditor.GuiLauncher import launch
    launch()

if __name__ == "__main__":
    main()