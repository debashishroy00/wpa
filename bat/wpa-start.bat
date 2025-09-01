@echo off
echo ========================================
echo Starting WealthPath AI System
echo ========================================
echo.

cd /d C:\projects\wpa

echo Stopping any existing containers...
docker-compose down

echo.
echo Starting all services...
docker-compose up -d

echo.
echo Waiting for services to be healthy...
timeout /t 10 /nobreak > nul

echo.
echo Checking service status...
docker-compose ps

echo.
echo ========================================
echo WealthPath AI is ready!
echo ========================================
echo Frontend: http://localhost:3004
echo Backend API: http://localhost:8000/docs
echo ========================================
pause