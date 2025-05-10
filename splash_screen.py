"""
Splash screen implementation for the Meeting Transcriber application.

This module provides a splash screen that displays when the application starts.

Author: Gianpaolo Albanese
E-Mail: albaneg@yahoo.com
Work Email: gianpaoa@amazon.com
Date: 05-09-2024
Version: 1.0
Assisted by: Amazon Q for VS Code
"""

import os
import sys
from PyQt5.QtWidgets import QSplashScreen, QApplication
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
from PyQt5.QtCore import Qt, QTimer

class SplashScreen(QSplashScreen):
    def __init__(self):
        """Initialize the splash screen with the application icon."""
        # Find the icon path
        icon_path = self._get_icon_path()
        
        if icon_path and os.path.exists(icon_path):
            # Create a larger pixmap for the splash screen (4x the size of the icon)
            pixmap = QPixmap(512, 512)  # 2x the width and height = 4x the area
            pixmap.fill(QColor(0, 120, 212))  # Blue background to match the icon
            
            # Load the icon
            icon_pixmap = QPixmap(icon_path)
            
            # Create a painter to draw on the pixmap
            painter = QPainter(pixmap)
            
            # Draw the icon in the center at 4x the size
            scaled_icon = icon_pixmap.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            x = (pixmap.width() - scaled_icon.width()) // 2
            y = (pixmap.height() - scaled_icon.height()) // 2 - 40  # Move up a bit for text
            painter.drawPixmap(x, y, scaled_icon)
            
            # Add text at the bottom
            font = QFont("Arial", 16)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(Qt.white)
            text = "Meeting Transcriber V1"
            text_width = painter.fontMetrics().horizontalAdvance(text)
            painter.drawText((pixmap.width() - text_width) // 2, y + scaled_icon.height() + 40, text)
            
            # Add author text
            font = QFont("Arial", 10)
            painter.setFont(font)
            author_text = "by Gianpaolo Albanese"
            author_width = painter.fontMetrics().horizontalAdvance(author_text)
            painter.drawText((pixmap.width() - author_width) // 2, y + scaled_icon.height() + 70, author_text)
            
            # End painting
            painter.end()
        else:
            # Create a default splash screen if icon is not found
            pixmap = QPixmap(512, 512)
            pixmap.fill(QColor(0, 120, 212))  # Blue background
            
            # Create a painter to draw on the pixmap
            painter = QPainter(pixmap)
            
            # Add text
            font = QFont("Arial", 24)
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(Qt.white)
            text = "Meeting Transcriber V1"
            text_width = painter.fontMetrics().horizontalAdvance(text)
            painter.drawText((pixmap.width() - text_width) // 2, pixmap.height() // 2, text)
            
            # Add author text
            font = QFont("Arial", 14)
            painter.setFont(font)
            author_text = "by Gianpaolo Albanese"
            author_width = painter.fontMetrics().horizontalAdvance(author_text)
            painter.drawText((pixmap.width() - author_width) // 2, pixmap.height() // 2 + 40, author_text)
            
            # End painting
            painter.end()
        
        # Initialize the splash screen with the pixmap
        super().__init__(pixmap)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setMask(pixmap.mask())
    
    def _get_icon_path(self):
        """Get the path to the application icon."""
        # Check for icon in the current directory
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            return icon_path
            
        # If running as a PyInstaller bundle
        if getattr(sys, 'frozen', False):
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_path, "icon.ico")
            if os.path.exists(icon_path):
                return icon_path
        
        return None

def show_splash(app, duration=3000):
    """
    Show a splash screen for the specified duration.
    
    Args:
        app: The QApplication instance
        duration: Time in milliseconds to show the splash screen
        
    Returns:
        The splash screen instance
    """
    splash = SplashScreen()
    splash.show()
    app.processEvents()
    
    # Close the splash screen after the specified duration
    QTimer.singleShot(duration, splash.close)
    
    return splash