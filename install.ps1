# Claude Code config pack installer (Windows / PowerShell)
#
# === ГЛАВНЫЙ ИНВАРИАНТ: установщик НИКОГДА не стирает и не переносит ~/.claude ===
# Твоё дерево ~/.claude остаётся на месте. Пак кладётся ПОВЕРХ копированием (merge).
# Никаких Move-Item/Remove-Item над всем каталогом — раньше -BackupExisting делал
# Move-Item ~/.claude ~/.claude.backup.*, то есть ПЕРЕНОСИЛ конфиг целиком; сбой посреди
# установки оставлял человека без ключей, памяти и истории сессий. Этот режим удалён.
#
# Два режима merge:
#   add-missing (ПО УМОЛЧАНИЮ) — robocopy /XC /XN /XO: докладываем ТОЛЬКО отсутствующие
#                                 файлы; всё существующее не трогаем вообще.
#   repair (-Repair)           — robocopy без /XC /XN /XO: перезаписываем наши базовые файлы.
# preserve-list (ключи, память, история чатов, tg-сессия, settings.local.json,
# ~\.claude\CLAUDE.md) защищён в ОБОИХ режимах, включая -Repair.
#
# Полная копия-бэкап ~/.claude делается ПЕРВОЙ операцией и ПО УМОЛЧАНИЮ. Это сейф-нет,
# а не единственная копия: неполный бэкап — предупреждение, а не остановка.
#
# Всё разложенное пишется в ~/.claude/.ccpack-manifest.txt — по нему uninstall.ps1
# удаляет РОВНО то, что положил пак.
param(
    [switch]$Repair,
    [switch]$NoBackup,
    [switch]$SkipDeps,
    [switch]$DryRun,
    [switch]$BackupExisting,   # устаревший: резервная копия теперь по умолчанию и это КОПИЯ
    [switch]$Force             # удалён: раньше затирал ~/CLAUDE.md
)
$ErrorActionPreference = 'Continue'

if ($Force) {
    Write-Host "ОШИБКА: -Force удалён. Раньше он затирал навигационный хаб без спроса." -ForegroundColor Red
    Write-Host "        Обновить наши базовые файлы: .\install.ps1 -Repair"
    Write-Host "        (~\.claude\CLAUDE.md всё равно не перезаписывается: это твой файл)."
    exit 2
}
if ($BackupExisting) {
    Write-Host "ПРИМЕЧАНИЕ: -BackupExisting больше не нужен — резервная копия делается по умолчанию"
    Write-Host "            и теперь это КОПИЯ, а не перенос ~/.claude."
}

$Here = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Definition }
$SrcClaude      = Join-Path $Here '.claude'
$SrcClaudeMd    = Join-Path $Here 'CLAUDE.md'
# Полный каталог переменных — один файл, и он в templates/. В корне пака лежит
# .credentials.template.env, но это НЕ список ключей: после переезда там записка о новом
# адресе. Установщик копировал именно её в ~\.claude\.credentials.master.env — человек
# открывал свой файл ключей и находил в нём объявление о переезде, а список имён
# переменных не был достижим ниоткуда.
$SrcEnvTemplate = Join-Path $SrcClaude 'templates\.credentials.master.env.example'
$Profile_       = $env:USERPROFILE
$DstClaude      = Join-Path $Profile_ '.claude'
# Навигационный хаб кладём в ПОЛЬЗОВАТЕЛЬСКУЮ память Claude Code — это ~\.claude\CLAUDE.md.
# Только она читается всегда, где бы ни лежал проект. Прежний адрес ~\CLAUDE.md — это
# ПРОЕКТНАЯ память: CLI поднимается от рабочего каталога вверх и подхватывает такой файл,
# только если проект лежит ВНУТРИ профиля. На Windows проект всегда снаружи C:\Users\<имя>,
# поэтому хаб не читался НИКОГДА: пак выглядел установленным, а модель не знала, что у неё
# есть навыки, и на «сделай ролик» писала ffmpeg руками.
$DstClaudeMd    = Join-Path $DstClaude 'CLAUDE.md'
$LegacyClaudeMd = Join-Path $Profile_ 'CLAUDE.md'          # адрес прежних версий пака
$DstSettings    = Join-Path $DstClaude 'settings.json'     # ${HOME} в нём материализуем (блок 5b)
$DstMcpJson     = Join-Path $DstClaude 'mcp.json'
$DstEnv         = Join-Path $DstClaude '.credentials.master.env'
$Manifest       = Join-Path $DstClaude '.ccpack-manifest.txt'

if (-not (Test-Path -LiteralPath $SrcClaude)) { Write-Host "ОШИБКА: не найден $SrcClaude" -ForegroundColor Red; exit 1 }

# --- preserve-list: ПОЛЬЗОВАТЕЛЬСКОЕ, не перезаписываем ни в одном режиме ---------------
# .credentials.* — ключи и OAuth Claude Code. settings.local.json — твои локальные настройки
# (settings.json — наш базовый, его обновляем). MEMORY.md + memory\ — авто-память.
# projects\ — история сессий (самое невосстановимое). todos\, shell-snapshots\ — рантайм.
# chats.db* — база чатов (+ -wal/-shm/-journal). tg_session.session* — авторизация Telegram.
# user-profile.md — файл-анкета: пак везёт ПУСТОЙ шаблон («Your Name»), а установщик прямым
# текстом просит вписать туда своё имя, почту, телефон. Это пользовательские данные, а не наш
# базовый файл, поэтому обращаемся с ним как с ~/CLAUDE.md: кладём, только если его нет, и
# НИКОГДА не перезаписываем — иначе -Repair менял живую анкету обратно на «Your Name».
# Анкета исключается ТОЛЬКО по своему точному месту — rules\user-profile.md. По голому
# имени она резалась на любой глубине, и собственный файл пака
# .claude\get-shit-done\templates\user-profile.md (шаблон, а не твои данные) не
# раскладывался вовсе — на macOS/Linux он ставится, на Windows молча пропадал.
# Тот же класс ошибки, что и с каталогом templates\memory\: правило без якоря.
$excludeNames = @('.credentials.master.env', '.credentials.json', 'settings.local.json',
                  'MEMORY.md', '.ccpack-manifest.txt', 'chats.db*', 'tg_session.session*')
$excludeDirs  = @('memory', 'projects', 'todos', 'shell-snapshots')
$preserveDirNames  = @('memory', 'projects', 'todos', 'shell-snapshots')
$preserveFileNames = @('.credentials.master.env', '.credentials.json', 'settings.local.json',
                       'MEMORY.md', '.ccpack-manifest.txt')
# CLAUDE.md здесь — это ~\.claude\CLAUDE.md, навигационный хаб: тоже твой файл, в него
# дописывают свои заметки. Кладём вручную (блок 4) и только если его нет. Якорь по точному
# пути ОБЯЗАТЕЛЕН: в паке есть свои skills\gstack\CLAUDE.md и skills\n8n\catalog\CLAUDE.md,
# по голому имени они перестали бы раскладываться.
$preserveExactPaths = @('rules/user-profile.md', 'CLAUDE.md')

function Test-Preserved([string]$rel) {
    # $rel — путь относительно .claude, разделитель '/'
    $parts = $rel.Split('/')
    $leaf  = $parts[$parts.Length - 1]
    if ($preserveFileNames -contains $leaf) { return $true }
    if ($preserveExactPaths -contains $rel) { return $true }
    if ($leaf -like 'chats.db*' -or $leaf -like 'tg_session.session*') { return $true }
    # Каталоги пользовательских данных сверяем ТОЛЬКО на первом уровне ~/.claude.
    # Без якоря совпадало имя каталога на ЛЮБОЙ глубине, и собственный каталог пака
    # .claude\templates\memory\ молча не раскладывался: под правило «не трогать память»
    # попадали файлы, которые пак обязан положить. Реальные данные человека лежат
    # ровно в ~/.claude\memory, projects, todos, shell-snapshots — этого якоря достаточно.
    if ($parts.Length -gt 1 -and $preserveDirNames -contains $parts[0]) { return $true }
    return $false
}

# --- symlink/junction-защита: РЕКУРСИВНЫЙ скан всего дерева ~/.claude -------------------
# Любой каталог ИЛИ файл внутри ~/.claude мог быть слинкован (mklink /J, mklink /D, symlink
# на файл) на твой git-репо или облако — и вовсе не обязательно на первом уровне:
# ~\.claude\agents\health, ~\.claude\config\rules-ref\hooks.md — такие же обычные случаи.
# Писать СКВОЗЬ ссылку нельзя: robocopy уходит по ней и затирает ВНЕШНЮЮ цель, а
# восстановить её НЕОТКУДА — резервная копия снимается с /XJ и содержимого внешних целей
# не содержит (и не должна: иначе копия растёт бесконечно). Защита ДО записи —
# единственная, поэтому скан рекурсивный: собираем КАЖДУЮ ссылку на ЛЮБОЙ глубине и
# запрещаем запись, если ссылкой оказалось хотя бы ОДНО ЗВЕНО пути назначения.
# Раньше проверялись только непосредственные дети ~/.claude и дети skills\ — ссылка на
# глубине 2 вне skills\ не обнаруживалась, и -Repair молча затирал внешний файл.
$reparseRels  = New-Object System.Collections.Generic.List[string]   # пути от .claude, разделитель '/'
$reparseDirs  = New-Object System.Collections.Generic.List[string]
$reparseFiles = New-Object System.Collections.Generic.List[string]
# Файлы, у которых есть ВТОРОЕ ИМЯ — жёсткая ссылка (см. большой комментарий ниже).
$hardlinkRels = New-Object System.Collections.Generic.List[string]

