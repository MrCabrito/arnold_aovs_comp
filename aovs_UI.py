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
        self.widget = QtUiTools.QUiLoader().load(ui_main)
        self.widget.setParent(self)
        self.setWindowTitle('{0} v{1}'.format(__title__, __version__))
        self.resize(305,56)
        self.activateWindow
        self.widget.btn_create.clicked.connect(self.create_template)
        self.show()

    def create_template(self):
        """
         Build a template for the selected read nodes
        """
        from .utilities.btn_actions import run_create
        template_type = self.widget.cBox_template.currentText()
        new_group = self.widget.chBox_new_group.checkState()
        run_create(template_type, new_group)

    def close_window(self):
        self.close()

def main():
    AOVs_Creator_Window()