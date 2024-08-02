import nuke
import os
from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2 import QtUiTools
from PySide2.QtWidgets import *

__author__ = "Abraham Gonzalez Castillo Pena"
__title__ = "Arnold AOV's Comp"
__version__ = '1.0.0'

try:
    parent = QApplication.activeWindow()
except:
    print("Error initializing window parent")

class AOVs_Creator_Window(QMainWindow):
    """QMainWindow which can be open as a standalone tool"""

    def __init__(self, parent=parent):
        """Load UI from file"""
        super(self.__class__, self).__init__(parent)

        # LOAD UI
        self.current_dir = os.path.dirname(os.path.realpath(__file__))
        ui_main = '{}/UI/UI_arnold_aov_comp.ui'.format(self.current_dir)
        ui_loader = QtUiTools.QUiLoader().load(ui_main)
        ui_loader.setParent(self)
        # ui_file = QFile(ui_main)
        # ui_file.open(QFile.ReadOnly)
        # self.ui = ui_loader.load(ui_file)
        # ui_file.close()
        self.show()

    def close_window(self):
        self.close()

def main():
    print('test')
    AOVs_Creator_Window()