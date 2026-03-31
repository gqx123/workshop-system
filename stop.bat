@echo off
chcp 65001
taskkill /f /im pythonw.exe 2>nul
taskkill /f /im python.exe 2>nul
echo 服务器已停止
pause
