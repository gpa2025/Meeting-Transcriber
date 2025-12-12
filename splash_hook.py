"""
Runtime hook for PyInstaller to show a splash screen immediately when the application starts.

Author: Gianpaolo Albanese
E-Mail: albaneg@yahoo.com
Work Email: gianpaoa@amazon.com
Date: 05-09-2024
Version: 1.0
Assisted by: Amazon Q for VS Code
"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
from PyQt5.QtCore import Qt, QTimer

# Store the original sys.argv
original_argv = list(sys.argv)

# Create the application
app = QApplication(sys.argv)

# Create a splash screen
pixmap = QPixmap(600, 400)
pixmap.fill(QColor(0, 120, 212))

# Create a painter to draw on the pixmap
painter = QPainter(pixmap)

# Draw the initials "GPA" with a large, bold font
font = QFont("Arial", 120)
font.setBold(True)
painter.setFont(font)
painter.setPen(Qt.white)
text = "GPA"
text_width = painter.fontMetrics().horizontalAdvance(text)
painter.drawText((pixmap.width() - text_width) // 2, 200, text)

# Add "Meeting Transcriber V1" text with a larger font
font = QFont("Arial", 30)
font.setBold(True)
painter.setFont(font)
text = "Meeting Transcriber V1"
text_width = painter.fontMetrics().horizontalAdvance(text)
painter.drawText((pixmap.width() - text_width) // 2, 280, text)

# Add author text
font = QFont("Arial", 16)
painter.setFont(font)
author_text = "by Gianpaolo Albanese"
author_width = painter.fontMetrics().horizontalAdvance(author_text)
painter.drawText((pixmap.width() - author_width) // 2, 330, author_text)

# End painting
painter.end()

# Show the splash screen
splash = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
splash.show()
app.processEvents()

# Store splash screen and app in global variables to prevent garbage collection
_splash = splash
_app = app

# Define a function to close the splash screen
def close_splash():
    global _splash
    if _splash:
        _splash.close()

# Set a timer to close the splash screen after 3 seconds
# This is a fallback in case the main application doesn't load
QTimer.singleShot(3000, close_splash)

# Restore the original sys.argv
sys.argv = original_argv