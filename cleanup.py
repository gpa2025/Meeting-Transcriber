"""
Cleanup script for the Meeting Transcriber project.

This script removes unnecessary files and directories from the work folder.

Author: Gianpaolo Albanese
E-Mail: albaneg@yahoo.com
Work Email: gianpaoa@amazon.com
Date: 05-09-2024
Version: 1.0
Assisted by: Amazon Q for VS Code
"""

import os
import shutil
import glob

def clean_work_folder():
    """Clean up unnecessary files from the work folder"""
    print("Cleaning up work folder...")
    
    # Files to remove
    files_to_remove = [
        "*.spec",           # PyInstaller spec files
        "*.bak",            # Backup files
        "test_*.py",        # Test files
        "*.pyc",            # Compiled Python files
        "*.pyo",            # Optimized Python files
    ]
    
    # Directories to remove
    dirs_to_remove = [
        "__pycache__",      # Python cache directories
        "build",            # PyInstaller build directory
    ]
    
    # Clean output directory but keep the directory itself
    output_files = glob.glob("output/*")
    for file in output_files:
        if os.path.isfile(file) and not file.endswith(".gitkeep"):
            print(f"Removing output file: {file}")
            os.remove(file)
    
    # Remove specific files
    for pattern in files_to_remove:
        for file in glob.glob(pattern):
            print(f"Removing file: {file}")
            os.remove(file)
    
    # Remove directories
    for dir_pattern in dirs_to_remove:
        for dir_path in glob.glob(dir_pattern):
            if os.path.isdir(dir_path):
                print(f"Removing directory: {dir_path}")
                shutil.rmtree(dir_path)
    
    print("Cleanup complete!")

if __name__ == "__main__":
    clean_work_folder()