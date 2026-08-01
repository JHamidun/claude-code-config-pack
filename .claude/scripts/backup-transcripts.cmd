@echo off
rem Daily incremental backup of Claude Code transcripts + search index.
rem robocopy WITHOUT /PURGE: new files are added, nothing is ever deleted from the backup,
rem so an upstream wipe (like the July 2026 cleanupPeriodDays regression) cannot propagate here.
set DST=${HOME}\claude-transcripts-backup
rem 0) Ensure destination exists (fix 2026-07-17: missing folder caused silent Result=1 failures)
if not exist "%DST%" mkdir "%DST%"
rem 1) Index new sessions into chats.db so the searchable history is always current
set PYTHONIOENCODING=utf-8
python "~/.claude/tools\search_chats.py" index >> "%DST%\backup.log" 2>&1
rem 2) Back up transcripts + index
robocopy "${HOME}\.claude\projects" "%DST%\projects" /E /XJ /R:1 /W:1 /NFL /NDL /NP >> "%DST%\backup.log" 2>&1
robocopy "${HOME}\.claude" "%DST%" chats.db /R:1 /W:1 /NFL /NDL /NP >> "%DST%\backup.log" 2>&1
echo [%date% %time%] backup done >> "%DST%\backup.log"
