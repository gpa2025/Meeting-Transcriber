@echo off 
echo Launching Meeting Transcriber... 
cd /d "%~dp0" 
call venv\Scripts\activate.bat 
python main.py 
call venv\Scripts\deactivate.bat 
