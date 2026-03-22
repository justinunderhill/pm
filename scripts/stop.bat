@echo off
setlocal

set CONTAINER_NAME=pm-mvp
set EXISTING=

for /f %%I in ('docker ps -a --filter "name=^/%CONTAINER_NAME%$" --format "{{.Names}}"') do set EXISTING=%%I

if /I "%EXISTING%"=="%CONTAINER_NAME%" (
  docker rm -f %CONTAINER_NAME% >nul
  echo Container '%CONTAINER_NAME%' stopped and removed.
) else (
  echo Container '%CONTAINER_NAME%' is not running.
)
