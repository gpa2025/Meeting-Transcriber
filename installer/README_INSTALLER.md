# Meeting Transcriber Installer

This folder contains files to create an installer for the Meeting Transcriber application.

## Prerequisites

1. **Inno Setup**: Download and install from [https://jrsoftware.org/isdl.php](https://jrsoftware.org/isdl.php)
2. **Built Executable**: Make sure you've built the executable using `build_exe.py`

## Creating the Installer

### Windows

1. Run `create_installer.bat` by double-clicking it
2. Wait for the compilation to complete
3. The installer will be created as `MeetingTranscriberSetup.exe` in this folder

### Linux/WSL/Git Bash

1. Make the script executable: `chmod +x create_installer.sh`
2. Run the script: `./create_installer.sh`
3. The installer will be created as `MeetingTranscriberSetup.exe` in this folder

## Installer Contents

The installer includes:

- The Meeting Transcriber executable
- Icon file
- README.md with basic information
- UserGuide.md with detailed usage instructions
- .env.example file with example configuration

## Customization

To customize the installer:

1. Edit `MeetingTranscriberSetup.iss` to change installer settings
2. Edit `README.md` and `UserGuide.md` to update documentation
3. Run the create_installer script again

## Distribution

After creating the installer, you can distribute it to users. They will be able to:

1. Run the installer
2. Follow the installation wizard
3. Launch the application from the desktop shortcut or start menu
4. Configure their AWS settings
5. Start using the application

## Notes

- The installer requires administrator privileges to install to Program Files
- Users can choose to install for the current user only during installation
- The application will save settings to the user's AppData folder