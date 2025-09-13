from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal

class BootSequence(QWidget):
    boot_complete = pyqtSignal()