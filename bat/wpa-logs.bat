@echo off
echo ========================================
echo WealthPath AI Logs
echo ========================================
echo.

cd /d C:\projects\wpa

echo Select which logs to view:
echo 1. Backend logs
echo 2. Frontend logs
echo 3. All logs
echo 4. Follow backend logs (real-time)
echo.

set /p choice=Enter your choice (1-4): 

if %choice%==1 (
    docker-compose logs --tail=100 backend
) else if %choice%==2 (
    docker-compose logs --tail=100 frontend
) else if %choice%==3 (
    docker-compose logs --tail=50
) else if %choice%==4 (
    docker-compose logs -f backend
) else (
    echo Invalid choice
)

pause