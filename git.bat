@echo off
powershell -Command "git add -A; git commit -m 'backup: %date% %time%'; git push origin main; Write-Host '=== Backup Complete ===' -ForegroundColor Green; pause"