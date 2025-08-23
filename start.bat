@echo off
echo Starting WealthPath AI - Backend and Frontend...
echo.

echo Restarting backend container...
docker-compose restart backend

echo.
echo Restarting frontend container...
docker-compose restart frontend

echo.
echo Checking container status...
docker-compose ps

echo.
echo WealthPath AI services restarted successfully!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3004
echo.
pause