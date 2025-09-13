from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
from datetime import datetime

class ClockWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("""
            QLabel {
                color: #00FFA3;
                font-family: 'Lexend Bold';
                font-size: 24px;
                background-color: transparent;
            }
        """)
        
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-family: 'Lexend Regular';
                font-size: 16px;
                background-color: transparent;
            }
        """)
        
        layout.addWidget(self.time_label)
        layout.addWidget(self.date_label)
        
        self.setStyleSheet("background-color: transparent;")
        
    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Update every 1000ms (1 second)
        
        self.update_time()
        
    def update_time(self):
        """Update the displayed time and date"""
        now = datetime.now()
        
        time_str = now.strftime("%H:%M")
        self.time_label.setText(time_str)
        
        date_str = now.strftime("%b %d").upper()
        self.date_label.setText(date_str)

class TimeOnlyWidget(QWidget):
    """Widget that displays only the time"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-family: 'Lexend Bold';
                font-size: 20px;
                background-color: transparent;
            }
        """)
        
        layout.addWidget(self.time_label)
        
        self.setStyleSheet("background-color: transparent;")
        
    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Update every 1000ms (1 second)
        
        self.update_time()
        
    def update_time(self):
        """Update the displayed time"""
        now = datetime.now()
        
        time_str = now.strftime("%H:%M")
        self.time_label.setText(time_str)

class DateOnlyWidget(QWidget):
    """Widget that displays only the date"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-family: 'Lexend Bold';
                font-size: 20px;
                background-color: transparent;
            }
        """)
        
        layout.addWidget(self.date_label)
        
        self.setStyleSheet("background-color: transparent;")
        
    def setup_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_date)
        self.timer.start(60000)  # Update every 60000ms (1 minute)
        
        self.update_date()
        
    def update_date(self):
        """Update the displayed date"""
        now = datetime.now()
        
        date_str = now.strftime("%b %d").upper()
        self.date_label.setText(date_str) 