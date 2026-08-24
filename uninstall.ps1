# Claude Code config pack — удаление (Windows / PowerShell)
#
# === ГЛАВНЫЙ ИНВАРИАНТ: удаляем ТОЛЬКО то, что положил install.ps1 ===
# Источник правды — ~/.claude/.ccpack-manifest.txt: install.ps1 записывает туда РОВНО те
# файлы, которые реально создал (не те, что у тебя уже были, даже если имена совпали),
# вместе с размером и датой на момент установки.
#
# Файл удаляется, только если выполнено ВСЁ:
#   1) он перечислен в манифесте;
#   2) он лежит внутри ~/.claude (или это ~/CLAUDE.md от прежних версий пака);
#   3) он не ссылка (symlink/junction);
#   4) размер и дата совпадают с записанными — то есть ты его не менял.
# Изменённый тобой файл НЕ удаляется: раз ты его правил, он больше не наш.
#
# Манифеста нет или он нечитаем — не удаляем НИЧЕГО (fail-closed) и честно говорим об этом.
#
# НЕ ТРОГАЕМ НИКОГДА: .credentials.master.env, .credentials.json, MEMORY.md, memory\,
# projects\ (история сессий), todos\, shell-snapshots\, chats.db*, tg_session.session*,
# settings.local.json, резервные копии ~/.claude.backup.*, и всё, чего нет в манифесте.
param([switch]$DryRun)
$ErrorActionPreference = 'Continue'

$Profile_  = $env:USERPROFILE
$DstClaude = Join-Path $Profile_ '.claude'
$Manifest  = Join-Path $DstClaude '.ccpack-manifest.txt'

