"""
Splash Screen for Meeting Transcriber

This module provides a splash screen for the Meeting Transcriber application.

Author: Gianpaolo Albanese
Date: 05-10-2024
"""

from PyQt5.QtWidgets import QSplashScreen
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer
import os

class SplashScreen(QSplashScreen):
    def __init__(self):
        # Try to load splash screen image from assets directory
        splash_image_path = os.path.join('assets', 'SplashScreen.png')
        
        if os.path.exists(splash_image_path):
            # Use the provided splash screen image
            pixmap = QPixmap(splash_image_path)
        else:
            # Create a basic splash screen with text
            pixmap = QPixmap(400, 200)
            pixmap.fill(Qt.white)
            
        super(SplashScreen, self).__init__(pixmap)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setEnabled(False)
        
        # Add text to the splash screen if we're using the default
        if not os.path.exists(splash_image_path):
            self.showMessage("Loading Meeting Transcriber...", 
                            Qt.AlignCenter | Qt.AlignBottom, 
                            Qt.black)
        
    def show_and_finish(self, main_window, duration=2000):
        """Show the splash screen and close it after duration milliseconds"""
        self.show()
        QTimer.singleShot(duration, lambda: self.finish(main_window))
