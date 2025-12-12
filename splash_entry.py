"""
Entry point script for the Meeting Transcriber application.

Author: Gianpaolo Albanese
E-Mail: albaneg@yahoo.com
Work Email: gianpaoa@amazon.com
Date: 05-09-2024
Version: 1.0
Assisted by: Amazon Q for VS Code
"""

import os
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

def main():
    """Main entry point for the Meeting Transcriber application."""
    # Create the application
    app = QApplication(sys.argv)
    
    # Set application icon for taskbar
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Create desktop shortcut if running as executable
    if getattr(sys, 'frozen', False):
        try:
            from meeting_transcriber_gui import create_desktop_shortcut
            create_desktop_shortcut()
        except Exception as e:
            print(f"Error creating desktop shortcut: {e}")
    
    # Import the main module
    from meeting_transcriber_gui import MeetingTranscriberGUI
    
    # Create the main window
    window = MeetingTranscriberGUI()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()