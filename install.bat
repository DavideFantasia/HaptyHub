@echo off
echo ===========================================
echo  Installazione di HaptyHub 
echo ===========================================
echo Controllo dipendenze di sistema in corso...
echo ==========================================

:: --- Controllo Node.js ---
where node >nul 2>nul
if %errorlevel% neq 0 (
    :: Se non e' nel PATH, cerchiamo nella cartella standard di installazione
    if exist "C:\Program Files\nodejs\node.exe" (
        echo [OK] Node.js trovato in C:\Program Files ma non nel PATH. Uso percorso assoluto.
        set "PATH=%PATH%;C:\Program Files\nodejs"
    ) else (
        echo [!] Node.js non e' installato. Tentativo di installazione automatica via winget...
        winget install -e --id OpenJS.NodeJS --accept-source-agreements --accept-package-agreements
        if %errorlevel% neq 0 (
            echo.
            echo [ERRORE CRITICO] Installazione di Node.js fallita. 
            echo Scarica e installa Node.js manualmente da: https://nodejs.org/
            pause
            exit /b
        )
        :: Aggiungiamo Node al PATH temporaneo della finestra corrente per far funzionare NPM subito sotto
        set "PATH=%PATH%;C:\Program Files\nodejs"
    )
) else (
    echo [OK] Node.js e' gia' installato e nel PATH.
)

echo [X] Installazione delle dipendenze Node.js...
IF EXIST "package.json" (
    echo   - package.json trovato. Esecuzione npm install...
    call npm install
) ELSE (
    echo   - Inizializzazione Node e installazione elkjs...
    call npm init -y >nul
    call npm install elkjs
)

:: --- Controllo OpenSCAD ---
where openscad >nul 2>nul
if %errorlevel% neq 0 (
    if exist "C:\Program Files\OpenSCAD\openscad.exe" (
        echo [OK] OpenSCAD trovato nella cartella standard. Lo aggiungo al PATH locale...
        set "PATH=%PATH%;C:\Program Files\OpenSCAD"
    ) else if exist "C:\Program Files (x86)\OpenSCAD\openscad.exe" (
        echo [OK] OpenSCAD trovato nella cartella x86. Lo aggiungo al PATH locale...
        set "PATH=%PATH%;C:\Program Files (x86)\OpenSCAD"
    ) else (
        echo [!] OpenSCAD non e' installato. Tentativo di installazione automatica...
        winget install -e --id OpenSCAD.OpenSCAD --accept-source-agreements --accept-package-agreements
        if %errorlevel% neq 0 (
            echo.
            echo [ERRORE CRITICO] Installazione di OpenSCAD fallita. 
            echo Scarica e installa OpenSCAD manualmente da: https://openscad.org/downloads.html
            pause
            exit /b
        )
        :: Aggiorniamo il path per sicurezza
        set "PATH=%PATH%;C:\Program Files\OpenSCAD"
    )
) else (
    echo [OK] OpenSCAD e' gia' installato e configurato.
)

echo.
echo Dipendenze di sistema verificate! Passaggio all'ambiente Python...
echo.

:: Creazione dell'ambiente virtuale
echo [1/4] Creazione dell'ambiente virtuale (venv)...
if not exist "venv\" (
    python -m venv venv
) else (
    echo   - L'ambiente virtuale esiste gia'. Verranno aggiornate le librerie.
)

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
set SHORTCUT_PATH=%USERPROFILE%\Desktop\HaptyHub.lnk

powershell -Command "$wshell = New-Object -ComObject WScript.Shell; $shortcut = $wshell.CreateShortcut('%SHORTCUT_PATH%'); $shortcut.TargetPath = '%TARGET_EXE%'; $shortcut.Arguments = '%TARGET_ARGS%'; $shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $shortcut.Save()"

:: 4. Creazione file delle Variabili d'Ambiente (.env)
echo [4/4] Creazione del file di configurazione (.env)...
if not exist ".env" (
    (echo OPENAI_API_KEY=) > .env
    (echo GEMINI_API_KEY=) >> .env
    echo   -^> File .env creato con successo.
) else (
    echo   -^> File .env gia' esistente, chiavi API preservate.
)

echo ========================================
echo  Installazione Completata! 
echo  Troverai l'icona 'HaptyHub' sul tuo Desktop.
echo ========================================

echo.
echo ==============================================================
echo NOTA IMPORTANTE:
echo Se Node.js o OpenSCAD sono stati installati o rilevati 
echo per la prima volta durante questo processo, DEVI RIAVVIARE 
echo IL COMPUTER (o disconnettere e riconnettere l'utente) 
echo affinche' Python riesca a "vederli" correttamente.
echo ==============================================================
pause