# --- ЖЁСТКАЯ ССЫЛКА (hardlink): почему её мало просто «не заметить» ----------------------
# Жёсткая ссылка — это второе имя ТОГО ЖЕ файла, а не отдельная копия. Признака «я ссылка»
# у неё нет: атрибута ReparsePoint нет, оба имени равноправны, скан выше её не видит.
# Robocopy перезаписывает файл НА МЕСТЕ — то есть меняет содержимое сразу по обоим именам:
# человек ставит пак, а меняется и его собственный файл где-нибудь в C:\work\config.json.
# Восстановить неоткуда: резервная копия хранит ~/.claude, а не внешнее имя.
# Лечим не пропуском, а способом записи: такой файл копируем сами — во временный файл рядом,
# затем Move-Item -Force поверх цели. Move заменяет ЗАПИСЬ В КАТАЛОГЕ, а старый файл живёт
# дальше под вторым именем со своим прежним содержимым; ссылка расщепляется, данные целы.
# LinkType возвращает 'HardLink' и в Windows PowerShell 5.1, и в pwsh 7 (проверено).
# Не смогли выяснить — считаем, что ссылка возможна, и идём безопасным путём.
# На файловых системах без жёстких ссылок (FAT, часть сетевых дисков) список будет пуст —
# там и расщеплять нечего.
function Test-MaybeHardlink($item) {
    try {
        if ($item.LinkType -eq 'HardLink') { return $true }
        return $false
    } catch { return $true }
}

