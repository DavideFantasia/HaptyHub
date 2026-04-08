@echo off
echo ===========================================
echo  Installazione di HaptyGraph - Lettore NVA 
echo ===========================================

:: Creazione dell'ambiente virtuale
echo [1/3] Creazione dell'ambiente virtuale (venv)...
python -m venv venv

:: Installazione dipendenze
echo [2/3] Installazione delle librerie Python...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
call venv\Scripts\deactivate.bat

:: Creazione del collegamento sul Desktop tramite PowerShell
echo [3/3] Creazione del collegamento sul Desktop...
set SCRIPT_DIR=%~dp0
set TARGET_EXE=%SCRIPT_DIR%venv\Scripts\pythonw.exe
set TARGET_ARGS=%SCRIPT_DIR%main.py
set SHORTCUT_PATH=%USERPROFILE%\Desktop\HaptyGraph.lnk

powershell -Command "$wshell = New-Object -ComObject WScript.Shell; $shortcut = $wshell.CreateShortcut('%SHORTCUT_PATH%'); $shortcut.TargetPath = '%TARGET_EXE%'; $shortcut.Arguments = '%TARGET_ARGS%'; $shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $shortcut.Save()"

echo ========================================
echo  Installazione Completata! 
echo  Troverai l'icona 'HaptyGraph' sul tuo Desktop.
echo ========================================
pause