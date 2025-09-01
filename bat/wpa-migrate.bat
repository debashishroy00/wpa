@echo off
echo ========================================
echo Running Database Migrations
echo ========================================
echo.

cd /d C:\projects\wpa

echo Running Alembic migrations...
docker-compose exec backend alembic upgrade head

echo.
echo Migrations complete!
pause