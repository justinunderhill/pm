@echo off
setlocal

set ROOT_DIR=%~dp0..
for %%I in ("%ROOT_DIR%") do set ROOT_DIR=%%~fI
set IMAGE_NAME=pm-mvp:local
set CONTAINER_NAME=pm-mvp
set EXISTING=

docker build -t %IMAGE_NAME% "%ROOT_DIR%"
if errorlevel 1 exit /b 1

for /f %%I in ('docker ps -a --filter "name=^/%CONTAINER_NAME%$" --format "{{.Names}}"') do set EXISTING=%%I
if /I "%EXISTING%"=="%CONTAINER_NAME%" docker rm -f %CONTAINER_NAME% >nul

if exist "%ROOT_DIR%\.env" (
  docker run -d --name %CONTAINER_NAME% -p 8000:8000 --env-file "%ROOT_DIR%\.env" %IMAGE_NAME% >nul
) else (
  docker run -d --name %CONTAINER_NAME% -p 8000:8000 %IMAGE_NAME% >nul
)
if errorlevel 1 exit /b 1

echo Container '%CONTAINER_NAME%' is running at http://127.0.0.1:8000
