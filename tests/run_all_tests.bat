@echo off
setlocal enabledelayedexpansion

:: ============================================================================
::                Fisio RAG+Graph - Suite di Test Unificata
:: ============================================================================
:: Esegue tutti i test principali in sequenza dalla root del progetto.
:: Si ferma al primo test fallito.
:: Salva un log dettagliato in /logs/
:: ============================================================================

:: --- Naviga alla root del progetto e imposta le variabili ---
pushd "%~dp0..\"
set "PROJECT_ROOT=%cd%"

:: --- Configurazione Robusta Timestamp e Log ---
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /format:list') do set "ts=%%I"
set "TIMESTAMP=%ts:~0,8%_%ts:~8,6%"
set "LOG_DIR=%PROJECT_ROOT%\logs"
set "LOG_FILE=%LOG_DIR%\full_test_run_%TIMESTAMP%.log"

set "ERROR_FLAG=0"
set "CONDA_RUN=C:\Users\aless\miniconda3\Scripts\conda.exe run -n fisio-rag"

:: --- Setup ---
echo.
echo =======================================================
echo            INIZIO SUITE DI TEST COMPLETA
echo         (Eseguita da: %PROJECT_ROOT%)
echo =======================================================
echo.

if not exist "%LOG_DIR%" (
    echo [SETUP] Creazione directory per i log: %LOG_DIR%
    mkdir "%LOG_DIR%"
)

(
    echo =======================================================
    echo           LOG TEST ESEGUITO IL %date% ALLE %time%
    echo =======================================================
) > "%LOG_FILE%"

:: ============================================================================
::                        SEQUENZA DI ESECUZIONE TEST
:: ============================================================================

:: --- Test 1: API REST Completa (fondamentale) ---
echo.
echo ------------------------------------------------------- >> "%LOG_FILE%"
echo [INFO] Inizio test: API REST Completa
(
    echo.
    echo ======================================================= >> "%LOG_FILE%"
    echo               TEST: API REST Completa >> "%LOG_FILE%"
    echo ======================================================= >> "%LOG_FILE%"
    echo Comando: call "tests\test_api_complete_fixed.bat" >> "%LOG_FILE%"
    echo. >> "%LOG_FILE%"
)
call "tests\test_api_complete_fixed.bat" >> "%LOG_FILE%" 2>&1
if !ERRORLEVEL! neq 0 (
    set "ERROR_FLAG=1"
    echo [ERRORE] Test "API REST Completa" fallito.
    goto :end_script
)
echo [SUCCESS] Test "API REST Completa" completato con successo.


:: --- Test 2: Autenticazione (Pytest) ---
echo.
echo ------------------------------------------------------- >> "%LOG_FILE%"
echo [INFO] Inizio test: Autenticazione JWT
(
    echo.
    echo ======================================================= >> "%LOG_FILE%"
    echo               TEST: Autenticazione JWT >> "%LOG_FILE%"
    echo ======================================================= >> "%LOG_FILE%"
    echo Comando: %CONDA_RUN% python -m pytest "tests\test_auth.py" -v >> "%LOG_FILE%"
    echo. >> "%LOG_FILE%"
)
call %CONDA_RUN% python -m pytest "tests\test_auth.py" -v >> "%LOG_FILE%" 2>&1
if !ERRORLEVEL! neq 0 (
    set "ERROR_FLAG=1"
    echo [ERRORE] Test "Autenticazione JWT" fallito.
    goto :end_script
)
echo [SUCCESS] Test "Autenticazione JWT" completato con successo.

:: --- Test 3: Sistema Medico End-to-End ---
echo.
echo ------------------------------------------------------- >> "%LOG_FILE%"
echo [INFO] Inizio test: Sistema Medico E2E
(
    echo.
    echo ======================================================= >> "%LOG_FILE%"
    echo               TEST: Sistema Medico E2E >> "%LOG_FILE%"
    echo ======================================================= >> "%LOG_FILE%"
    echo Comando: %CONDA_RUN% python "tests\complete_medical_test.py" >> "%LOG_FILE%"
    echo. >> "%LOG_FILE%"
)
call %CONDA_RUN% python "tests\complete_medical_test.py" >> "%LOG_FILE%" 2>&1
if !ERRORLEVEL! neq 0 (
    set "ERROR_FLAG=1"
    echo [ERRORE] Test "Sistema Medico E2E" fallito.
    goto :end_script
)
echo [SUCCESS] Test "Sistema Medico E2E" completato con successo.


:: ============================================================================
::                               CONCLUSIONE
:: ============================================================================
:end_script

popd

echo.
echo =======================================================
if %ERROR_FLAG% equ 1 (
    echo               RISULTATO: SUITE FALLITA
    echo.
    echo          Controllare i dettagli nel file di log:
    echo          %LOG_FILE%
) else (
    echo            🎉 RISULTATO: TUTTI I TEST SUPERATI 🎉
    echo.
    echo Il log completo e' disponibile in: %LOG_FILE%
)
echo =======================================================
echo.

endlocal
exit /b %ERROR_FLAG% 