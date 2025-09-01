@echo off
echo ========================================
echo WARNING: Full System Reset
echo ========================================
echo This will DELETE all data and rebuild everything!
echo.

set /p confirm=Are you sure? Type YES to continue: 

if not %confirm%==YES (
    echo Reset cancelled.
    pause
    exit
)

cd /d C:\projects\wpa

echo Stopping all containers...
docker-compose down -v

echo Rebuilding images...
docker-compose build --no-cache

echo Starting fresh...
docker-compose up -d

echo.
echo System reset complete!
pause