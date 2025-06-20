"""RoiEditor

Author: Bart Vanderbeke & Elisa
Copyright: © 2025
License: MIT

Parts of the code in this project have been derived from chatGPT suggestions.
When code has been explicitly derived from someone else's code,
I left the (GitHub) url of the original code next to the derived code.

"""
# Stylesheet.py
# chatGPT generated cellpose-like style

overall:str="""
            QWidget {
                background-color: #111111;
                color: white;
                font-size: 13px;
                border: none;
            }

            QGroupBox {
                border: 1px solid #444;
                border-radius: 6px;
                margin-top: 10px;
            }

            QGroupBox:title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                color: #8be9fd;
                font-weight: bold;
            }

            QLabel {
                background: transparent;
                color: #ffffff;
                border: none;
            }

            QLineEdit {
                background-color: #222222;
                color: white;
                border: 1px solid #555;
                padding: 4px;
            }

            QPushButton {
                background-color: #444;
                color: #8be9fd;
                border: 1px solid #555;
                padding: 6px;
                border-radius: 4px;
            }

            QPushButton:default {
                border: 2px solid #0078d7;
            }

            QPushButton:hover {
                background-color: #5e5e5e;
            }

            QPushButton:pressed {
                background-color: #777;
            }

            QCheckBox,QRadioButton {
                color: #bd93f9;
            }

            QDialog {
                background-color: #111;
            }

            QGraphicsView {
                background-color: black;
            }
            QMainWindow {
                background-color: black;
            }
            
            QComboBox, QTableWidget {
                background-color: #3c3c3c;
                border: 1px solid #666;
                border-radius: 4px;
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #444;
                color: white;
                border: 1px solid #666;
            }
            QStatusBar {
                background-color: black;
                border: none
            }
            QFileDialog QTreeView {
                background-color: #1e1e1e;
                color: #cccccc;
                alternate-background-color: #2a2a2a;
                selection-background-color: #4488ff;
                selection-color: black;
            }

            QFileDialog QTreeView::item:selected {
                background-color: #4488ff;
                color: black;
            }

            QFileDialog QLabel {
                color: #aaaaaa;
            }
            QRadioButton {
                color: #cccccc;
                spacing: 6px;
            }

            QRadioButton::indicator {
                width: 14px;
                height: 14px;
                border-radius: 7px;
                border: 1px solid #666666;
                background-color: #2a2a2a;
            }

            QRadioButton::indicator:unchecked {
                background-color: #444444;   /* zacht grijs, subtiel zichtbaar op donkere bg */
                border: 1px solid #666666;
            }

            QRadioButton::indicator:checked {
                background-color: #4488ff;   /* Cellpose-blauw */
                border: 1px solid #4488ff;
            }
            
        """
        
            # QFileDialog {
                # background-color: #111;
            # }