function Invoke-LinkScan {
    # Вызывается ДВАЖДЫ: в начале (для dry-run и отчёта) и вплотную к записи (см. «ЛОСС 5»).
    # Списки каждый раз пересобираем с нуля.
    $reparseRels.Clear(); $reparseDirs.Clear(); $reparseFiles.Clear(); $hardlinkRels.Clear()
    if (-not (Test-Path -LiteralPath $DstClaude)) { return $true }
    # Свой обход стеком, а НЕ Get-ChildItem -Recurse: в Windows PowerShell 5.1 рекурсия
    # заходит ВНУТРЬ junction и уходит в чужое дерево (вплоть до зацикливания).
    # Внутрь reparse-точки не спускаемся никогда — она уже целиком под запретом.
    $stack = New-Object System.Collections.Generic.Stack[string]
    $stack.Push('')
    # projects\, todos\, shell-snapshots\, memory\ не обходим: пак туда не пишет ни в одном
    # режиме (preserve-list), а на живой машине это десятки тысяч файлов.
    $skipTop = @('projects', 'todos', 'shell-snapshots', 'memory')
    try {
        while ($stack.Count -gt 0) {
            $rel  = $stack.Pop()
            $full = if ($rel -eq '') { $DstClaude } else { Join-Path $DstClaude ($rel -replace '/', '\') }
            foreach ($k in @(Get-ChildItem -Force -LiteralPath $full -ErrorAction Stop)) {
                $krel = if ($rel -eq '') { $k.Name } else { "$rel/$($k.Name)" }
                if ($k.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
                    # junction (mklink /J), symlink (/D), любой directory reparse point,
                    # symlink на файл — всё сюда; внутрь не заходим
                    [void]$reparseRels.Add($krel)
                    if ($k.PSIsContainer) { [void]$reparseDirs.Add($krel) } else { [void]$reparseFiles.Add($krel) }
                } elseif ($k.PSIsContainer) {
                    if ($rel -eq '' -and $skipTop -contains $k.Name) { continue }
                    $stack.Push($krel)
                } elseif (Test-MaybeHardlink $k) {
                    [void]$hardlinkRels.Add($krel)
                }
            }
        }
    } catch { return $false }
    return $true
}

$scanOk = Invoke-LinkScan
if (-not $scanOk) {
    # Не смогли проверить ссылки — не рискуем писать вовсе (fail-closed).
    Write-Host "ОШИБКА: не удалось просмотреть ~/.claude на симлинки/junction — установка прервана," -ForegroundColor Red
    Write-Host "        чтобы не записать сквозь ссылку в твой внешний каталог. Ничего не изменено."
    Write-Host "        Обычная причина — нет прав на чтение какого-то подкаталога ~/.claude."
    exit 1
}

function Test-LinkExcluded([string]$rel) {
    # true, если ссылкой является сам путь ИЛИ любой его предок
    foreach ($k in $reparseRels) {
        if ($rel -eq $k) { return $true }
        if ($rel.StartsWith("$k/", [System.StringComparison]::OrdinalIgnoreCase)) { return $true }
    }
    return $false
}

# Проверка по ЖИВОМУ состоянию диска — для точечных копирований ниже. Скан знает ссылки на
# момент старта, а этот тест ловит и ссылку, созданную уже после скана.
function Get-LinkAncestor([string]$rel) {   # вернёт звено-ссылку (rel от .claude) или $null
    $acc = ''
    foreach ($comp in $rel.Split('/')) {
        if (-not $comp) { continue }
        $acc = if ($acc) { "$acc/$comp" } else { $comp }
        try {
            $it = Get-Item -LiteralPath (Join-Path $DstClaude ($acc -replace '/', '\')) -Force -ErrorAction Stop
            if ($it.Attributes -band [System.IO.FileAttributes]::ReparsePoint) { return $acc }
        } catch { }
    }
    return $null
}

function Show-Links([string]$prefix) {
    foreach ($n in $reparseRels) {
        Write-Host "${prefix}  ~\.claude\$($n -replace '/', '\') — ссылка (junction/symlink): пропускаю ВЕСЬ этот путь, внешнюю цель не трогаю"
    }
    if ($reparseRels.Count -gt 0) {
        # ${prefix} обязательно в фигурных скобках: кириллица — допустимые символы имени
        # переменной, и "$prefixссылок" разбирается как одно несуществующее имя.
        Write-Host "${prefix}ссылок найдено: $($reparseRels.Count) — ни один файл под ними не записывается"
    }
}

# --- dry-run ветвится ДО любой мутации --------------------------------------------------
if ($DryRun) {
    $mode = if ($Repair) { 'repair' } else { 'add-missing' }
    Write-Host "[dry-run] Режим: $mode"
    if (-not $NoBackup -and (Test-Path -LiteralPath $DstClaude)) {
        Write-Host "[dry-run] WOULD: копия-бэкап $DstClaude -> $DstClaude.backup.<stamp> (КОПИЯ, не перенос; без ключей и tg-сессии; храню 3 последние)"
    }
    if ($Repair) { Write-Host "[dry-run] WOULD: перезаписать наши базовые файлы в $DstClaude; пользовательское (preserve-list) не трогать" }
    else { Write-Host "[dry-run] WOULD: скопировать в $DstClaude ТОЛЬКО недостающие файлы; существующее не трогать" }
    if (Test-Path -LiteralPath $DstClaudeMd) { Write-Host "[dry-run] ~\.claude\CLAUDE.md уже есть — НЕ трогаю (твой файл)" } else { Write-Host "[dry-run] WOULD: создать ~\.claude\CLAUDE.md — навигационный хаб (сейчас его нет)" }
    $srcSettingsDry = Join-Path $SrcClaude 'settings.json'
    if ((Test-Path -LiteralPath $srcSettingsDry) -and ((Get-Content -LiteralPath $srcSettingsDry -Raw -ErrorAction SilentlyContinue) -like '*${HOME}*')) {
        if ((-not (Test-Path -LiteralPath $DstSettings)) -or $Repair) {
            Write-Host "[dry-run] WOULD: заменить `${HOME} в ~\.claude\settings.json на абсолютный путь ($Profile_)"
        } else {
            Write-Host "[dry-run] ~\.claude\settings.json твой — не трогаю; `${HOME} в нём (если есть) останется"
        }
    }
    if (Test-Path -LiteralPath $DstEnv) { Write-Host "[dry-run] .credentials.master.env уже есть — НЕ трогаю" } else { Write-Host "[dry-run] WOULD: создать .credentials.master.env из шаблона" }
    Show-Links "[dry-run] "
    # Про жёсткие ссылки честно предупреждаем ЗАРАНЕЕ: в -Repair такой файл будет записан
    # заново, и связь между двумя именами разорвётся. Данные не пропадут (второе имя
    # останется со старым содержимым), но знать об этом человек должен до запуска.
    if ($Repair) {
        $dryHl = 0
        foreach ($n in $hardlinkRels) {
            if (Test-Preserved $n) { continue }
            if (Test-LinkExcluded $n) { continue }
            if (-not (Test-Path -LiteralPath (Join-Path $SrcClaude ($n -replace '/', '\')))) { continue }
            $dryHl++
            if ($dryHl -le 10) { Write-Host "[dry-run] ~\.claude\$($n -replace '/', '\') — у файла есть второе имя (жёсткая ссылка): запишем новый файл, второе имя останется прежним" }
        }
        if ($dryHl -gt 10) { Write-Host "[dry-run] ... и ещё $($dryHl - 10) таких файлов" }
        if ($dryHl -gt 0) { Write-Host "[dry-run] файлов с несколькими жёсткими ссылками: $dryHl" }
    }
    Write-Host "[dry-run] WOULD: записать список разложенного в $Manifest"
    if ($SkipDeps) {
        Write-Host "[dry-run] -SkipDeps: pip и доводка рантайма пропускаются целиком"
        Write-Host "[dry-run]   (браузер Playwright, маркетплейсы плагинов, node_modules останутся неустановленными)"
    } else {
        Write-Host "[dry-run] WOULD: pip install --user -r requirements.txt"
        # Про сеть надо сказать ЗАРАНЕЕ. План, который молчит про ~150 МБ загрузки,
        # обнаруживается человеком в момент загрузки — на мобильном интернете это поздно.
        Write-Host "[dry-run] WOULD: python ~\.claude\scripts\setup_runtime.py — доводка рантайма, ходит в сеть:"
        Write-Host "[dry-run]   * npx playwright install chromium — около 150 МБ загрузки, самая долгая часть"
        Write-Host "[dry-run]   * claude plugin marketplace add ... — клонирование объявленных маркетплейсов"
        Write-Host "[dry-run]   * npm install для skills\dev-browser и skills\gstack"
        Write-Host "[dry-run]   Пропустить всё это: -SkipDeps (потом можно запустить вручную)"
    }
    Write-Host "[dry-run] Изменений не внесено."
    exit 0
}

# --- 1. Резервная копия — ПЕРВАЯ мутирующая операция ------------------------------------
# Это КОПИЯ. Оригинал остаётся на месте, поэтому неполный бэкап не фатален.
# robocopy, а не Copy-Item -Recurse: PowerShell 5.1 не longPathAware.
# /R:1 /W:1 — не висеть на залоченном файле (дефолт robocopy: 1 000 000 ретраев по 30 с,
# то есть открытый Cursor/Claude подвешивал бы установку фактически навсегда).
# /XJ — не рекурсировать по junction внутри ~/.claude (иначе копия уходит по ссылке
# на профиль/сетевую папку и растёт бесконечно).
# /XF — секреты в копию не кладём: копий храним 3 ротируемые, ключи и tg-сессия
# размножались бы в трёх экземплярах рядом с ~/.claude. Оригиналы целы (preserve-list).
$backupDir = $null
if (-not $NoBackup -and (Test-Path -LiteralPath $DstClaude)) {
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $backupDir = "$DstClaude.backup.$stamp"
    Write-Host "Резервная копия ~/.claude -> $backupDir (без ключей и tg-сессии; храню 3 последние)..."
    $backupOk = $true
    try {
        robocopy $DstClaude $backupDir /E /R:1 /W:1 /XJ /NFL /NDL /NJH /NJS /NP /XF '.credentials.master.env' '.credentials.json' 'tg_session.session*' | Out-Null
        if ($LASTEXITCODE -ge 8) { $backupOk = $false }   # 1..7 у robocopy = успех
        $global:LASTEXITCODE = 0
        if (-not (Test-Path -LiteralPath $backupDir)) { $backupOk = $false }
    } catch { $backupOk = $false }
    if ($backupOk) {
        # Маркер «эту копию сделали мы» — по нему и только по нему ретенция ниже имеет
        # право её удалить. Чужой каталог с похожим именем (в том числе перенесённый
        # ~/.claude от прежних версий пака, где установка делала Move-Item) маркера не
        # имеет и переживёт любое число прогонов.
        try {
            # self: — ПОЛНЫЙ путь самой копии. По нему ретенция отличает свой ротируемый
            # слот от копии этого же каталога, сделанной человеком: при Copy-Item маркер
            # переезжает, а путь в нём остаётся прежним и перестаёт совпадать с фактическим.
            Set-Content -LiteralPath (Join-Path $backupDir '.ccpack-backup') -Encoding UTF8 -ErrorAction Stop `
                -Value @("claude-config-pack backup", "created: $stamp", "source: $DstClaude", "self: $backupDir")
        } catch {
            Write-Host "  (маркер копии записать не удалось — эта копия не будет удаляться ретенцией)"
        }

        # ПОЛНОТА КОПИИ. robocopy возвращает 1..7 как успех — в том числе когда часть
        # файлов пропущена (занят другим процессом, отказано в доступе). Для add-missing
        # это терпимо: мы ничего не перезаписываем. Для -Repair неполная копия означает,
        # что часть перезаписываемых файлов не сохранена НИГДЕ, поэтому считаем сами.
        # Считаем без секретов — их мы исключаем намеренно, иначе копия всегда «неполна».
        if ($Repair) {
            $srcN = 0; $dstN = 0; $countOk = $true
            try {
                $skip = { param($n) $n -eq '.credentials.master.env' -or $n -eq '.credentials.json' -or $n -like 'tg_session.session*' }
                $srcN = (Get-ChildItem -Force -Recurse -File -LiteralPath $DstClaude -ErrorAction Stop |
                         Where-Object { -not (& $skip $_.Name) }).Count
                $dstN = (Get-ChildItem -Force -Recurse -File -LiteralPath $backupDir -ErrorAction Stop).Count
            } catch { $countOk = $false }

            if (-not $countOk) {
                Write-Host "ОШИБКА: не удалось проверить полноту резервной копии, а -Repair перезаписывает файлы." -ForegroundColor Red
                Write-Host "  Прерываю ДО изменений. Повтори позже или запусти без -Repair."
                exit 1
            }
            # Маркер, который мы только что записали, в источнике не существует — поэтому -1.
            if (($dstN - 1) -lt $srcN) {
                Write-Host "ОШИБКА: копия неполная ($($dstN - 1) из $srcN), а -Repair перезаписывает файлы. Прерываю ДО изменений." -ForegroundColor Red
                Write-Host "  Обычно причина в занятых файлах: закрой Cursor, VS Code и Claude Code, потом повтори."
                Write-Host "  Либо запусти БЕЗ -Repair — обычный режим существующие файлы не трогает."
                exit 1
            }
        }
    }
    if (-not $backupOk) {
        # ГЛАВНОЕ РАЗЛИЧИЕ РЕЖИМОВ. «Оригинал не переносится и не стирается» верно ТОЛЬКО
        # для add-missing: там robocopy /XC /XN /XO существующие файлы не трогает вовсе,
        # поэтому отсутствие копии ничем не грозит. В -Repair оригинал именно
        # перезаписывается — и без копии файл человека, совпавший по имени с файлом пака
        # (свой settings.json, свои hooks\, свои rules\*.md), не остаётся НИГДЕ.
        # Раньше оба режима шли дальше с одинаково успокаивающим текстом, а в финале
        # печаталось «Прежняя версия — в резервной копии выше», хотя копии не было.
        if ($Repair) {
            Write-Host "ОШИБКА: резервную копию снять не удалось, а -Repair перезаписывает файлы. Прерываю ДО изменений." -ForegroundColor Red
            Write-Host "  Причина обычно одна из: нет места на диске, квота, профиль только для чтения, сетевой профиль."
            Write-Host "  Устрани причину и повтори. Либо запусти БЕЗ -Repair: обычный режим только докладывает"
            Write-Host "  недостающее и существующие файлы не трогает, поэтому копия там не критична."
            exit 1
        }
        Write-Host "ВНИМАНИЕ: снять полную копию не удалось (возможно, часть файлов занята — открыт Cursor/Claude)."
        Write-Host "  НЕ критично: обычный режим только докладывает недостающее, существующее не трогает. Продолжаю."
        # Копию БЕЗ ЕДИНОГО ФАЙЛА убираем: она ничего не хранит, но занимает один из трёх
        # слотов ретенции и на следующих прогонах вытесняет РАБОЧУЮ копию. Проверяем именно
        # файлы рекурсивно: robocopy успевает создать дерево пустых каталогов даже когда не
        # скопировал ничего. Частичную копию (хоть один файл) оставляем — неполный сейф-нет
        # лучше, чем никакого.
        try {
            if ((Test-Path -LiteralPath $backupDir) -and
                -not (Get-ChildItem -Force -Recurse -File -LiteralPath $backupDir -ErrorAction Stop)) {
                Remove-Item -LiteralPath $backupDir -Recurse -Force -ErrorAction SilentlyContinue
            }
        } catch { }
        $backupDir = $null
    }
    # Ретенция: 3 последние копии. Имя .backup.<yyyyMMdd-HHmmss> => лексикографический
    # порядок = хронологический. Без ретенции каждый прогон оставлял бы полную копию навсегда.
    # УДАЛЯЕМ ТОЛЬКО СВОИ КОПИИ — по маркеру .ccpack-backup внутри.
    # Раньше сносилось ВСЁ, что подошло под маску имени, без вопроса «мы ли это создали».
    # Цена ошибки максимальная: ПРЕДЫДУЩИЕ версии этого же пака делали
    # Move-Item ~/.claude -> ~/.claude.backup.<stamp>, то есть у человека, ставящего пак
    # поверх старой установки, такой каталог — ЕДИНСТВЕННАЯ копия прежнего конфига:
    # история сессий (projects\), память (memory\), chats.db, ключи. Три обычных прогона
    # уничтожали её молча. Каталог без маркера считаем ЧУЖИМ и не трогаем никогда.
    try {
        Get-ChildItem -Path (Split-Path $DstClaude -Parent) -Directory -Filter ((Split-Path $DstClaude -Leaf) + '.backup.*') -ErrorAction Stop |
            Sort-Object Name -Descending | Select-Object -Skip 3 |
            ForEach-Object {
                # Маркера НЕДОСТАТОЧНО: он отвечает «этот каталог сделал наш код», а не
                # «это наш ротируемый слот». Человек мог скопировать нашу копию себе и
                # дописать туда своё — маркер переехал вместе с файлами. Сверяем ПУТЬ,
                # записанный при создании, с фактическим: у копии он не совпадёт.
                $mk = Join-Path $_.FullName '.ccpack-backup'
                if (-not (Test-Path -LiteralPath $mk)) {
                    Write-Host "  Оставляю $($_.FullName) — копия создана не нами (нет маркера .ccpack-backup)."
                    Write-Host "  Если она не нужна, удали вручную."
                    return
                }
                $self = $null
                try {
                    $line = Get-Content -LiteralPath $mk -ErrorAction Stop | Where-Object { $_ -like 'self: *' } | Select-Object -First 1
                    if ($line) { $self = $line.Substring(6).Trim() }
                } catch { $self = $null }
                if ($self -and ($self -eq $_.FullName)) {
                    Remove-Item -Recurse -Force $_.FullName -ErrorAction SilentlyContinue
                } else {
                    Write-Host "  Оставляю $($_.FullName) — маркер указывает на другой путь (это копия нашей копии, а не наш слот)."
                    Write-Host "  Если она не нужна, удали вручную."
                }
            }
    } catch { Write-Host "  (старые копии ~/.claude.backup.* перечислить не удалось — оставляю как есть)" }
} elseif ($NoBackup -and (Test-Path -LiteralPath $DstClaude)) {
    Write-Host "ВНИМАНИЕ: -NoBackup — резервная копия ~/.claude НЕ делается."
}

New-Item -ItemType Directory -Force -Path $DstClaude -ErrorAction SilentlyContinue | Out-Null
if (-not (Test-Path -LiteralPath $DstClaude)) { Write-Host "ОШИБКА: не удалось создать $DstClaude" -ForegroundColor Red; exit 1 }

Show-Links "  "

# --- 2. Список файлов источника + снимок «что уже было» ДО копирования -------------------
$srcRootLen = $SrcClaude.TrimEnd('\').Length + 1
$ourCandidates = New-Object System.Collections.Generic.List[string]
$preExistingPaths = New-Object 'System.Collections.Generic.HashSet[string]'
# path -> строка прошлого манифеста. Нужна не только чтобы знать «наше ли это»,
# но и чтобы в add-missing СОХРАНИТЬ прежние размер/дату (см. блок манифеста ниже).
$prevLine = New-Object 'System.Collections.Generic.Dictionary[string,string]'
if (Test-Path -LiteralPath $Manifest) {
    try {
        foreach ($line in [System.IO.File]::ReadAllLines($Manifest)) {
            if ($line.StartsWith('#')) { continue }
            $f = $line.Split("`t")
            if ($f.Length -ge 3) { $prevLine[$f[2]] = $line }
        }
    } catch { }
}
$manifestOk = $true
# Все файлы пака, которые мы вообще имеем право писать (без preserve-list и без путей под
# ссылками). Нужен, чтобы понять, какие из найденных жёстких ссылок нас касаются.
$srcRels = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
try {
    Get-ChildItem -LiteralPath $SrcClaude -Recurse -File -Force -ErrorAction Stop | ForEach-Object {
        $rel = $_.FullName.Substring($srcRootLen).Replace('\', '/')
        if (Test-Preserved $rel) { return }
        if (Test-LinkExcluded $rel) { return }
        [void]$srcRels.Add($rel)
        $dstPath = Join-Path $DstClaude ($rel -replace '/', '\')
        $preExists = [System.IO.File]::Exists($dstPath) -or [System.IO.Directory]::Exists($dstPath)
        # Наше = чего не было ДО копирования, либо что мы уже записывали в манифест раньше.
        # Файл, который у тебя УЖЕ был и в манифесте не значится, нашим не считаем, даже
        # если -Repair его перезаписал: uninstall.ps1 его не тронет.
        if ((-not $preExists) -or $prevLine.ContainsKey(".claude/$rel")) { $ourCandidates.Add(".claude/$rel") }
        if ($preExists) { [void]$preExistingPaths.Add(".claude/$rel") }
    }
} catch {
    $manifestOk = $false
    Write-Host "ВНИМАНИЕ: не удалось перечислить файлы источника — список разложенного не обновится (uninstall.ps1 эти файлы не тронет)."
}

# --- ЛОСС 5: ПЕРЕПРОВЕРКА ССЫЛОК ВПЛОТНУЮ К ЗАПИСИ --------------------------------------
# Первый скан отработал в самом начале, ДО резервного копирования. Копирование бэкапа —
# это секунды, а на большом конфиге и десятки секунд. Всё это время список ссылок уже
# устарел: junction/symlink, появившийся за это окно (его мог создать твой скрипт
# синхронизации, облачный клиент или ты сам в соседнем окне), не попал бы в /XD /XF —
# и robocopy записал бы сквозь него в твой внешний каталог.
#
# ЧЕСТНО ПРО ОСТАТОК. Полностью окно не закрывается: между этим сканом и моментом, когда
# robocopy запишет последний файл, проходит время самого прогона (обычно секунды). Ссылка,
# созданная ровно в эти секунды, замечена не будет. Закрыть остаток можно было бы, только
# отказавшись от robocopy в пользу пофайлового копирования с проверкой перед каждым файлом,
# но и там окно не ноль (те же микросекунды между проверкой и записью), зато теряются
# длинные пути (>260 символов) — PowerShell 5.1 не longPathAware, а robocopy умеет.
# Итог: было «время копирования резервной копии» (десятки секунд), стало «время одного
# прогона robocopy». Создать ссылку в этот момент может только процесс от твоего имени.
# Второй скан — ещё и последний барьер: не смогли просмотреть дерево — не пишем вовсе.
$knownLinks = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
foreach ($n in $reparseRels) { [void]$knownLinks.Add($n) }
if (-not (Invoke-LinkScan)) {
    Write-Host "ОШИБКА: повторная проверка ~/.claude на симлинки/junction не удалась — установка" -ForegroundColor Red
    Write-Host "        прервана ПЕРЕД записью. Файлы конфига не изменены; резервная копия на месте."
    exit 1
}
foreach ($n in $reparseRels) {
    if ($knownLinks.Contains($n)) { continue }
    Write-Host "  ~\.claude\$($n -replace '/', '\') — ссылка (появилась после первой проверки): пропускаю весь этот путь."
    # Выкидываем такой путь из списка разложенного: иначе манифест записал бы как «наши»
    # файлы, которых мы не клали.
    $drop = @($ourCandidates | Where-Object {
        $_ -eq ".claude/$n" -or $_.StartsWith(".claude/$n/", [System.StringComparison]::OrdinalIgnoreCase) })
    foreach ($d in $drop) { [void]$ourCandidates.Remove($d) }
}

# --- 3. Merge-копия ПОВЕРХ ~/.claude (без переноса и стирания) ---------------------------
# Каталоги пользовательских данных исключаем ПОЛНЫМ путём в источнике — robocopy /XD
# по голому имени режет каталог на ЛЮБОЙ глубине, из-за чего собственный каталог пака
# .claude\templates\memory\ не раскладывался вовсе. Полный путь якорит правило к корню.
$mergeXD = @($excludeDirs | ForEach-Object { Join-Path $SrcClaude $_ })
# Ссылки исключаем ПОЛНЫМ путём и в источнике, и в приёмнике — заранее перечислить их
# можно только рекурсивным сканом (двух уровней недостаточно, ровно на этом и погорели).
# Голое имя тут не годится: оно резало бы одноимённый каталог на любой глубине.
foreach ($n in $reparseDirs) {
    $w = $n -replace '/', '\'
    $mergeXD += (Join-Path $SrcClaude $w)
    $mergeXD += (Join-Path $DstClaude $w)
}
$mergeXF = @($excludeNames)
# Анкету исключаем ПОЛНЫМ путём (см. комментарий у $preserveExactPaths): голое имя
# вырезало бы и одноимённый шаблон пака в get-shit-done\templates\.
foreach ($n in $preserveExactPaths) {
    $w = $n -replace '/', '\'
    $mergeXF += (Join-Path $SrcClaude $w)
    $mergeXF += (Join-Path $DstClaude $w)
}
foreach ($n in $reparseFiles) {
    $w = $n -replace '/', '\'
    $mergeXF += (Join-Path $SrcClaude $w)
    $mergeXF += (Join-Path $DstClaude $w)
}

# Файлы с ВТОРЫМ ИМЕНЕМ (жёсткой ссылкой) забираем у robocopy: он пишет на месте и затёр
# бы содержимое по обоим именам. Копируем их сами ниже — во временный файл + Move-Item,
# то есть с расщеплением ссылки. Актуально только для -Repair: в add-missing robocopy
# /XC /XN /XO существующие файлы не перезаписывает вообще, значит и ломать нечего.
# Про объём: каждый такой файл добавляет два пути в /XF, а командная строка процесса
# ограничена ~32 000 символов. Реально жёстких ссылок в ~/.claude единицы; если их вдруг
# окажутся сотни, robocopy не запустится — и это будет ВИДНО: блок манифеста ниже пересчитает
# файлы «которых не оказалось на месте» и скажет об этом прямым текстом. Молча потерять
# данные этот путь не может: файлы со вторым именем к тому моменту уже скопированы вручную.
$hardlinkTargets = New-Object System.Collections.Generic.List[string]
if ($Repair) {
    foreach ($n in $hardlinkRels) {
        if (-not $srcRels.Contains($n)) { continue }   # не файл пака — мы его и так не пишем
        if (Test-LinkExcluded $n) { continue }         # путь под симлинком — уже запрещён
        [void]$hardlinkTargets.Add($n)
        $w = $n -replace '/', '\'
        $mergeXF += (Join-Path $SrcClaude $w)
        $mergeXF += (Join-Path $DstClaude $w)
    }
}

# Снимаем ДО копирования: были ли settings.json / mcp.json твоими ещё до нас. От этого
# зависит, имеем ли мы право трогать в них пути (блок 5b). Твой файл не правим — предупреждаем.
$settingsPreexisted = Test-Path -LiteralPath $DstSettings
$mcpJsonPreexisted  = Test-Path -LiteralPath $DstMcpJson

$copyFailed = $false
if ($Repair) {
    Write-Host "Режим -Repair: перезаписываю НАШИ базовые файлы свежими (ключи, память, история, settings.local.json, ~\.claude\CLAUDE.md не трогаю)..."
    Write-Host "  ВНИМАНИЕ: если ты правил файл, имя которого совпадает с файлом пака (например,"
    Write-Host "  skills\<имя>\SKILL.md), в этом режиме он будет заменён нашей версией. Прежняя"
    Write-Host "  версия — в резервной копии выше."
    robocopy $SrcClaude $DstClaude /E /XJ /R:1 /W:1 /NFL /NDL /NJH /NJS /NP /XF $mergeXF /XD $mergeXD | Out-Null
} else {
    Write-Host "Добавляю только НЕДОСТАЮЩИЕ файлы конфига (существующее сохраняю)..."
    # /XC /XN /XO — исключить Changed/Newer/Older, т.е. копировать ТОЛЬКО отсутствующие.
    robocopy $SrcClaude $DstClaude /E /XC /XN /XO /XJ /R:1 /W:1 /NFL /NDL /NJH /NJS /NP /XF $mergeXF /XD $mergeXD | Out-Null
}
if ($LASTEXITCODE -ge 8) { $copyFailed = $true; Write-Host "ВНИМАНИЕ: robocopy вернул код $LASTEXITCODE — часть файлов не скопирована." }
$global:LASTEXITCODE = 0

# --- 3b. Файлы с двумя именами: пишем сами, через временный файл + переименование --------
# Copy-Item сохраняет время изменения источника, Move-Item его не меняет — то есть внешне
# результат тот же, что дал бы robocopy, только старый файл под вторым именем остаётся
# нетронутым. Идемпотентность не страдает: повторный прогон кладёт тот же файл байт в байт.
if ($hardlinkTargets.Count -gt 0) {
    $splitOk = New-Object System.Collections.Generic.List[string]
    foreach ($n in $hardlinkTargets) {
        $w   = $n -replace '/', '\'
        $s   = Join-Path $SrcClaude $w
        $d   = Join-Path $DstClaude $w
        $tmp = "$d.ccpk-tmp"
        # Если файл и так наш и не отличается (размер + время), не трогаем его вовсе:
        # robocopy такие файлы тоже пропускает, а лишнее переписывание разорвало бы
        # ссылку без всякой пользы. Заодно не пишем потом, что «расщепили», когда не.
        try {
            $sf = Get-Item -LiteralPath $s -Force -ErrorAction Stop
            $df = Get-Item -LiteralPath $d -Force -ErrorAction Stop
            if ($sf.Length -eq $df.Length -and $sf.LastWriteTimeUtc -eq $df.LastWriteTimeUtc) { continue }
        } catch { }
        # Длинные пути (>260 символов) Copy-Item в PowerShell 5.1 не осилит и честно
        # ругнётся — это лучше, чем прежнее поведение, когда robocopy молча затирал
        # содержимое по второму имени.
        try {
            Copy-Item -LiteralPath $s -Destination $tmp -Force -ErrorAction Stop
            Move-Item -LiteralPath $tmp -Destination $d -Force -ErrorAction Stop
            [void]$splitOk.Add($n)
        } catch {
            $copyFailed = $true
            Write-Host "ВНИМАНИЕ: не удалось обновить ~\.claude\$w ($($_.Exception.Message))."
            Remove-Item -LiteralPath $tmp -Force -ErrorAction SilentlyContinue
        }
    }
    if ($splitOk.Count -gt 0) {
        Write-Host "ПРИМЕЧАНИЕ: у $($splitOk.Count) файл(ов) в ~\.claude было по нескольку жёстких ссылок"
        Write-Host "  (второе имя того же файла — обычно твоя копия вне ~\.claude)."
        Write-Host "  Свежую версию записали как НОВЫЙ файл, второе имя оставили нетронутым:"
        foreach ($n in ($splitOk | Select-Object -First 10)) { Write-Host "    ~\.claude\$($n -replace '/', '\')" }
        if ($splitOk.Count -gt 10) { Write-Host "    ... и ещё $($splitOk.Count - 10)" }
        Write-Host "  Если связь между двумя именами была нужна — пересоздай её вручную (mklink /H)."
    }
}

# --- 4. ~\.claude\CLAUDE.md — навигационный хаб, только если его нет (это ТВОЙ файл) -----
# Пользовательская память Claude Code: единственный файл, который CLI читает при любом
# рабочем каталоге. Из него модель узнаёт, что навыки, правила и команды пака существуют.
# Из merge он исключён (preserve-list), поэтому кладём вручную — как анкету.
$claudeMdAdded = $false
$claudeMdLink  = Get-LinkAncestor 'CLAUDE.md'
if (Test-Path -LiteralPath $SrcClaudeMd) {
    if ($claudeMdLink) {
        # Путь ведёт сквозь ссылку наружу — писать туда нельзя, затрём чужую цель.
        Write-Host "CLAUDE.md пропущен: ~/.claude/$claudeMdLink — ссылка, во внешнюю цель не пишу."
    } elseif (Test-Path -LiteralPath $DstClaudeMd) {
        Write-Host "~\.claude\CLAUDE.md уже есть — НЕ трогаю (твои личные инструкции). Наш вариант: $SrcClaudeMd"
    } else {
        try {
            New-Item -ItemType Directory -Force -Path $DstClaude -ErrorAction SilentlyContinue | Out-Null
            Copy-Item -LiteralPath $SrcClaudeMd -Destination $DstClaudeMd -ErrorAction Stop
            $claudeMdAdded = $true
            Write-Host "Создан ~\.claude\CLAUDE.md — навигация по конфигу (её читает Claude Code)"
        }
        catch { $copyFailed = $true; Write-Host "ВНИМАНИЕ: не удалось скопировать ~\.claude\CLAUDE.md ($($_.Exception.Message))." }
    }
}
# Прежние версии пака клали хаб в ~\CLAUDE.md. Это ПРОЕКТНАЯ память: читается, только когда
# работаешь ВНУТРИ профиля, то есть на Windows не читается никогда. Файл твой — не удаляем,
# но молчать нельзя: он остаётся лежать и вводит в заблуждение («хаб же на месте»).
if (Test-Path -LiteralPath $LegacyClaudeMd) {
    $legacyText = Get-Content -LiteralPath $LegacyClaudeMd -Raw -ErrorAction SilentlyContinue
    if ($legacyText -and $legacyText.Contains('SKILLS-FIRST')) {
        Write-Host "ПРИМЕЧАНИЕ: в ~\CLAUDE.md лежит наш хаб от прежней версии установщика — адрес сменился."
        Write-Host "  Рабочий адрес теперь ~\.claude\CLAUDE.md (его Claude Code читает всегда)."
        Write-Host "  Старый файл можно удалить вручную — сам не трогаю."
    }
}

# --- 4b. rules\user-profile.md — только если его нет (это ТВОЯ анкета) -------------------
# Из merge он исключён в ОБОИХ режимах (см. preserve-list выше), поэтому кладём вручную.
$userProfileRel   = '.claude/rules/user-profile.md'
$srcUserProfile   = Join-Path $SrcClaude 'rules\user-profile.md'
$dstUserProfile   = Join-Path $DstClaude 'rules\user-profile.md'
$userProfileAdded = $false
$userProfileLink = Get-LinkAncestor 'rules/user-profile.md'
if (Test-Path -LiteralPath $srcUserProfile) {
    if (Test-Path -LiteralPath $dstUserProfile) {
        Write-Host "rules\user-profile.md уже есть — НЕ трогаю (там твои личные данные)."
    } elseif ($userProfileLink) {
        # Самого файла ещё нет, но каталог rules\ (или он сам) — ссылка наружу.
        # New-Item + Copy-Item создали бы файл в ТВОЁМ внешнем каталоге. Не делаем.
        Write-Host "rules\user-profile.md пропущен: ~/.claude/$userProfileLink — ссылка, во внешнюю цель не пишу."
    } else {
        try {
            New-Item -ItemType Directory -Force -Path (Split-Path $dstUserProfile -Parent) -ErrorAction SilentlyContinue | Out-Null
            Copy-Item -LiteralPath $srcUserProfile -Destination $dstUserProfile -ErrorAction Stop
            $userProfileAdded = $true
        } catch { $copyFailed = $true; Write-Host "ВНИМАНИЕ: не удалось скопировать rules\user-profile.md ($($_.Exception.Message))." }
    }
}

# --- 5. credentials — только если ключей ещё нет ----------------------------------------
if (Test-Path -LiteralPath $DstEnv) {
    Write-Host "$DstEnv уже есть — НЕ трогаю."
} elseif (Test-Path -LiteralPath $SrcEnvTemplate) {
    try { Copy-Item -LiteralPath $SrcEnvTemplate -Destination $DstEnv -ErrorAction Stop; Write-Host "Создан $DstEnv из templates\.credentials.master.env.example — ключи НЕ нужны: всё работает по подписке Claude. Трогай только если включаешь опциональную платную фичу." }
    catch { $copyFailed = $true; Write-Host "ВНИМАНИЕ: не удалось создать $DstEnv." }
} else {
    # Молчать здесь нельзя: без этого файла у человека нет НИ ОДНОГО достижимого
    # списка имён переменных, а установка при этом выглядит успешной.
    $copyFailed = $true
    Write-Host "ВНИМАНИЕ: шаблона ключей нет ($SrcEnvTemplate) — $DstEnv не создан."
    Write-Host "  Список имён переменных смотри в .claude\templates\.credentials.master.env.example в клоне."
}

# --- 5b. ${HOME} в settings.json -> абсолютный путь --------------------------------------
# В паке пути к хукам, статус-строке и MCP записаны как ${HOME}/.claude/... На Windows это
# не работает, и отказ ТИХИЙ:
#   • hooks[].command и statusLine.command CLI отдаёт шеллу. По умолчанию это Git Bash —
#     без Git for Windows хук не запускается вовсе; с "shell":"powershell" ${HOME} пусто,
#     потому что в PowerShell такой переменной нет (проверено в pwsh 7 и PS 5.1);
#   • mcpServers[].args подставляет САМ CLI по своему окружению (process.env). У процесса
#     Claude Code на Windows переменной HOME нет — сервер не поднимается.
# На экране при этом ни одной ошибки: защитного хука нет, статус-строки нет, MCP нет.
# Пишем то, что работает одинаково везде: абсолютный путь с прямыми слэшами. Прямые слэши
# понимают и node, и python, и сам Windows, и в JSON их не надо экранировать.
$homeFwd = $Profile_.TrimEnd('\', '/') -replace '\\', '/'

function Set-AbsoluteHomePaths([string]$file) {
    # Возвращает $true, если файл в порядке (или трогать было нечего).
    if (-not (Test-Path -LiteralPath $file)) { return $true }
    $raw = Get-Content -LiteralPath $file -Raw -ErrorAction SilentlyContinue
    if (-not $raw -or -not $raw.Contains('${HOME}')) { return $true }
    # .Replace(), а не -replace: второй трактует шаблон как регулярку, а ${...} в ней —
    # ссылка на группу. Подстановка молча превратилась бы в пустую строку.
    $new = $raw.Replace('${HOME}', $homeFwd)
    try { $null = $new | ConvertFrom-Json }
    catch {
        Write-Host "ВНИМАНИЕ: после подстановки путей $file перестал быть корректным JSON — оставил как было." -ForegroundColor Yellow
        return $false
    }
    try {
        # UTF-8 БЕЗ BOM: PS 5.1 в Out-File -Encoding utf8 добавляет BOM, а JSON с BOM
        # часть парсеров не читает.
        [System.IO.File]::WriteAllText($file, $new, (New-Object System.Text.UTF8Encoding($false)))
        return $true
    } catch {
        Write-Host "ВНИМАНИЕ: не удалось записать $file с абсолютными путями ($($_.Exception.Message))." -ForegroundColor Yellow
        return $false
    }
}

if ((-not $settingsPreexisted) -or $Repair) {
    $rawSettings = Get-Content -LiteralPath $DstSettings -Raw -ErrorAction SilentlyContinue
    if ($rawSettings -and $rawSettings.Contains('${HOME}')) {
        if (Set-AbsoluteHomePaths $DstSettings) {
            Write-Host "Пути в settings.json (хуки, статус-строка, MCP) записаны как $homeFwd/.claude/..."
        } else {
            $copyFailed = $true
        }
    }
} elseif (Test-Path -LiteralPath $DstSettings) {
    $rawSettings = Get-Content -LiteralPath $DstSettings -Raw -ErrorAction SilentlyContinue
    if ($rawSettings -and $rawSettings.Contains('${HOME}')) {
        Write-Host "ВНИМАНИЕ: в твоём ~\.claude\settings.json пути записаны через `${HOME}." -ForegroundColor Yellow
        Write-Host "  Твой файл я не трогаю. Но на Windows такая запись молча отключает защитный хук,"
        Write-Host "  статус-строку и MCP: у процесса Claude Code переменной HOME нет."
        Write-Host "  Замени `${HOME} на $homeFwd вручную — или запусти .\install.ps1 -Repair."
    }
}
if ((-not $mcpJsonPreexisted) -or $Repair) { $null = Set-AbsoluteHomePaths $DstMcpJson }

# --- 6. Манифест: РОВНО то, что положили мы ---------------------------------------------
if ($manifestOk) {
    if ($claudeMdAdded) { $ourCandidates.Add('.claude/CLAUDE.md') }
    if ($userProfileAdded) { $ourCandidates.Add($userProfileRel) }
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add('# ccpack manifest v1 - файлы, разложенные your-config-repo')
    $lines.Add('# Не редактируй руками. uninstall.ps1 удаляет ТОЛЬКО перечисленное здесь')
    $lines.Add('# и только если файл не изменился (сверка по размеру и дате).')
    $lines.Add('# поля: размер<TAB>mtime_unix<TAB>путь (относительно профиля)')
    $epoch = [datetime]::SpecifyKind([datetime]'1970-01-01T00:00:00', 'Utc')
    $written = New-Object 'System.Collections.Generic.HashSet[string]'
    $notPlaced = 0
    foreach ($rel in $ourCandidates) {
        # Ключи в манифест не попадают никогда — их uninstall не должен удалять даже теоретически.
        if ($rel -like '.claude/.credentials.*') { continue }
        # Файл, который УЖЕ лежал в ~/.claude до этого прогона, мы в add-missing НЕ писали
        # (robocopy /XC /XN /XO его пропустил). Значит и запись в манифесте должна остаться
        # ПРЕЖНЕЙ — с размером и датой на момент, когда файл клали МЫ.
        # Иначе получается «отмывание правки»: ты поправил наш файл, потом повторно запустил
        # установку, и она записала бы в манифест твой изменённый размер/дату. После этого
        # uninstall считал бы файл нетронутым и УДАЛИЛ бы его вместе с твоей правкой.
        # В -Repair наоборот: там мы файл действительно перезаписали своей версией,
        # поэтому актуальные размер/дата — правильные.
        # $copyFailed в -Repair означает «часть файлов переписать не удалось» (файл занят).
        # Какие именно — robocopy не говорит, поэтому для всех уже существовавших файлов
        # действует то же консервативное правило: держим прежнюю запись. Худшее, что из
        # этого выйдет, — uninstall оставит лишний файл. Это лучше, чем удалить чужой.
        if (((-not $Repair) -or $copyFailed) -and $preExistingPaths.Contains($rel) -and $prevLine.ContainsKey($rel)) {
            $lines.Add($prevLine[$rel])
            [void]$written.Add($rel)
            continue
        }
        $full = Join-Path $Profile_ ($rel -replace '/', '\')
        $fi = New-Object System.IO.FileInfo $full
        if (-not $fi.Exists) {
            # Файла нет там, где он должен был появиться. Если он и не существовал до прогона —
            # значит копирование его пропустило (антивирус придержал файл, права, диск),
            # и robocopy об этом не сообщил. Молчать нельзя: файл не разложен И не попадёт
            # в список разложенного. Если же файл раньше был наш, а сейчас его нет — это
            # нормально, человек его просто удалил.
            if (-not $preExistingPaths.Contains($rel)) { $notPlaced++ }
            continue
        }
        $mt = [long][math]::Floor(($fi.LastWriteTimeUtc - $epoch).TotalSeconds)
        $lines.Add("$($fi.Length)`t$mt`t$rel")
        [void]$written.Add($rel)
    }
    # Переносим записи прошлых прогонов, которые сейчас не обновлялись, но файлы на месте:
    # иначе снятие пака работало бы ровно один раз (на второй прогон наши вчерашние файлы
    # уже «пред-существуют», разность пуста и uninstall стал бы no-op).
    if (Test-Path -LiteralPath $Manifest) {
        try {
            foreach ($line in [System.IO.File]::ReadAllLines($Manifest)) {
                if ($line.StartsWith('#')) { continue }
                $f = $line.Split("`t")
                if ($f.Length -lt 3) { continue }
                if ($written.Contains($f[2])) { continue }
                $full = Join-Path $Profile_ ($f[2] -replace '/', '\')
                if ([System.IO.File]::Exists($full)) { $lines.Add($line) }
            }
        } catch { }
    }
    if ($notPlaced -gt 0) {
        Write-Host "ВНИМАНИЕ: $notPlaced файл(ов) пака не оказалось на месте после копирования"
        Write-Host "  (чаще всего их придержал антивирус или не хватило прав). Они НЕ разложены и"
        Write-Host "  не попали в список разложенного. Запусти установку ещё раз — она их доложит."
    }
    try {
        $enc = New-Object System.Text.UTF8Encoding $false    # без BOM
        [System.IO.File]::WriteAllLines($Manifest, $lines, $enc)
        Write-Host "Список разложенного записан: $Manifest (файлов: $($lines.Count - 4))"
    } catch {
        Write-Host "ВНИМАНИЕ: не удалось записать $Manifest — uninstall.ps1 не сможет ничего удалить (fail-closed)."
    }
}

# --- 6b. Поиск НАСТОЯЩЕГО Python ---------------------------------------------------------
# На чистой Win11 в PATH выше настоящего интерпретатора лежит заглушка Microsoft Store
# (%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe). Это не Python, а перехватчик: он
# открывает магазин приложений и не возвращает управление — установка встаёт намертво,
# без единого сообщения на экране. Поэтому:
#   • берём ВСЕ одноимённые команды из PATH (-All), а не первую: заглушка обычно первая,
#     и без -All фильтр выбросил бы её вместе с ответом «Python не найден»;
#   • отсеиваем по ПУТИ (WindowsApps), а не по имени;
#   • добавляем типовые каталоги установки — python.org и winget не всегда правят PATH
#     текущего процесса;
#   • проверяем кандидата запуском `--version` и ждём ответа вида «Python 3.x».
# Та же гоча описана в skills/installer-builder/references/gotchas.md §3.
function Get-RealPython {
    $cands = New-Object System.Collections.Generic.List[string]
    # 1) настоящий python.exe из PATH
    foreach ($n in @('python', 'python3')) {
        try {
            Get-Command $n -All -ErrorAction SilentlyContinue |
                Where-Object { $_.Path -and $_.Path -notmatch '\\WindowsApps\\' } |
                ForEach-Object { $cands.Add($_.Path) }
        } catch { }
    }
    # 2) типовые каталоги установки — PATH текущего процесса мог не обновиться
    $probes = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Python'),
        (Join-Path $env:ProgramFiles 'Python'),
        'C:\'
    )
    foreach ($root in $probes) {
        if (-not $root) { continue }
        try {
            Get-ChildItem -LiteralPath $root -Filter 'Python3*' -Directory -ErrorAction SilentlyContinue |
                Sort-Object Name -Descending | ForEach-Object {
                    $exe = Join-Path $_.FullName 'python.exe'
                    if ([System.IO.File]::Exists($exe)) { $cands.Add($exe) }
                }
        } catch { }
    }
    # 3) последний резерв — лаунчер py.exe (он ставится вместе с настоящим Python,
    #    на чистой системе его нет; без установленного Python отсеется проверкой версии)
    try {
        Get-Command 'py' -All -ErrorAction SilentlyContinue |
            Where-Object { $_.Path -and $_.Path -notmatch '\\WindowsApps\\' } |
            ForEach-Object { $cands.Add($_.Path) }
    } catch { }

    foreach ($c in $cands) {
        if ($c -match '\\WindowsApps\\') { continue }
        try {
            $out = & $c --version 2>&1 | Out-String
            if ($out -match 'Python\s+3\.\d') { return $c }
        } catch { }
    }
    return $null
}
$PyExe = Get-RealPython

# --- 7. Python-зависимости (по желанию) --------------------------------------------------
if (-not $SkipDeps) {
    $req = Join-Path $Here 'requirements.txt'
    if (Test-Path -LiteralPath $req) {
        $py = $PyExe
        if ($py) {
            Write-Host "Ставлю Python-зависимости (--user)... (пропустить: -SkipDeps)"
            $pipOk = $false
            try {
                & $py -m pip install --user --upgrade pip 2>$null | Out-Null
                & $py -m pip install --user -r $req
                $pipOk = ($LASTEXITCODE -eq 0)
            } catch { $pipOk = $false }
            $global:LASTEXITCODE = 0

            # Проверяем РЕЗУЛЬТАТ, а не код возврата.
            if ($pipOk) {
                & $py -c "import requests" 2>$null | Out-Null
                if ($LASTEXITCODE -ne 0) {
                    $pipOk = $false
                    Write-Host "  pip отчитался об успехе, но 'import requests' не проходит — считаю это провалом."
                }
                $global:LASTEXITCODE = 0
            }

            # Пакетная установка — всё или ничего: pip сначала решает весь граф, и ОДИН
            # пакет без колеса под эту платформу оставляет без библиотек все остальные.
            # Добиваем по одному: пусть не приедет один, а не тридцать восемь.
            $failedPkgs = @()
            if (-not $pipOk) {
                Write-Host "  Пакетная установка не прошла — ставлю по одному, чтобы уцелело максимум."
                foreach ($raw in [System.IO.File]::ReadAllLines($req)) {
                    $pkg = ($raw -split '#')[0].Trim()
                    if (-not $pkg) { continue }
                    & $py -m pip install --user $pkg 2>$null | Out-Null
                    if ($LASTEXITCODE -ne 0) { $failedPkgs += $pkg }
                    $global:LASTEXITCODE = 0
                }
                & $py -c "import requests" 2>$null | Out-Null
                $baseOk = ($LASTEXITCODE -eq 0)
                $global:LASTEXITCODE = 0
                if ($baseOk) {
                    if ($failedPkgs.Count -gt 0) {
                        Write-Host "  Базовое встало. НЕ установилось (навыки, которым это нужно, работать не будут):"
                        foreach ($p in $failedPkgs) { Write-Host "      $p" }
                        Write-Host "Python-зависимости встали ЧАСТИЧНО (проверено импортом)."
                    } else {
                        Write-Host "Python-зависимости на месте (проверено импортом)."
                    }
                    $pipOk = $true
                }
            } else {
                Write-Host "Python-зависимости на месте (проверено импортом)."
            }

            if (-not $pipOk) {
                # Раньше здесь печаталось «на работу конфига не влияет». Это неправда:
                # от Python зависят ~46 навыков и весь ~\.claude\tools\ — без библиотек
                # они падают ModuleNotFoundError, и связь с установкой уже не видна.
                Write-Host ""
                Write-Host "ВНИМАНИЕ: Python-зависимости НЕ установлены." -ForegroundColor Yellow
                Write-Host "  Это НЕ косметика: без них ~46 навыков и все CLI из $DstClaude\tools\"
                Write-Host "  будут падать с 'ModuleNotFoundError'. Конфиг разложен, но работать будет неполно."
                Write-Host "  Поставить вручную:"
                Write-Host "    `"$py`" -m pip install --user -r `"$req`""
                Write-Host "  Если pip ругается на права или на 'externally-managed-environment':"
                Write-Host "    `"$py`" -m pip install --user --break-system-packages -r `"$req`""
            }
        } else {
            Write-Host ""
            Write-Host "ВНИМАНИЕ: Python не найден — зависимости НЕ установлены." -ForegroundColor Yellow
            Write-Host "  От Python зависят ~46 навыков и все CLI из $DstClaude\tools\ — без него они не работают."
            Write-Host "  Поставь Python 3 (python.org или 'winget install Python.Python.3.13'),"
            Write-Host "  открой НОВОЕ окно терминала и запусти установку ещё раз."
            Write-Host "  Заглушка из Microsoft Store не подходит — нужен настоящий интерпретатор."
        }
    }
}

# --- 7b. Рантайм: то, что живёт НЕ в файлах ------------------------------------------------
# Копирование файлов — ещё не рабочий конфиг. Три вещи живут в состоянии машины, и без них
# пак выглядит установленным, а половина скиллов падает на первом запуске:
#   • браузер Playwright (пакет ставится из requirements, сам браузер — нет; на него
#     завязаны 42 скилла: карточки, экспорт в PNG/PDF/PPTX, деки, скриншот-тесты);
#   • маркетплейсы плагинов (объявлено 33 плагина, но машина не знает, откуда их брать);
#   • node_modules для dev-browser (его server.sh иначе делает npm install в бою).
# Именно это и было «полчаса докручивали после установки»: скрипт-лекарство существовал,
# но его никто не вызывал, и на экране о нём не было ни слова.
# Идемпотентно: повторный прогон занимает секунды и ничего не делает.
if (-not $SkipDeps) {
    $runtimeScript = Join-Path $DstClaude 'scripts\setup_runtime.py'
    if (Test-Path -LiteralPath $runtimeScript) {
        # Интерпретатор ищем той же Get-RealPython, что и в блоке 7: заглушку Microsoft
        # Store (WindowsApps\python.exe) брать нельзя — она не интерпретатор, а перехватчик,
        # открывает магазин и не возвращает управление.
        $py2 = $PyExe
        if ($py2) {
            Write-Host ""
            Write-Host "Довожу рантайм (браузер Playwright, маркетплейсы плагинов, node_modules)..."
            & $py2 $runtimeScript
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Рантайм доехал НЕ полностью. Это не ломает установку — доделать можно в любой момент:"
                Write-Host "  python `"$runtimeScript`""
                Write-Host "Что именно не хватает, покажет: python `"$runtimeScript`" --check"
            }
            $global:LASTEXITCODE = 0
        } else {
            Write-Host "Python не найден — рантайм не доведён. После установки Python запусти:"
            Write-Host "  python `"$runtimeScript`""
        }
    }
} else {
    # -SkipDeps гасит и этот шаг тоже. Пока об этом молчали, флаг читался как
    # «не ставить pip-пакеты», а выключал заодно браузер (42 навыка), маркетплейсы
    # плагинов и node_modules — и человек узнавал об этом только по отказу навыка.
    Write-Host ""
    Write-Host "-SkipDeps: рантайм НЕ доведён. Не сделано:"
    Write-Host "  * браузер Playwright (~150 МБ) — от него зависят 42 навыка;"
    Write-Host "  * маркетплейсы плагинов (объявлено 33 плагина);"
    Write-Host "  * node_modules для dev-browser и gstack."
    Write-Host "Доделать в любой момент: python `"$(Join-Path $DstClaude 'scripts\setup_runtime.py')`""
}

# --- 7c. Проверка ПОСЛЕ установки --------------------------------------------------------
# Скопировали ≠ работает. Самый дорогой отказ этого пака — тихий: файлы на месте, «ГОТОВО»
# на экране, а хаб не читается или защитный хук не запускается. В бою этого не понять:
# модель просто не знает, что навыки есть. Проверяем ровно то, без чего пак мёртв.
$verifyFailed = $false
Write-Host ""
Write-Host "Проверяю установленное..."

# 1) навигационный хаб — единственный файл, из которого модель узнаёт про навыки
$hubItem = Get-Item -LiteralPath $DstClaudeMd -Force -ErrorAction SilentlyContinue
if (-not $hubItem -or $hubItem.PSIsContainer) {
    Write-Host "  [X] НЕТ $DstClaudeMd — Claude Code не увидит НИ ОДНОГО навыка пака." -ForegroundColor Red
    Write-Host "      Положи его вручную:  Copy-Item `"$SrcClaudeMd`" `"$DstClaudeMd`""
    $verifyFailed = $true
} elseif ($hubItem.Length -eq 0) {
    Write-Host "  [X] $DstClaudeMd пустой (0 байт) — это то же самое, что его нет." -ForegroundColor Red
    $verifyFailed = $true
} else {
    $hubText = Get-Content -LiteralPath $DstClaudeMd -Raw -ErrorAction SilentlyContinue
    if (-not $hubText) {
        Write-Host "  [X] $DstClaudeMd не читается (права доступа?)." -ForegroundColor Red
        $verifyFailed = $true
    } else {
        Write-Host "  [ok] ~\.claude\CLAUDE.md на месте и читается ($($hubItem.Length) байт)" -ForegroundColor Green
        if (-not $hubText.Contains('SKILLS-FIRST')) {
            Write-Host "       (в нём не наш хаб, а твой текст — так и задумано: свой файл мы не перезаписываем)"
        }
    }
}

# 2) settings.json: пути должны быть абсолютными, а файлы по ним — существовать
if (-not (Test-Path -LiteralPath $DstSettings)) {
    Write-Host "  [X] НЕТ $DstSettings — хуки, статус-строка и MCP не настроены." -ForegroundColor Red
    $verifyFailed = $true
} else {
    $sTxt = Get-Content -LiteralPath $DstSettings -Raw -ErrorAction SilentlyContinue
    if ($sTxt -and $sTxt.Contains('${HOME}')) {
        Write-Host "  [X] в settings.json остались пути через `${HOME}: на Windows это молча отключает" -ForegroundColor Red
        Write-Host "      защитный хук, статус-строку и MCP. Почини: .\install.ps1 -Repair"
        $verifyFailed = $true
    } else {
        Write-Host "  [ok] пути в settings.json абсолютные" -ForegroundColor Green
    }
    # Файлы, на которые settings.json ссылается: хуки, статус-строка, python-MCP.
    # Ищем по обеим формам записи каталога — со слэшами и с обратными слэшами.
    $refs = @()
    if ($sTxt) {
        # Три формы записи одного каталога: C:/Users/x, C:\Users\x и C:\\Users\\x (в JSON
        # обратный слэш экранируется). Искать только по одной — значит ничего не найти и
        # напечатать «проверено» ни по чему.
        $sep = '(?:/|\\{1,2})'
        foreach ($pfx in @($homeFwd, ($homeFwd -replace '/', '\'), ($homeFwd -replace '/', '\\'))) {
            $rx = [regex]::Escape($pfx) + $sep + '\.claude(?:' + $sep + '[^"\\]+)*\.(?:js|py)'
            foreach ($m in [regex]::Matches($sTxt, $rx)) { $refs += ($m.Value -replace '\\\\', '\') }
        }
        $refs = $refs | Sort-Object -Unique
    }
    $refMiss = 0
    foreach ($r in $refs) {
        if (Test-Path -LiteralPath $r) { continue }
        Write-Host "  [X] файл, на который ссылается settings.json, не найден: $r" -ForegroundColor Red
        $refMiss++
    }
    if ($refMiss -gt 0) {
        $verifyFailed = $true
    } elseif ($refs.Count -gt 0) {
        Write-Host "  [ok] файлы хуков/статус-строки/MCP на месте ($($refs.Count) шт.)" -ForegroundColor Green
    } else {
        # Ноль найденных путей — это не «всё хорошо», а «проверять было нечего».
        # Промолчать здесь значило бы выдать пустую проверку за пройденную.
        Write-Host "  [!] в settings.json не нашлось ни одной ссылки на файл внутри ~\.claude —" -ForegroundColor Yellow
        Write-Host "      проверять нечего. Если защитный хук и статус-строка нужны, сверь файл вручную."
    }
}

# 3) node: на нём написаны защитный хук и статус-строка
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
if ($nodeCmd) {
    Write-Host "  [ok] node есть ($($nodeCmd.Source))" -ForegroundColor Green
} else {
    Write-Host "  [!] node не найден в PATH — защитный хук guard.js и статус-строка не запустятся." -ForegroundColor Yellow
    Write-Host "      Поставь Node.js (nodejs.org). Остальной конфиг от этого не страдает."
}

# 4) bash: на нём написана ~1000 строк команд внутри навыков
# Тела навыков пишут POSIX-синтаксисом: 2>/dev/null, $(...), /tmp/..., фоновый & и nohup.
# В cmd.exe и PowerShell это не выполняется. Claude Code запускает такие команды через
# Git Bash — если его нет, отказ приходит НЕ здесь, а посреди работы навыка, и выглядит
# как поломка навыка, а не как отсутствие оболочки. Поэтому говорим сейчас.
$bashCmd = Get-Command bash -ErrorAction SilentlyContinue
if ($bashCmd) {
    Write-Host "  [ok] bash есть ($($bashCmd.Source))" -ForegroundColor Green
} else {
    Write-Host "  [!] bash не найден в PATH — POSIX-команды внутри навыков не выполнятся." -ForegroundColor Yellow
    Write-Host "      Это ~1000 строк в десятках навыков (2>/dev/null, `$(...), /tmp/..., фоновый &)."
    Write-Host "      Ставится вместе с Git for Windows:  winget install Git.Git"
    Write-Host "      После установки открой НОВЫЙ терминал — PATH подхватывается только там."
}

if ($verifyFailed) {
    Write-Host ""
    Write-Host "ПРОВЕРКА НЕ ПРОШЛА — см. строки со знаком [X] выше." -ForegroundColor Red
    Write-Host "  Файлы разложены, но в таком виде пак работает НЕ полностью."
}

# --- 8. Честный итог ---------------------------------------------------------------------
Write-Host ""
if ($copyFailed) {
    Write-Host "ГОТОВО НЕ ПОЛНОСТЬЮ: часть файлов скопировать не удалось (см. вывод выше)." -ForegroundColor Yellow
    Write-Host "  Твои ключи, память и история сессий НЕ тронуты — мы ничего не переносили и не стирали."
    Write-Host "  Можно запустить установку повторно после устранения причины."
} else {
    if ($Repair) { Write-Host "ГОТОВО: наши базовые файлы обновлены, пользовательские данные на месте." -ForegroundColor Green }
    else { Write-Host "ГОТОВО: добавлено недостающее, всё существующее сохранено." -ForegroundColor Green }
}
Write-Host "Сохранено без изменений: ключи (.credentials.*), MEMORY.md, memory\, projects\ (история сессий),"
Write-Host "  todos\, shell-snapshots\, chats.db*, tg_session.session*, settings.local.json, ~\.claude\CLAUDE.md."
if ($backupDir) { Write-Host "Резервная копия: $backupDir (храним 3 последние)." }
Write-Host "Откат: .\uninstall.ps1 — удалит только то, что положил этот установщик."
Write-Host "Дальше: заполни $DstClaude\rules\user-profile.md  ->  запусти 'claude'. API-ключи не требуются."
if ($copyFailed) { exit 1 }
# Проверка выше нашла неработающее — это не «предупреждение на всякий случай», а факт:
# хаб не читается или хук не запустится. Возвращаем ненулевой код, чтобы отказ было видно
# и человеку, и любому скрипту-обёртке.
if ($verifyFailed) { exit 1 }
exit 0
