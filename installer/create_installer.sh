#!/bin/bash

echo "Creating Meeting Transcriber Installer..."

# Check if the executable exists
if [ ! -f "../dist/MeetingTranscriber.exe" ]; then
    echo "Executable not found. Please build the executable first using build_exe.py"
    exit 1
fi

# Check if Inno Setup is installed (for Windows with WSL)
if [ -f "/mnt/c/Program Files (x86)/Inno Setup 6/ISCC.exe" ]; then
    echo "Running Inno Setup compiler..."
    "/mnt/c/Program Files (x86)/Inno Setup 6/ISCC.exe" MeetingTranscriberSetup.iss
elif [ -f "C:/Program Files (x86)/Inno Setup 6/ISCC.exe" ]; then
    echo "Running Inno Setup compiler..."
    "C:/Program Files (x86)/Inno Setup 6/ISCC.exe" MeetingTranscriberSetup.iss
else
    echo "Inno Setup not found."
    echo "Please download and install Inno Setup from https://jrsoftware.org/isdl.php"
    echo "After installation, run this script again."
    exit 1
fi

# Check if compilation was successful
if [ $? -ne 0 ]; then
    echo "Error: Inno Setup compilation failed."
    exit 1
fi

echo ""
echo "Installer created successfully!"
echo "The installer is located at: $(pwd)/MeetingTranscriberSetup.exe"
echo ""