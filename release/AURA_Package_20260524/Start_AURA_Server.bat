@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "ROOT=%~dp0"
set "APP=%ROOT%AURA.exe"
set "MODEL_MAIN=%ROOT%models\models\iic\SenseVoiceSmall\model.pt"
set "MODEL_VAD=%ROOT%models\models\iic\speech_fsmn_vad_zh-cn-16k-common-pytorch\model.pt"

title AURA Server Launcher
echo ==================================================
echo AURA Server Preflight Check
echo ==================================================

if not exist "%APP%" (
  echo [ERROR] AURA.exe is missing. Keep the complete release directory.
  pause
  exit /b 1
)

if not exist "%ROOT%_internal\" (
  echo [ERROR] The _internal directory is missing.
  echo         AURA.exe bundles Python dependencies but requires _internal beside it.
  pause
  exit /b 1
)

echo [OK] Server runtime is present. No Python or pip install is required.

set "NEED_MODEL=0"
if not exist "%MODEL_MAIN%" set "NEED_MODEL=1"
if not exist "%MODEL_VAD%" set "NEED_MODEL=1"

if "%NEED_MODEL%"=="0" (
  echo [OK] Local speech models are present and will be reused.
) else (
  echo [INFO] Local speech models are not complete.
  echo        On first startup AURA will download models from ModelScope in China.
  echo [CHECK] Testing connection to www.modelscope.cn:443...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "try { if (Test-NetConnection -ComputerName 'www.modelscope.cn' -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue) { exit 0 } else { exit 1 } } catch { exit 1 }"
  if errorlevel 1 (
    echo [ERROR] www.modelscope.cn:443 is unreachable. First-run model download cannot start.
    echo         Check the network or proxy settings, then run this file again.
    pause
    exit /b 1
  )
  echo [OK] ModelScope is reachable. AURA will download the missing models after launch.
)

netsh advfirewall firewall show rule name="AURA WebSocket 8765" >nul 2>&1
if errorlevel 1 (
  net session >nul 2>&1
  if errorlevel 1 (
    echo [WARN] Missing firewall rule: AURA WebSocket 8765
    echo        If phone discovery fails, run this file as Administrator once.
  ) else (
    netsh advfirewall firewall add rule name="AURA WebSocket 8765" dir=in action=allow protocol=TCP localport=8765 enable=yes >nul 2>&1
    if errorlevel 1 (echo [WARN] Failed to add firewall rule: AURA WebSocket 8765) else (echo [OK] Added firewall rule: AURA WebSocket 8765)
  )
) else (
  echo [OK] Firewall rule exists: AURA WebSocket 8765
)

netsh advfirewall firewall show rule name="AURA File Transfer 8766" >nul 2>&1
if errorlevel 1 (
  net session >nul 2>&1
  if errorlevel 1 (
    echo [WARN] Missing firewall rule: AURA File Transfer 8766
    echo        If phone discovery fails, run this file as Administrator once.
  ) else (
    netsh advfirewall firewall add rule name="AURA File Transfer 8766" dir=in action=allow protocol=TCP localport=8766 enable=yes >nul 2>&1
    if errorlevel 1 (echo [WARN] Failed to add firewall rule: AURA File Transfer 8766) else (echo [OK] Added firewall rule: AURA File Transfer 8766)
  )
) else (
  echo [OK] Firewall rule exists: AURA File Transfer 8766
)

netsh advfirewall firewall show rule name="AURA mDNS 5353" >nul 2>&1
if errorlevel 1 (
  net session >nul 2>&1
  if errorlevel 1 (
    echo [WARN] Missing firewall rule: AURA mDNS 5353
    echo        If phone discovery fails, run this file as Administrator once.
  ) else (
    netsh advfirewall firewall add rule name="AURA mDNS 5353" dir=in action=allow protocol=UDP localport=5353 enable=yes >nul 2>&1
    if errorlevel 1 (echo [WARN] Failed to add firewall rule: AURA mDNS 5353) else (echo [OK] Added firewall rule: AURA mDNS 5353)
  )
) else (
  echo [OK] Firewall rule exists: AURA mDNS 5353
)

tasklist /fi "imagename eq AURA.exe" /nh 2>nul | find /i "AURA.exe" >nul
if not errorlevel 1 (
  echo [INFO] AURA.exe is already running. No duplicate server was started.
  exit /b 0
)

echo [START] Launching AURA server...
if "%NEED_MODEL%"=="1" echo [INFO] Keep the network connected while the first-run model download completes.
start "" /D "%ROOT%" "%APP%"
exit /b 0
