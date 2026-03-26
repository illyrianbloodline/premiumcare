@echo off
echo Stopping any running Flask instance...
taskkill /F /IM python.exe /T 2>nul

echo Clearing Python cache...
for /d /r "C:\Projects\medplatform" %%d in (__pycache__) do (
    if exist "%%d" rd /s /q "%%d"
)
del /s /q "C:\Projects\medplatform\*.pyc" 2>nul

echo Clearing Flask template cache...
if exist "C:\Projects\medplatform\flask_session" rd /s /q "C:\Projects\medplatform\flask_session"

echo Starting app...
cd /d "C:\Projects\medplatform"
python app.py
