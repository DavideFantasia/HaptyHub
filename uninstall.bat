@echo off
echo =================================
echo  Disinstallazione di HaptyGraph
echo =================================

:: 1. Rimozione dell'Ambiente Virtuale
echo [1/2] Rimozione dell'ambiente virtuale (venv)...
if exist venv\ (
    rmdir /s /q venv
    echo   -^> Cartella venv rimossa con successo.
) else (
    echo   -^> Cartella venv non trovata, salto.
)

:: 2. Rimozione della Scorciatoia (Icona dal Desktop)
echo [2/2] Rimozione dell'icona dal Desktop...
set SHORTCUT_PATH=%USERPROFILE%\Desktop\HaptyGraph.lnk

if exist "%SHORTCUT_PATH%" (
    del /q "%SHORTCUT_PATH%"
    echo   -^> Icona rimossa dal Desktop.
) else (
    echo   -^> Icona non trovata sul Desktop, salto.
)

echo.
echo ===========================================
echo  Pulizia Completata con successo! 
echo  Ora puoi eliminare in sicurezza l'intera cartella del progetto.
echo ===========================================
pause