@echo off
git add -A
git commit -m "backup: %date% %time%"
git push origin main
echo === Backup Complete ===
pause