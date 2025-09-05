@echo off
echo === WealthPath AI Save Tool ===
echo.
echo [1] Quick save (timestamp)
echo [2] Save with message
echo [3] View status only
echo [4] Save without push
echo [5] Cancel
echo.

choice /c 12345 /n /m "Select option: "

if %errorlevel%==1 goto quick
if %errorlevel%==2 goto message
if %errorlevel%==3 goto status
if %errorlevel%==4 goto local
if %errorlevel%==5 goto end

:quick
git add -A
git commit -m "Update: %date% %time%"
git push origin main
echo === Quick Save Complete ===
pause
goto end

:message
set /p msg="Enter commit message: "
git add -A
git commit -m "%msg%"
git push origin main
echo === Save Complete ===
pause
goto end

:status
git status
pause
goto end

:local
git add -A
git commit -m "Local save: %date% %time%"
echo === Local Save Complete (not pushed) ===
pause
goto end

:end