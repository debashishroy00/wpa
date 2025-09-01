@echo off
echo ========================================
echo Stopping WealthPath AI System
echo ========================================
echo.

cd /d C:\projects\wpa

docker-compose down

echo.
echo All services stopped.
pause