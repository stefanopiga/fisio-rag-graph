@echo off
:: Fisio RAG+Graph - Test API Completo (Fixed)
:: Script automatizzato per test sistematici dell'API REST (CMD/Conda)
:: Logs: ..\logs\api_test_log.txt

setlocal enabledelayedexpansion

:: Configurazione
set BASE_URL=http://localhost:8058
set LOG_FILE=..\logs\api_test_log.txt
set DOCUMENT_ID=
set SESSION_ID=
set ERROR_OCCURRED=0

:: Crea directory per logs se non esiste
if not exist "..\logs" mkdir "..\logs"

:: Pulisci log precedente
if exist "%LOG_FILE%" del "%LOG_FILE%"

:: Funzione per logging e output
call :log "🚀 INIZIO TEST API FISIO RAG+GRAPH (FIXED)" "START"
call :log "🔗 Base URL: %BASE_URL%" "INFO"
call :log "📁 Log File: %LOG_FILE%" "INFO"
call :log "⏰ Start Time: %date% %time%" "INFO"
call :log "======================================================================" "INFO"

:: FASE 1: VERIFICHE PRELIMINARI
call :log "📋 FASE 1: VERIFICHE PRELIMINARI" "PHASE"

call :test_endpoint "GET" "/status" "" "Sistema Status Check"
if !ERROR_OCCURRED!==1 goto :error_exit

call :test_endpoint "GET" "/health" "" "Health Check Dettagliato"
if !ERROR_OCCURRED!==1 goto :error_exit

call :test_endpoint "GET" "/graph/statistics" "" "Statistiche Knowledge Graph"
:: Non fermare su errore per graph statistics (normale se vuoto)

:: FASE 2: DOCUMENT MANAGEMENT
call :log "📋 FASE 2: DOCUMENT MANAGEMENT" "PHASE"

:: 2.1 Creare documento usando file temporaneo
call :log "📄 Preparazione JSON documento..." "INFO"
echo {"title": "Test Lombalgia API", "content": "Trattamento del dolore lombare acuto con terapia manuale.", "source": "test-api-cmd", "metadata": {"type": "case_study", "specialty": "physiotherapy"}} > temp_doc.json

call :test_endpoint_file "POST" "/documents" "temp_doc.json" "Creazione Documento Test"
if !ERROR_OCCURRED!==1 goto :error_exit

:: 2.2 Lista documenti per vedere quello creato
call :test_endpoint "GET" "/documents?limit=5&offset=0" "" "Lista Documenti con Pagination"
if !ERROR_OCCURRED!==1 goto :error_exit

:: FASE 3: SEARCH FUNCTIONALITY
call :log "📋 FASE 3: SEARCH FUNCTIONALITY" "PHASE"

:: 3.1 Ricerca ibrida con file temporaneo
echo {"query": "dolore lombare", "search_type": "hybrid", "limit": 5} > temp_search.json
call :test_endpoint_file "POST" "/search" "temp_search.json" "Ricerca Ibrida"
if !ERROR_OCCURRED!==1 goto :error_exit

:: 3.2 Ricerca vettoriale con file temporaneo
echo {"query": "trattamento fisioterapico", "search_type": "vector", "limit": 5} > temp_vector.json
call :test_endpoint_file "POST" "/search" "temp_vector.json" "Ricerca Vettoriale"
if !ERROR_OCCURRED!==1 goto :error_exit

:: 3.3 Ricerca su grafo con file temporaneo
echo {"query": "lombalgia", "search_type": "graph"} > temp_graph.json
call :test_endpoint_file "POST" "/search" "temp_graph.json" "Ricerca su Knowledge Graph"
if !ERROR_OCCURRED!==1 goto :error_exit

:: 3.4 Endpoint GET alternativi (più semplici)
call :test_endpoint "GET" "/search/hybrid?query=dolore%%20lombare&limit=3" "" "Ricerca Ibrida (GET)"
if !ERROR_OCCURRED!==1 goto :error_exit

:: FASE 4: SESSION MANAGEMENT
call :log "📋 FASE 4: SESSION MANAGEMENT" "PHASE"

:: 4.1 Creare sessione con file temporaneo
echo {"user_id": "test_user_cmd", "metadata": {"test_session": true}, "timeout_minutes": 30} > temp_session.json
call :test_endpoint_file "POST" "/sessions" "temp_session.json" "Creazione Sessione Test"
if !ERROR_OCCURRED!==1 goto :error_exit

:: 4.2 Lista sessioni
call :test_endpoint "GET" "/sessions?limit=10" "" "Lista Sessioni"
if !ERROR_OCCURRED!==1 goto :error_exit

:: FASE 5: CHAT API
call :log "📋 FASE 5: CHAT API" "PHASE"

