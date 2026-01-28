@echo off
REM Build standalone EXE for Assistant GUI (requires Python + pip + pyinstaller on Windows)
REM Usage: run in repo root: build_exe.bat
setlocal
python -m pip install --upgrade pip
python -m pip install pyinstaller
pyinstaller --noconfirm --name ai_assistant --onefile assistant_gui.py
echo Build complete. EXE is under dist\\ai_assistant.exe
