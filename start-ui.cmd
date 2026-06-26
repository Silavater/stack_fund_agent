@echo off
REM ── StackFund web app launcher (Windows) ────────────────────────────────────
REM Double-click this file to run the demo server in ITS OWN window, independent
REM of any Claude/agent session, so it stays up while you record.
REM   - serves http://localhost:5757  (pricing / chat / board / finops / journal)
REM   - needs the stackfund-dashboard container running (for the chat)
REM   - close this window (or Ctrl-C) to stop the server.
REM ─────────────────────────────────────────────────────────────────────────────
cd /d "%~dp0"
set "SF_AGENT_CONTAINER=stackfund-dashboard"
set "SF_UI_PORT=5757"
set "PYTHONUTF8=1"

REM Prefer uv on PATH; fall back to the per-user Hermes install.
set "UV=uv"
where uv >nul 2>nul || set "UV=%USERPROFILE%\.hermes\bin\uv"

echo Starting StackFund UI on http://localhost:%SF_UI_PORT% ...
echo (leave this window open while recording; close it to stop)
echo.
"%UV%" run --extra stripe python ui/server.py

echo.
echo Server stopped.
pause
