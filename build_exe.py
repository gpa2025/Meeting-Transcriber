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
    
    # Create spec file
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['meeting_transcriber_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['boto3', 'botocore'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add all Python files in the current directory
import os
for file in os.listdir('.'):
    if file.endswith('.py') and file != 'meeting_transcriber_gui.py' and file != 'build_exe.py':
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
    
    # Create a simple icon if it doesn't exist
    if not os.path.exists("icon.ico"):
        try:
            from PIL import Image, ImageDraw
            
            # Create a simple icon
            img = Image.new('RGB', (256, 256), color=(0, 120, 212))
            draw = ImageDraw.Draw(img)
            draw.rectangle([50, 50, 206, 206], fill=(255, 255, 255))
            draw.rectangle([80, 80, 176, 176], fill=(0, 120, 212))
            
            # Save as .ico
            img.save("icon.ico")
            print("Created icon.ico")
        except ImportError:
            print("PIL not installed, skipping icon creation")
    
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

if __name__ == "__main__":
    build_exe()