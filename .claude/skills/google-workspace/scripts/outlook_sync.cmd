@echo off
REM Перенос рабочих встреч Outlook в Google Календарь.
REM Вызывается планировщиком раз в 20 минут; окна не показывает.
REM Лог перезаписывается каждый раз — нужен только последний результат.
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
python outlook_to_gcal.py > "%TEMP%\outlook_sync.log" 2>&1
exit /b %ERRORLEVEL%
