@echo off
echo ========================================
echo WealthPath AI Health Check
echo ========================================
echo.

cd /d C:\projects\wpa

echo Checking container status...
docker-compose ps

echo.
echo Testing backend health endpoint...
curl -s http://localhost:8000/health || echo Backend health check failed

echo.
echo Testing frontend...
curl -s -o nul -w "Frontend HTTP Status: %%{http_code}\n" http://localhost:3004 || echo Frontend check failed

echo.
echo Checking database connection...
docker-compose exec backend python -c "from app.db.session import SessionLocal; db = SessionLocal(); print('Database: Connected'); db.close()" 2>nul || echo Database connection failed

echo.
pause