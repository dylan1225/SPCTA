#!/usr/bin/env python3

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout
from src.clock_widget import TimeOnlyWidget, DateOnlyWidget
from src.mallard_svg_widget import MallardSVGWidget

def test_time_display():
    """Test the time display and MALLARD SVG in isolation"""
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("Time Display Test")
    window.resize(800, 400)
    window.setStyleSheet("background-color: #000000;")
    
    central_widget = QWidget()
    layout = QVBoxLayout(central_widget)
    layout.setContentsMargins(20, 20, 20, 20)
    
    date_widget = DateOnlyWidget()
    layout.addWidget(date_widget)
    
    layout.addStretch(1)
    
    time_widget = TimeOnlyWidget()
    layout.addWidget(time_widget)
    
    mallard_widget = MallardSVGWidget()
    layout.addWidget(mallard_widget)
    
    window.setCentralWidget(central_widget)
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    print("Testing time display and MALLARD SVG...")
    print("You should see:")
    print("1. Date at the top (e.g., 'AUG 2')")
    print("2. Time in the center (e.g., '14:30') updating every second")
    print("3. MALLARD SVG at the bottom")
    sys.exit(test_time_display()) 
