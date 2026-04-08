@echo off
echo ===========================================
echo  Installazione di HaptyGraph - Lettore NVA 
echo ===========================================

:: Creazione dell'ambiente virtuale
echo [1/4] Creazione dell'ambiente virtuale (venv)...
python -m venv venv

:: Installazione dipendenze
echo [2/4] Installazione delle librerie Python...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
call venv\Scripts\deactivate.bat

:: Creazione del collegamento sul Desktop tramite PowerShell
echo [3/4] Creazione del collegamento sul Desktop...
set SCRIPT_DIR=%~dp0
set TARGET_EXE=%SCRIPT_DIR%venv\Scripts\pythonw.exe
set TARGET_ARGS=%SCRIPT_DIR%main.py
set SHORTCUT_PATH=%USERPROFILE%\Desktop\HaptyGraph.lnk

powershell -Command "$wshell = New-Object -ComObject WScript.Shell; $shortcut = $wshell.CreateShortcut('%SHORTCUT_PATH%'); $shortcut.TargetPath = '%TARGET_EXE%'; $shortcut.Arguments = '%TARGET_ARGS%'; $shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $shortcut.Save()"

:: 4. Creazione file delle Variabili d'Ambiente (.env)
echo [4/4] Creazione del file di configurazione (.env)...
if not exist ".env" (
    (echo OPENAI_API_KEY=) > .env
    (echo GEMINI_API_KEY=) >> .env
    echo   -^> File .env creato con successo.
) else (
    echo   -> File .env gia' esistente, chiavi API preservate.
)

echo ========================================
echo  Installazione Completata! 
echo  Troverai l'icona 'HaptyGraph' sul tuo Desktop.
echo ========================================
pause