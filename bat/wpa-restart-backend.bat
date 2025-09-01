@echo off
echo ========================================
echo Restarting Backend Service
echo ========================================
echo.

cd /d C:\projects\wpa

echo Stopping backend...
docker-compose stop backend

echo Starting backend...
docker-compose start backend

echo.
echo Checking logs...
timeout /t 3 /nobreak > nul
docker-compose logs --tail=20 backend

echo.
echo Backend restarted!
pause