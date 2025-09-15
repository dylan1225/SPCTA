#!/usr/bin/env python3

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QFrame, QLabel
from PyQt5.QtCore import Qt
from src.clock_widget import TimeOnlyWidget, DateOnlyWidget
from src.mallard_svg_widget import MallardSVGWidget

def test_fullscreen_layout():
    """Test the fullscreen layout to ensure time and MALLARD are visible"""
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("Fullscreen Layout Test")
    window.showFullScreen()
    window.setStyleSheet("background-color: #000000;")
    
    central_widget = QWidget()
    main_layout = QVBoxLayout(central_widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)
    
    top_container = QFrame()
    top_layout = QVBoxLayout(top_container)
    top_layout.setContentsMargins(0, 0, 0, 0)
    
    navbar_label = QLabel("Navigation Bar")
    navbar_label.setStyleSheet("color: #00FFA3; font-size: 16px; padding: 10px;")
    navbar_label.setAlignment(Qt.AlignCenter)
    top_layout.addWidget(navbar_label)
    
    date_widget = DateOnlyWidget()
    date_widget.setFixedHeight(25)
    top_layout.addWidget(date_widget)
    
    main_layout.addWidget(top_container)
    
    content_label = QLabel("Content Area\n(YouTube, Maps, etc.)")
    content_label.setStyleSheet("color: #666; font-size: 24px; padding: 50px;")
    content_label.setAlignment(Qt.AlignCenter)
    main_layout.addWidget(content_label, 1)  # Stretch
    
    bottom_container = QFrame()
    bottom_layout = QHBoxLayout(bottom_container)
    bottom_layout.setContentsMargins(10, 5, 10, 10)
    
    version_label = QLabel("Puddle Ver. 0.1 Alpha")
    version_label.setStyleSheet("color: #888; font-size: 12px;")
    bottom_layout.addWidget(version_label, 1)
    
    center_container = QFrame()
    center_layout = QVBoxLayout(center_container)
    center_layout.setContentsMargins(0, 0, 0, 0)
    center_layout.setSpacing(8)
    
    time_widget = TimeOnlyWidget()
    time_widget.setFixedHeight(35)
    center_layout.addWidget(time_widget)
    
    mallard_widget = MallardSVGWidget()
    center_layout.addWidget(mallard_widget)
    
    bottom_layout.addWidget(center_container)
    bottom_layout.addWidget(QWidget(), 1)  # Spacer
    
    main_layout.addWidget(bottom_container, 0)  # Fixed size
    
    window.setCentralWidget(central_widget)
    window.show()
    
    print("Fullscreen layout test running...")
    print("Press F11 to toggle fullscreen, ESC to exit")
    
    return app.exec()

if __name__ == "__main__":
    print("Testing fullscreen layout...")
    print("You should see:")
    print("1. Navigation bar at top")
    print("2. Date below navbar")
    print("3. Content area in middle")
    print("4. Time and MALLARD SVG at bottom")
    print("5. All elements should be visible in fullscreen")
    sys.exit(test_fullscreen_layout()) 
