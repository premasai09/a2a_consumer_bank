@echo off
echo Starting A2A Consumer Banking System
echo ====================================

echo Starting all bank agents...
echo.

echo Starting Bank Agent 1 (CloudTrust Financial - Port 10002)...
start "Bank Agent 1 - CloudTrust Financial" cmd /k "python -m bank_agent_1_adk.main"
timeout /t 2 /nobreak >nul

echo Starting Bank Agent 2 (Finovate Bank - Port 10003)...
start "Bank Agent 2 - Finovate Bank" cmd /k "python -m bank_agent_2_adk.main"
timeout /t 2 /nobreak >nul

echo Starting Bank Agent 3 (Zentra Bank - Port 10004)...
start "Bank Agent 3 - Zentra Bank" cmd /k "python -m bank_agent_3_adk.main"
timeout /t 2 /nobreak >nul

echo Starting Bank Agent 4 (NexVault Bank - Port 10005)...
start "Bank Agent 4 - NexVault Bank" cmd /k "python -m bank_agent_4_adk.main"
timeout /t 2 /nobreak >nul

echo Starting Bank Agent 5 (Byte Bank - Port 10006)...
start "Bank Agent 5 - Byte Bank" cmd /k "python -m bank_agent_5_adk.main"

echo.
echo Waiting for all bank agents to initialize...
timeout /t 15 /nobreak >nul

echo.
echo Starting Host Agent Custom UI...
echo ===============================
python -m host_agent_adk.start_custom_ui

echo.
echo System startup complete.
pause