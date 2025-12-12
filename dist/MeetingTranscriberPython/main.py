"""
Main entry point for Meeting Transcriber

This script shows a splash screen and then launches the Meeting Transcriber GUI.

Author: Gianpaolo Albanese
Date: 05-10-2024
"""

import sys
import time
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from splash_screen import SplashScreen
from meeting_transcriber_gui import MeetingTranscriberGUI

def main():
    # Create application
    app = QApplication(sys.argv)
    
    # Show splash screen
    splash = SplashScreen()
    splash.show()
    
    # Process events to make sure splash screen is displayed
    app.processEvents()
    
    try:
        print("Creating main window...")
        main_window = MeetingTranscriberGUI()
        print("Main window created successfully")
        
        # Show splash screen for 2 seconds, then show main window
        print("Configuring splash screen to finish...")
        splash.show_and_finish(main_window, 2000)
        print("Splash configured to finish")
        
        # Explicitly show and raise the main window
        print("Explicitly showing main window...")
        main_window.show()
        main_window.raise_()
        main_window.activateWindow()
        print("Main window should now be visible")
        
    except Exception as e:
        print(f"ERROR: Failed to create or show main window: {e}")
        traceback.print_exc()
        QMessageBox.critical(None, "Error", f"Application failed to start: {str(e)}\n\nSee console for details.")
        return 1
    
    # Start the application
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