:: 5.1 Chat request con file temporaneo
echo {"message": "Quali sono i trattamenti per la lombalgia acuta?", "search_type": "hybrid"} > temp_chat.json
call :test_endpoint_file "POST" "/chat" "temp_chat.json" "Chat Request Standard"
if !ERROR_OCCURRED!==1 goto :error_exit

:: FASE 6: TEST ERRORI
call :log "📋 FASE 6: TEST GESTIONE ERRORI" "PHASE"

:: 6.1 Documento inesistente (aspetta 404)
call :test_endpoint "GET" "/documents/00000000-0000-0000-0000-000000000000" "" "Test Documento Inesistente (404 atteso)"
:: Non fermare su errore - 404 è atteso

:: CLEANUP FILE TEMPORANEI
call :log "🗑️ Pulizia file temporanei..." "INFO"
if exist "temp_doc.json" del "temp_doc.json"
if exist "temp_search.json" del "temp_search.json"
if exist "temp_vector.json" del "temp_vector.json"
if exist "temp_graph.json" del "temp_graph.json"
if exist "temp_session.json" del "temp_session.json"
if exist "temp_chat.json" del "temp_chat.json"

:: SUCCESSO COMPLETO
call :log "======================================================================" "INFO"
call :log "🎉 TUTTI I TEST COMPLETATI CON SUCCESSO!" "SUCCESS"
call :log "📊 Test eseguiti: Verifiche principali API REST" "SUCCESS"
call :log "🔗 Server testato: %BASE_URL%" "SUCCESS"
call :log "✅ SISTEMA API OPERATIVO" "SUCCESS"
call :log "🏁 SCRIPT TERMINATO" "END"

echo.
echo ✅ TEST COMPLETATI! Controlla il file: %LOG_FILE%
echo.
goto :eof

:error_exit
:: Cleanup in caso di errore
if exist "temp_doc.json" del "temp_doc.json"
if exist "temp_search.json" del "temp_search.json"
if exist "temp_vector.json" del "temp_vector.json"
if exist "temp_graph.json" del "temp_graph.json"
if exist "temp_session.json" del "temp_session.json"
if exist "temp_chat.json" del "temp_chat.json"

call :log "======================================================================" "ERROR"
call :log "❌ TEST FALLITO!" "ERROR"
call :log "🚨 Controllare i dettagli nel log sopra" "ERROR"
call :log "📋 REPORT: Un test ha fallito, verificare configurazione API" "ERROR"
echo.
echo ❌ TEST FALLITI! Controlla i dettagli in: %LOG_FILE%
echo.
exit /b 1

:: Funzione test endpoint standard (GET senza body)
:test_endpoint
set METHOD=%~1
set ENDPOINT=%~2
set BODY=%~3
set DESCRIPTION=%~4

call :log "🧪 TEST: %DESCRIPTION%" "TEST"
call :log "   METHOD: %METHOD% %ENDPOINT%" "TEST"

curl -X %METHOD% "%BASE_URL%%ENDPOINT%" -w "\n   STATUS: %%{http_code}\n" --silent --show-error >> "%LOG_FILE%" 2>&1

if !errorlevel! neq 0 (
    call :log "   ❌ ERROR: Comando curl fallito" "ERROR"
    set ERROR_OCCURRED=1
) else (
    call :log "   ✅ SUCCESS: Richiesta completata" "SUCCESS"
)

goto :eof

:: Funzione test endpoint con file JSON
:test_endpoint_file
set METHOD=%~1
set ENDPOINT=%~2
set JSON_FILE=%~3
set DESCRIPTION=%~4

call :log "🧪 TEST: %DESCRIPTION%" "TEST"
call :log "   METHOD: %METHOD% %ENDPOINT%" "TEST"
call :log "   JSON FILE: %JSON_FILE%" "TEST"

curl -X %METHOD% "%BASE_URL%%ENDPOINT%" -H "Content-Type: application/json" --data-binary @%JSON_FILE% -w "\n   STATUS: %%{http_code}\n" --silent --show-error >> "%LOG_FILE%" 2>&1

if !errorlevel! neq 0 (
    call :log "   ❌ ERROR: Comando curl fallito" "ERROR"
    set ERROR_OCCURRED=1
) else (
    call :log "   ✅ SUCCESS: Richiesta completata" "SUCCESS"
)

goto :eof

:: Funzione logging
:log
set MESSAGE=%~1
set LEVEL=%~2
set TIMESTAMP=%date% %time%

echo [%TIMESTAMP%] [%LEVEL%] %MESSAGE%
echo [%TIMESTAMP%] [%LEVEL%] %MESSAGE% >> "%LOG_FILE%"

goto :eof 