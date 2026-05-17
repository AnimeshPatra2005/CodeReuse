@echo off
echo Starting Code Reuse Frontend...
echo.
echo Opening browser at http://localhost:8080
echo Press Ctrl+C to stop the server
echo.
cd /d "%~dp0"
start http://localhost:8080
python -m http.server 8080

@REM Made with Bob
