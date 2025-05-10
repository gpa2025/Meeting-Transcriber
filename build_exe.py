"""
Build script for creating an executable of the Meeting Transcriber application.

This script:
1. Creates a custom icon with GPA initials and Meeting Transcriber V1 text
2. Generates a PyInstaller spec file
3. Builds the executable using PyInstaller

Author: Gianpaolo Albanese
E-Mail: albaneg@yahoo.com
Work Email: gianpaoa@amazon.com
Date: 05-09-2024
Version: 1.0
Assisted by: Amazon Q for VS Code
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_exe():
    """Build the executable using PyInstaller"""
    print("Building Meeting Transcriber executable...")
    
    # Install PyInstaller if not already installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Install PyQt5 if not already installed
    try:
        import PyQt5
    except ImportError:
        print("Installing PyQt5...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt5"])
    
    # Install additional dependencies for desktop shortcut creation
    try:
        import winshell
        import win32com
    except ImportError:
        print("Installing winshell and pywin32 for desktop shortcut creation...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "winshell"])
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pywin32"])
    
    # Create a custom icon with GPA initials and Meeting Transcriber V1 text
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple icon with initials and text
        img = Image.new('RGB', (256, 256), color=(0, 120, 212))  # Blue background
        draw = ImageDraw.Draw(img)
        
        # Try to use a system font
        try:
            # Try to find a suitable font
            font_paths = [
                "C:/Windows/Fonts/Arial.ttf",
                "C:/Windows/Fonts/segoeui.ttf",
                "C:/Windows/Fonts/calibri.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
                "/System/Library/Fonts/Helvetica.ttc"  # macOS
            ]
            
            main_font = None
            small_font = None
            for path in font_paths:
                if os.path.exists(path):
                    main_font = ImageFont.truetype(path, 80)  # Larger font for initials
                    small_font = ImageFont.truetype(path, 20)  # Smaller font for text
                    break
            
            if main_font is None:
                # Fallback to default
                main_font = ImageFont.load_default()
                small_font = ImageFont.load_default()
                
            # Draw the initials "GPA"
            initials_text = "GPA"
            # For newer Pillow versions
            if hasattr(draw, 'textbbox'):
                bbox = draw.textbbox((0, 0), initials_text, font=main_font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            else:
                # For older Pillow versions
                text_width, text_height = draw.textsize(initials_text, font=main_font)
                
            position = ((256 - text_width) // 2, (256 - text_height) // 2 - 20)  # Move up a bit
            draw.text(position, initials_text, fill=(255, 255, 255), font=main_font)
            
            # Draw "Meeting Transcriber V1" text
            app_text = "Meeting Transcriber V1"
            # For newer Pillow versions
            if hasattr(draw, 'textbbox'):
                bbox = draw.textbbox((0, 0), app_text, font=small_font)
                small_text_width = bbox[2] - bbox[0]
                small_text_height = bbox[3] - bbox[1]
            else:
                # For older Pillow versions
                small_text_width, small_text_height = draw.textsize(app_text, font=small_font)
                
            small_position = ((256 - small_text_width) // 2, position[1] + text_height + 20)  # Position below initials
            draw.text(small_position, app_text, fill=(255, 255, 255), font=small_font)
            
        except Exception as e:
            print(f"Error with font: {e}")
            # Simple fallback without font
            # Draw a white rectangle for background
            draw.rectangle([48, 48, 208, 208], fill=(255, 255, 255))
            
            # Draw "GPA" in blue
            # Draw "G"
            draw.rectangle([68, 88, 98, 148], fill=(0, 120, 212))
            draw.rectangle([68, 88, 88, 98], fill=(0, 120, 212))
            draw.rectangle([68, 138, 88, 148], fill=(0, 120, 212))
            draw.rectangle([78, 118, 98, 148], fill=(0, 120, 212))
            
            # Draw "P"
            draw.rectangle([108, 88, 138, 148], fill=(0, 120, 212))
            draw.rectangle([108, 88, 128, 118], fill=(0, 120, 212))
            
            # Draw "A"
            draw.polygon([(148, 148), (168, 88), (188, 148)], fill=(0, 120, 212))
            draw.rectangle([153, 118, 183, 128], fill=(0, 120, 212))
            
            # Draw a line for "Meeting Transcriber V1"
            draw.rectangle([58, 158, 198, 168], fill=(0, 120, 212))
        
        # Save as .ico
        img.save("icon.ico")
        print("Created icon.ico with 'GPA' and 'Meeting Transcriber V1'")
    except ImportError:
        print("PIL not installed, skipping icon creation")
    
    # Create spec file
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['splash_entry.py'],  # Use the splash entry point
    pathex=[],
    binaries=[],
    datas=[('icon.ico', '.')],  # Include icon file in the bundle
    hiddenimports=['boto3', 'botocore', 'winshell', 'win32com', 'meeting_transcriber_gui'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['splash_hook.py'],  # Add splash hook
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add all Python files in the current directory
import os
for file in os.listdir('.'):
    if file.endswith('.py') and file != 'splash_entry.py' and file != 'build_exe.py':
        a.datas += [(file, file, 'DATA')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MeetingTranscriber',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
    """
    
    # Write spec file
    with open("meeting_transcriber.spec", "w") as f:
        f.write(spec_content)
    
    # Build the executable
    print("Building executable with PyInstaller...")
    subprocess.check_call([
        sys.executable, 
        "-m", 
        "PyInstaller", 
        "meeting_transcriber.spec",
        "--clean"
    ])
    
    print("Build complete!")
    print(f"Executable is located at: {os.path.abspath(os.path.join('dist', 'MeetingTranscriber.exe'))}")
    
    # Create a desktop shortcut
    try:
        if sys.platform == 'win32':
            print("Creating desktop shortcut...")
            import winshell
            from win32com.client import Dispatch
            
            # Get the path to the executable
            exe_path = os.path.abspath(os.path.join('dist', 'MeetingTranscriber.exe'))
            
            # Get the desktop path
            desktop = winshell.desktop()
            
            # Create shortcut path
            shortcut_path = os.path.join(desktop, "Meeting Transcriber.lnk")
            
            # Create the shortcut
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = exe_path
            shortcut.WorkingDirectory = os.path.dirname(exe_path)
            
            # Set icon path
            icon_path = os.path.abspath("icon.ico")
            if os.path.exists(icon_path):
                shortcut.IconLocation = icon_path
                
            shortcut.save()
            print(f"Desktop shortcut created at: {shortcut_path}")
    except Exception as e:
        print(f"Failed to create desktop shortcut: {e}")

if __name__ == "__main__":
    build_exe()