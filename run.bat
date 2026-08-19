@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (
  py -3 -m engine check
  if errorlevel 1 exit /b 1
  py -3 -m engine serve --open %*
  exit /b %errorlevel%
)
where python >nul 2>&1
if %errorlevel%==0 (
  python -m engine check
  if errorlevel 1 exit /b 1
  python -m engine serve --open %*
  exit /b %errorlevel%
)
echo Python 3.10+ peyda nashod.
exit /b 1
