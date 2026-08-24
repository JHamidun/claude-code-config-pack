@echo off
setlocal enabledelayedexpansion
rem Daily incremental backup of Claude Code transcripts + search index (Windows).
rem POSIX twin: backup-transcripts.sh (same layout, same destination name).
rem
rem Run it by hand or from Task Scheduler:
rem   schtasks /create /tn "claude-transcripts-backup" /tr "%%USERPROFILE%%\.claude\scripts\backup-transcripts.cmd" /sc daily /st 21:00
rem
rem robocopy WITHOUT /PURGE: new files are added, nothing is ever deleted from the backup,
rem so an upstream wipe (like the July 2026 cleanupPeriodDays regression) cannot propagate here.
rem
rem cmd.exe does NOT expand ${HOME} or ~ — it passes them through literally, which used to
rem create a real folder named "${HOME}" next to the caller and hide every error in it.
rem Paths are derived from this script's own location instead.

rem 0) Locate .claude (this file lives in .claude\scripts\)
pushd "%~dp0.." || (echo [backup] FATAL: cannot enter "%~dp0.." & exit /b 1)
set "CLAUDE_DIR=%CD%"
popd
set "DST=%USERPROFILE%\claude-transcripts-backup"
set "LOG=%DST%\backup.log"
set "FAILED="

if not exist "%CLAUDE_DIR%\projects" (
  echo [backup] FATAL: "%CLAUDE_DIR%\projects" not found - nothing to back up.
  exit /b 1
)

if not exist "%DST%" mkdir "%DST%"
if not exist "%DST%" (
  echo [backup] FATAL: cannot create "%DST%".
  exit /b 1
)

echo [backup] source: %CLAUDE_DIR%
echo [backup] target: %DST%

rem 1) Index new sessions into chats.db so the searchable history is always current
set PYTHONIOENCODING=utf-8
set "PY="
where python >nul 2>&1 && set "PY=python"
if not defined PY where py >nul 2>&1 && set "PY=py"
if not defined PY (
  echo [backup] WARN: no python on PATH - chats.db index NOT refreshed.
  echo [%date% %time%] WARN: python missing, index skipped >> "%LOG%"
  set "FAILED=1"
) else (
  "%PY%" "%CLAUDE_DIR%\tools\search_chats.py" index >> "%LOG%" 2>&1
  set "RC=!errorlevel!"
  if not "!RC!"=="0" (
    echo [backup] WARN: search_chats.py index failed ^(exit !RC!^) - see "%LOG%".
    set "FAILED=1"
  )
)

rem 2) Back up transcripts + index. robocopy: exit code >=8 means real failure.
robocopy "%CLAUDE_DIR%\projects" "%DST%\projects" /E /XJ /R:1 /W:1 /NFL /NDL /NP >> "%LOG%" 2>&1
set "RC=!errorlevel!"
if !RC! GEQ 8 (
  echo [backup] ERROR: robocopy projects failed ^(exit !RC!^) - see "%LOG%".
  set "FAILED=1"
)

if exist "%CLAUDE_DIR%\chats.db" (
  robocopy "%CLAUDE_DIR%" "%DST%" chats.db /R:1 /W:1 /NFL /NDL /NP >> "%LOG%" 2>&1
  set "RC=!errorlevel!"
  if !RC! GEQ 8 (
    echo [backup] ERROR: robocopy chats.db failed ^(exit !RC!^) - see "%LOG%".
    set "FAILED=1"
  )
) else (
  echo [backup] WARN: no chats.db yet - search index not backed up.
)

if defined FAILED (
  echo [%date% %time%] backup FINISHED WITH ERRORS >> "%LOG%"
  echo [backup] FINISHED WITH ERRORS - backup is incomplete. Log: "%LOG%"
  exit /b 1
)

echo [%date% %time%] backup done >> "%LOG%"
echo [backup] done.
exit /b 0
