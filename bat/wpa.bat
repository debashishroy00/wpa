@echo off
:menu
cls
echo ========================================
echo    WealthPath AI Docker Management
echo ========================================
echo.
echo 1. Start all services
echo 2. Stop all services
echo 3. Restart backend
echo 4. View logs
echo 5. Run migrations
echo 6. Health check
echo 7. Full reset (CAUTION!)
echo 8. Exit
echo.

set /p choice=Select option (1-8): 

if %choice%==1 call "%~dp0wpa-start.bat"
if %choice%==2 call "%~dp0wpa-stop.bat"
if %choice%==3 call "%~dp0wpa-restart-backend.bat"
if %choice%==4 call "%~dp0wpa-logs.bat"
if %choice%==5 call "%~dp0wpa-migrate.bat"
if %choice%==6 call "%~dp0wpa-health.bat"
if %choice%==7 call "%~dp0wpa-reset.bat"
if %choice%==8 exit

goto menu