if (-not (Test-Path -LiteralPath $Manifest)) {
    Write-Host "Список разложенного не найден: $Manifest"
    Write-Host ""
    Write-Host "Без него невозможно отличить файлы пака от твоих собственных, поэтому НИЧЕГО не удаляю."
    Write-Host "Так и задумано: лучше оставить лишнее, чем снести чужое."
    Write-Host ""
    Write-Host "Что можно сделать:"
    Write-Host "  * если пак ставился этим install.ps1 — манифест должен быть в ~/.claude, проверь;"
    Write-Host "  * если конфиг раскладывался вручную/старым скриптом — удали нужные подкаталоги сам;"
    Write-Host "  * резервные копии (если install.ps1 их делал) лежат рядом: dir `"$DstClaude.backup.*`""
    exit 1
}

$lines = $null
try { $lines = [System.IO.File]::ReadAllLines($Manifest) }
catch { Write-Host "Список разложенного нечитаем: $Manifest — ничего не удаляю (fail-closed)." -ForegroundColor Red; exit 1 }

$preserveDirNames  = @('memory', 'projects', 'todos', 'shell-snapshots')
$preserveFileNames = @('.credentials.master.env', '.credentials.json', 'settings.local.json',
                       'MEMORY.md', '.ccpack-manifest.txt')
function Test-Preserved([string]$rel) {
    # второй рубеж на случай правленого/старого манифеста
    $parts = $rel.Split('/')
    $leaf  = $parts[$parts.Length - 1]
    if ($preserveFileNames -contains $leaf) { return $true }
    if ($leaf -like 'chats.db*' -or $leaf -like 'tg_session.session*') { return $true }
    # Якорь к первому уровню ВНУТРИ .claude — зеркало install.ps1. Здесь путь идёт от
    # профиля (".claude/rules/..."), поэтому смотрим на второй сегмент. Голое имя каталога
    # совпадало на любой глубине, и .claude\templates\memory\* (файлы пака) считались
    # пользовательской памятью, из-за чего uninstall их не убирал.
    if ($parts.Length -gt 2 -and $parts[0] -eq '.claude' -and $preserveDirNames -contains $parts[1]) { return $true }
    return $false
}

# Ссылкой может оказаться не сам файл, а ЛЮБОЙ его предок. Бытовой случай без экзотики:
# человек перенёс ~/.claude\skills в свой репозиторий и слинковал обратно (mklink /J).
# Move в пределах тома сохраняет размер и mtime, поэтому сверка манифеста совпадает — и
# удаление уносит файлы ИЗ ЕГО РЕПОЗИТОРИЯ, а отчёт пишет «пропущено ссылок: 0».
# Поэтому проверяем КАЖДОЕ ЗВЕНО пути, а не только последний элемент.
$linkCache = New-Object 'System.Collections.Generic.Dictionary[string,bool]'
$linksHit  = New-Object 'System.Collections.Generic.HashSet[string]'
function Get-LinkAncestor([string]$rel) {   # вернёт звено-ссылку (rel от профиля) или $null
    $acc = ''
    foreach ($comp in ($rel -split '[\\/]')) {
        if (-not $comp) { continue }
        $acc = if ($acc) { "$acc/$comp" } else { $comp }
        $isLink = $false
        if ($linkCache.ContainsKey($acc)) {
            $isLink = $linkCache[$acc]
        } else {
            try {
                $it = Get-Item -LiteralPath (Join-Path $Profile_ ($acc -replace '/', '\')) -Force -ErrorAction Stop
                $isLink = [bool]($it.Attributes -band [System.IO.FileAttributes]::ReparsePoint)
            } catch { $isLink = $false }
            $linkCache[$acc] = $isLink
        }
        if ($isLink) { return $acc }
    }
    return $null
}

# Молчать про пропущенные ссылки нельзя: человек должен видеть, что часть пака осталась
# лежать в его внешнем каталоге, и убрать её при желании руками.
function Show-SkippedLinks([string]$prefix) {
    foreach ($d in ($linksHit | Sort-Object)) {
        Write-Host "${prefix}  ~\$($d -replace '/', '\') — ссылка: внутрь внешней цели не заходим, файлы под ней НЕ удалены"
    }
}

$epoch = [datetime]::SpecifyKind([datetime]'1970-01-01T00:00:00', 'Utc')
$toDelete = New-Object System.Collections.Generic.List[string]   # относительные пути
$keepLines = New-Object System.Collections.Generic.List[string]
$nMod = 0; $nGone = 0; $nLink = 0; $nPreserved = 0; $nUnsafe = 0

foreach ($line in $lines) {
    if ($line -eq '' -or $line.StartsWith('#')) { continue }
    $f = $line.Split("`t")
    if ($f.Length -lt 3) { $nUnsafe++; continue }
    $sz = $f[0]; $mt = $f[1]; $rel = $f[2]
    # Путь обязан быть внутри .claude. Никаких "..", дисков и абсолютных путей — манифест
    # могли подправить руками. Голый CLAUDE.md разрешён отдельной строкой: так навигационный
    # хаб записывали прежние версии установщика (~\CLAUDE.md), и такие манифесты ещё лежат
    # у тех, кто ставил пак раньше. Сейчас хаб пишется как .claude/CLAUDE.md и проходит по
    # общему правилу.
    if ($rel -match '\.\.' -or $rel -match '^[\\/]' -or $rel -match '^[A-Za-z]:') { $nUnsafe++; continue }
    if (-not ($rel -like '.claude/*' -or $rel -eq 'CLAUDE.md')) { $nUnsafe++; continue }
    if (Test-Preserved $rel) { $nPreserved++; continue }
    $szL = 0L; $mtL = 0L
    if (-not ([long]::TryParse($sz, [ref]$szL)) -or -not ([long]::TryParse($mt, [ref]$mtL)) -or $mtL -le 0) { $nUnsafe++; continue }

    # Проверка ссылки — по ВСЕМ звеньям пути (включая сам файл), а не только по нему одному.
    $linkAnc = Get-LinkAncestor $rel
    if ($linkAnc) { $nLink++; [void]$linksHit.Add($linkAnc); continue }

    $full = Join-Path $Profile_ ($rel -replace '/', '\')
    $item = $null
    try { $item = Get-Item -LiteralPath $full -Force -ErrorAction Stop } catch { $item = $null }
    if ($null -eq $item) { $nGone++; continue }
    if ($item.PSIsContainer) { $nUnsafe++; continue }
    $curMt = [long][math]::Floor(($item.LastWriteTimeUtc - $epoch).TotalSeconds)
    if ($item.Length -eq $szL -and $curMt -eq $mtL) { $toDelete.Add($rel) }
    else { $nMod++; $keepLines.Add($line) }
}

if ($DryRun) {
    Write-Host "[dry-run] Будет удалено файлов: $($toDelete.Count)"
    $toDelete | Select-Object -First 20 | ForEach-Object { Write-Host "  rm ~\$($_ -replace '/', '\')" }
    if ($toDelete.Count -gt 20) { Write-Host "  ... и ещё $($toDelete.Count - 20)" }
    Write-Host "[dry-run] Оставлю (ты их менял после установки): $nMod"
    $keepLines | Select-Object -First 20 | ForEach-Object { Write-Host "  keep ~\$(($_.Split("`t")[2]) -replace '/', '\')" }
    Write-Host "[dry-run] Уже отсутствуют: $nGone"
    Write-Host "[dry-run] Пропущено записей из-за ссылок: $nLink, защищённых: $nPreserved, некорректных: $nUnsafe"
    Show-SkippedLinks "[dry-run] "
    Write-Host "[dry-run] Ничего не изменено."
    exit 0
}

$removed = 0; $failed = 0
$dirs = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($rel in $toDelete) {
    $full = Join-Path $Profile_ ($rel -replace '/', '\')
    try {
        [System.IO.File]::Delete($full)
        $removed++
        # Копим каталоги-предки, чтобы потом снять опустевшие.
        $d = Split-Path $rel -Parent
        while ($d -and $d -ne '.' -and $d -ne '.claude') {
            [void]$dirs.Add($d)
            $d = Split-Path $d -Parent
        }
    } catch { $failed++ }
}

# Опустевшие каталоги — снизу вверх. Directory.Delete($p, $false) удаляет ТОЛЬКО пустой
# каталог: непустой бросит исключение, ссылку не тронем (проверяем ReparsePoint).
# Remove-Item -Recurse здесь не используем принципиально: на junction в PS 5.1 он может
# уйти в ЧУЖУЮ цель.
# Глубину считаем по ОБОИМ разделителям: Split-Path выше вернул пути с '\', и сортировка
# по '/' давала всем одинаковый ключ — порядок получался произвольным, родитель попадался
# раньше своих детей, падал как «непустой» и больше не пересматривался. Именно так после
# полного удаления оставались сотни пустых каталогов.
# Плюс повторные проходы: удаление вложенного каталога делает пустым родителя, поэтому
# одного прохода мало в любом порядке. Цикл идёт, пока есть прогресс.
do {
    $progress = $false
    $sortedDirs = $dirs | Sort-Object { ($_ -split '[\\/]').Count } -Descending
    foreach ($d in $sortedDirs) {
        $full = Join-Path $Profile_ ($d -replace '/', '\')
        # Ссылку ищем по ВСЕМ звеньям пути: rmdir ~/.claude\skills\alpha при junction на
        # skills снёс бы каталог во внешнем репозитории. Кэш здесь не используем — он мог
        # запомнить состояние до удалений; спрашиваем диск заново.
        try {
            $anc = $null; $accum = ''
            foreach ($comp in ($d -split '[\\/]')) {
                if (-not $comp) { continue }
                $accum = if ($accum) { "$accum/$comp" } else { $comp }
                $ai = Get-Item -LiteralPath (Join-Path $Profile_ ($accum -replace '/', '\')) -Force -ErrorAction SilentlyContinue
                if ($ai -and ($ai.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) { $anc = $accum; break }
            }
            if ($anc) { [void]$linksHit.Add($anc); continue }
            [System.IO.Directory]::Delete($full, $false)
            $progress = $true
        } catch { }
    }
} while ($progress)

# Манифест: оставляем записи, которые пережили удаление (изменённые тобой файлы), чтобы
# повторный запуск снова про них честно сказал. Ничего не осталось и что-то удалили — убираем файл.
if ($keepLines.Count -gt 0) {
    $out = New-Object System.Collections.Generic.List[string]
    $out.Add('# ccpack manifest v1 - остаток после uninstall.ps1')
    $out.Add('# Здесь только файлы, которые ты менял после установки, - они НЕ удалены.')
    $out.Add('# поля: размер<TAB>mtime_unix<TAB>путь (относительно профиля)')
    foreach ($l in $keepLines) { $out.Add($l) }
    try { [System.IO.File]::WriteAllLines($Manifest, $out, (New-Object System.Text.UTF8Encoding $false)) } catch { }
} elseif ($removed -gt 0) {
    Remove-Item -LiteralPath $Manifest -Force -ErrorAction SilentlyContinue
} else {
    Write-Host "Удалять нечего — список разложенного оставлен на месте."
}

Write-Host ""
Write-Host "Удалено файлов пака: $removed"
if ($nMod -gt 0)       { Write-Host "Оставлено (ты их правил после установки, значит они уже не наши): $nMod — см. $Manifest" }
if ($nGone -gt 0)      { Write-Host "Уже отсутствовали: $nGone" }
if ($linksHit.Count -gt 0) {
    # $nLink считает записи манифеста; в $linksHit может добавиться ссылка, найденная уже
    # на этапе снятия опустевших каталогов — тогда записей 0, а сказать всё равно надо.
    if ($nLink -gt 0) { Write-Host "Пропущено записей из-за ссылок (внутрь внешних целей не заходим): $nLink" }
    else { Write-Host "Пропущены пути под ссылками (внутрь внешних целей не заходим):" }
    Show-SkippedLinks ""
}
if ($nPreserved -gt 0) { Write-Host "Пропущено защищённых записей: $nPreserved" }
if ($nUnsafe -gt 0)    { Write-Host "Пропущено некорректных записей манифеста: $nUnsafe" }
if ($failed -gt 0)     { Write-Host "Не удалось удалить (нет прав / файл занят): $failed" -ForegroundColor Yellow }
Write-Host ""
Write-Host "НЕ тронуты: ключи (.credentials.*), MEMORY.md, memory\, projects\ (история сессий), todos\,"
Write-Host "  shell-snapshots\, chats.db*, tg_session.session*, settings.local.json и всё, чего нет в манифесте."
$envFile = Join-Path $DstClaude '.credentials.master.env'
if (Test-Path -LiteralPath $envFile) {
    Write-Host "  $envFile оставлен намеренно (там могут быть твои ключи)."
    Write-Host "  Если он так и остался пустым шаблоном — удали его сам."
}
$backups = @(Get-ChildItem -Path (Split-Path $DstClaude -Parent) -Directory -Filter ((Split-Path $DstClaude -Leaf) + '.backup.*') -ErrorAction SilentlyContinue)
if ($backups.Count -gt 0) { Write-Host "Резервные копии на месте: $(($backups | ForEach-Object { $_.FullName }) -join ', ')" }
if ($failed -gt 0) { exit 1 }
exit 0
