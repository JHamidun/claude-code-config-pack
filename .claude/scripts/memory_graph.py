#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
memory_graph.py - Граф знаний памяти (Layer 1: из курированных заметок).

Превращает ~/.claude/projects/<proj>/memory/*.md в запрашиваемый граф:
- Узлы = заметки (id = frontmatter name или имя файла), типизированы (user/feedback/project/reference/memory).
- Рёбра = [[wikilinks]] (rel=link) + frontmatter supersedes/superseded_by (rel=supersedes, bi-temporal).
Хранилище = локальный SQLite ~/.claude/memory-graph/graph.db (часть памяти, офлайн, durable).

Команды:
  build                      пересобрать граф из заметок
  stats                      узлы/рёбра/типы/битые ссылки
  neighbors <name> [depth]   соседи узла (по умолч. depth=1)
  path <a> <b>               кратчайший путь между узлами (BFS)
  timeline <name>            цепочка supersedes (что считали верным и когда)
  hubs [N]                   топ-N самых связанных узлов
  orphans                    узлы без рёбер
  search <substr>            узлы по подстроке имени/заголовка
  dangling                   [[ссылки]] на несуществующие узлы (кандидаты на заметку)
  gaps [stale_days]          gap-анализ (паттерн gbrain, 0 LLM): orphans+dangling+stale-hubs+контра-детект
"""
import sqlite3, re, sys, os, glob
from pathlib import Path

HOME = Path.home()
MEM_DIRS = list((HOME / ".claude" / "projects").glob("*/memory"))
GRAPH_DIR = HOME / ".claude" / "memory-graph"
DB = GRAPH_DIR / "graph.db"

LINK_RE = re.compile(r"\[\[([^\]|]+)")           # [[name]] или [[name|alias]]
FM_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_note(path):
    """Вернуть (name, type, title, status, supersedes[list], links[list])."""
    txt = path.read_text(encoding="utf-8", errors="replace")
    name = path.stem
    ntype, title, status, supersedes = "memory", "", "active", []
    m = FM_RE.match(txt)
    body = txt
    if m:
        fm = m.group(1)
        body = txt[m.end():]
        nm = re.search(r"^name:\s*(.+)$", fm, re.M)
        if nm:
            name = nm.group(1).strip().strip('"\'')
        tm = re.search(r"^\s*type:\s*(.+)$", fm, re.M)
        if tm:
            ntype = tm.group(1).strip().split()[0].strip('"\'')
        sm = re.search(r"^\s*status:\s*(.+)$", fm, re.M)
        if sm:
            status = sm.group(1).strip().strip('"\'')
        dm = re.search(r"^description:\s*(.+)$", fm, re.M)
        if dm:
            title = dm.group(1).strip().strip('"\'>')[:200]
        # supersedes может быть [[id]] или список
        for sup in re.findall(r"supersede[sd_by]*:\s*\[?\[?([^\]\n]+)", fm):
            for tok in re.split(r"[,\s]+", sup):
                tok = tok.strip().strip('[]"\'')
                if tok and tok not in ("null", "none", "[]"):
                    supersedes.append(tok)
    # заголовок из первого H1 если нет description
    if not title:
        h = re.search(r"^#\s+(.+)$", body, re.M)
        if h:
            title = h.group(1).strip()[:200]
    links = [l.strip() for l in LINK_RE.findall(body)]
    return name, ntype, title, status, supersedes, links


def build():
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.executescript("""
        DROP TABLE IF EXISTS nodes; DROP TABLE IF EXISTS edges;
        CREATE TABLE nodes(name TEXT PRIMARY KEY, type TEXT, title TEXT, status TEXT, file TEXT, mtime REAL);
        CREATE TABLE edges(src TEXT, dst TEXT, rel TEXT);
        CREATE INDEX i_src ON edges(src); CREATE INDEX i_dst ON edges(dst);
    """)
    notes, edges = {}, []
    files = []
    for d in MEM_DIRS:
        files += glob.glob(str(d / "*.md"))
    # первый проход: распарсить все заметки и построить alias-карту (filename-слаг -> frontmatter name).
    # Узел индексируется по frontmatter name, но [[links]] ссылаются по имени файла — резолвим по обоим.
    parsed = []
    alias = {}
    for f in files:
        p = Path(f)
        if p.name in ("MEMORY.md",) or p.name.startswith("_"):
            # индекс и служебные (_ORPHANS_INDEX, _ops-archive) не как узлы, но их ссылки учтём отдельно
            pass
        name, ntype, title, status, sup, links = parse_note(p)
        parsed.append((p, name, ntype, title, status, sup, links))
        notes[name] = (ntype, title, status, str(p), p.stat().st_mtime)
        alias.setdefault(p.stem, name)  # слаг -> канон-имя узла
        alias.setdefault(name, name)    # имя -> само
    # второй проход: рёбра с резолвом цели по alias (слаг ИЛИ frontmatter name -> канон-имя узла)
    for p, name, ntype, title, status, sup, links in parsed:
        for l in links:
            edges.append((name, alias.get(l, l), "link"))
        for s in sup:
            edges.append((name, alias.get(s, s), "supersedes"))
    for name, (ntype, title, status, file, mt) in notes.items():
        con.execute("INSERT OR REPLACE INTO nodes VALUES(?,?,?,?,?,?)", (name, ntype, title, status, file, mt))
    con.executemany("INSERT INTO edges VALUES(?,?,?)", edges)
    cb_n, cb_e = _ingest_casebook(con)
    link_e = _link_notes_to_projects(con)
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    e = con.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
    dangling = con.execute("SELECT COUNT(DISTINCT dst) FROM edges WHERE dst NOT IN (SELECT name FROM nodes)").fetchone()[0]
    con.close()
    print(f"[build] nodes={n} edges={e} dangling_targets={dangling}  (+casebook {cb_n}n/{cb_e}e, +L1-L2 links {link_e})  db={DB}")


def _link_notes_to_projects(con):
    """L1↔L2: связать заметки с proj-узлами по ДИСТИНКТИВНЫМ ключам в имени-слаге заметки (rel=about).
    Строго: ключ ≥5 симв, не общий (в ≤4 проектах), матч по name (не title), кап 3/заметку — иначе over-link."""
    import re
    from collections import Counter
    STOP = {"crm", "agent", "app", "site", "web", "api", "bot", "prod", "proj", "team", "test",
            "demo", "page", "user", "data", "flow", "docs", "auto", "tool", "yourname", "company",
            "система", "проект", "бот", "агент", "сайт", "лендинг", "review", "audit", "setup", "deploy"}
    raw = []
    kw_freq = Counter()
    for (name,) in con.execute("SELECT name FROM nodes WHERE name LIKE 'proj:%'"):
        label = name[5:].lower()
        kws = {w for w in re.split(r"[\s/()\[\].,_+-]+", label) if len(w) >= 5 and w not in STOP}
        raw.append((name, kws))
        for w in kws:
            kw_freq[w] += 1
    # оставить только дистинктивные ключи (встречаются в ≤4 проектах)
    projs = [(name, {w for w in kws if kw_freq[w] <= 4}) for name, kws in raw]
    projs = [(n, k) for n, k in projs if k]
    notes = con.execute(
        "SELECT name FROM nodes WHERE name NOT LIKE 'proj:%' AND name NOT LIKE 'case:%' "
        "AND name NOT LIKE 'person:%' AND name NOT LIKE 'company:%' AND name NOT LIKE 'tool:%'").fetchall()
    edges = 0
    for (nname,) in notes:
        slug = nname.lower()
        hits = [pname for pname, kws in projs if any(k in slug for k in kws)]
        for pname in hits[:3]:  # кап 3 самых на заметку
            con.execute("INSERT INTO edges VALUES(?,?,?)", (nname, pname, "about"))
            edges += 1
    return edges


CASEBOOK = HOME / "_casebook"
CANON = CASEBOOK / "canon"
_MAPS = {}


def _load_maps():
    import json
    for kind, fn in (("project", "project_map.json"), ("person", "person_map.json"),
                     ("company", "company_map.json"), ("tool", "tool_map.json")):
        p = CANON / fn
        try:
            _MAPS[kind] = json.load(open(p, encoding="utf-8")) if p.exists() else {}
        except Exception:
            _MAPS[kind] = {}


def canon(kind, name):
    """Нормализовать имя через канон-карту (вариант→канон). Незамапленное → само; пустой канон → '' (дроп)."""
    name = (str(name) if name is not None else "").strip()
    return _MAPS.get(kind, {}).get(name, name)


def _ingest_casebook(con):
    """Влить _casebook (Layer 2): карточки→case-узлы, clusters/project→project-узлы, +сущности (люди/компании/инструменты).
    Источники: all_cards_v2.json (исходный кейсбук 856) + cards_db/*.json (догон из chats.db, богаче — с сущностями).
    Layer 2 переиспользует прошлую масс-экстракцию (761127d1/9182c0aa) + догон дыры покрытия, а не гонит LLM с нуля."""
    import json, glob
    _load_maps()
    nodes, edges = 0, 0
    cards = []
    f = CASEBOOK / "all_cards_v2.json"
    if f.exists():
        try:
            d = json.load(open(f, encoding="utf-8"))
            cards = d if isinstance(d, list) else (d.get("cards") or list(d.values()))
        except Exception:
            cards = []
    # догон-карточки (chats.db, с сущностями) — перекрывают дубли по session_id
    for cf in glob.glob(str(CASEBOOK / "cards_db" / "*.json")):
        try:
            c = json.load(open(cf, encoding="utf-8"))
        except Exception:
            continue
        if isinstance(c, dict) and c.get("session_id"):
            sid = str(c.get("session_id"))
            cards = [x for x in cards if str(x.get("session_id")) != sid]
            cards.append(c)

    def ent(kind, val, sid, rel):
        nonlocal nodes, edges
        val = (str(val) if val is not None else "").strip().strip('"\'')
        val = canon(kind, val)  # нормализация вариант→канон (пусто → дроп)
        if not val or len(val) > 80 or val.lower() in ("", "none", "unknown", "n/a", "-", "неизвестно"):
            return
        nid = f"{kind}:{val}"
        con.execute("INSERT OR IGNORE INTO nodes VALUES(?,?,?,?,?,?)", (nid, kind, val, "", "", 0))
        con.execute("INSERT INTO edges VALUES(?,?,?)", (f"case:{sid}", nid, rel))
        edges += 1

    for c in cards:
        if not isinstance(c, dict) or not c.get("is_real_case", True):
            continue
        sid = c.get("session_id")
        if not sid:
            continue
        title = f"{c.get('date','')} [{c.get('project','')}] {c.get('title','')}".strip()[:200]
        con.execute("INSERT OR REPLACE INTO nodes VALUES(?,?,?,?,?,?)",
                    (f"case:{sid}", "case", title, c.get("category", ""), c.get("jsonl_path", ""), 0))
        nodes += 1
        proj = canon("project", c.get("project"))
        if proj:
            con.execute("INSERT OR IGNORE INTO nodes VALUES(?,?,?,?,?,?)", (f"proj:{proj}", "project-cluster", str(proj)[:200], "", "", 0))
            con.execute("INSERT INTO edges VALUES(?,?,?)", (f"case:{sid}", f"proj:{proj}", "in_project"))
            edges += 1
        # сущности — ТОЛЬКО если поле список (догон-карточки; у старого кейсбука stack=строка → пропуск)
        def as_list(v):
            return v if isinstance(v, list) else []
        for p in as_list(c.get("people")):
            ent("person", p, sid, "involves")
        for co in as_list(c.get("companies")):
            ent("company", co, sid, "for_company")
        for t in as_list(c.get("tools")):
            ent("tool", t, sid, "uses")
        for s in as_list(c.get("stack")):
            ent("tool", s, sid, "uses")
    # энричмент сущностей старых карточек (entities_v1/*.json — supplements к 856 без своих people/tools)
    for ef in glob.glob(str(CASEBOOK / "entities_v1" / "*.json")):
        try:
            e = json.load(open(ef, encoding="utf-8"))
        except Exception:
            continue
        esid = str(e.get("session_id", "")) if isinstance(e, dict) else ""
        if not esid or not con.execute("SELECT 1 FROM nodes WHERE name=?", (f"case:{esid}",)).fetchone():
            continue
        for p in (e.get("people") or []):
            ent("person", p, esid, "involves")
        for co in (e.get("companies") or []):
            ent("company", co, esid, "for_company")
        for t in (e.get("tools") or []):
            ent("tool", t, esid, "uses")
    # clusters.json — канонический роллап
    cl_f = CASEBOOK / "clusters.json"
    if cl_f.exists():
        try:
            cl = json.load(open(cl_f, encoding="utf-8"))
            for cluster0, sids in (cl.items() if isinstance(cl, dict) else []):
                cluster = canon("project", cluster0)
                if not cluster:
                    continue
                con.execute("INSERT OR IGNORE INTO nodes VALUES(?,?,?,?,?,?)",
                            (f"proj:{cluster}", "project-cluster", str(cluster)[:200], "", "", 0))
                for sid in sids:
                    if con.execute("SELECT 1 FROM nodes WHERE name=?", (f"case:{sid}",)).fetchone():
                        con.execute("INSERT INTO edges VALUES(?,?,?)", (f"case:{sid}", f"proj:{cluster}", "in_cluster"))
                        edges += 1
        except Exception:
            pass
    return nodes, edges


def cases(sub):
    """Список кейсов (сессий) по проекту/подстроке."""
    con = _con()
    rows = con.execute("""
        SELECT n.name, n.title FROM nodes n
        WHERE n.type='case' AND (n.title LIKE ? OR n.name IN (
            SELECT src FROM edges WHERE dst LIKE ? ))
        ORDER BY n.title DESC LIMIT 60""", (f"%{sub}%", f"proj:%{sub}%")).fetchall()
    for name, title in rows:
        print(f"  {title[:100]}  [{name}]")
    print(f"  -- {len(rows)} кейсов")


def _con():
    if not DB.exists():
        print("graph not built yet -> run: python memory_graph.py build"); sys.exit(1)
    return sqlite3.connect(DB)


def stats():
    con = _con()
    n = con.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
    e = con.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
    print(f"nodes={n} edges={e}")
    print("by type:", dict(con.execute("SELECT type,COUNT(*) FROM nodes GROUP BY type ORDER BY 2 DESC").fetchall()))
    print("by rel :", dict(con.execute("SELECT rel,COUNT(*) FROM edges GROUP BY rel").fetchall()))
    orph = con.execute("SELECT COUNT(*) FROM nodes WHERE name NOT IN (SELECT src FROM edges UNION SELECT dst FROM edges)").fetchone()[0]
    dang = con.execute("SELECT COUNT(DISTINCT dst) FROM edges WHERE dst NOT IN (SELECT name FROM nodes)").fetchone()[0]
    print(f"orphans={orph} dangling_link_targets={dang}")


def neighbors(name, depth=1):
    con = _con()
    seen = {name}; frontier = {name}
    for d in range(int(depth)):
        nxt = set()
        for nd in frontier:
            for src, dst, rel in con.execute("SELECT src,dst,rel FROM edges WHERE src=? OR dst=?", (nd, nd)):
                other = dst if src == nd else src
                if other not in seen:
                    t = con.execute("SELECT title FROM nodes WHERE name=?", (other,)).fetchone()
                    tag = "" if t else "  (нет заметки)"
                    print(f"  d{d+1} {nd} --{rel}--> {other}{tag}")
                    nxt.add(other); seen.add(other)
        frontier = nxt
    if len(seen) == 1:
        print(f"  '{name}': нет связей (или узел не найден)")


def path(a, b):
    con = _con()
    adj = {}
    for src, dst in con.execute("SELECT src,dst FROM edges"):
        adj.setdefault(src, set()).add(dst); adj.setdefault(dst, set()).add(src)
    from collections import deque
    q = deque([[a]]); seen = {a}
    while q:
        p = q.popleft()
        if p[-1] == b:
            print(" -> ".join(p)); return
        for nb in adj.get(p[-1], ()):
            if nb not in seen:
                seen.add(nb); q.append(p + [nb])
    print(f"нет пути {a} .. {b}")


def timeline(name):
    con = _con()
    # цепочка supersedes: что этот узел заместил, и что заместило его
    print(f"[{name}] замещает (supersedes ->):")
    for _, dst, _ in con.execute("SELECT src,dst,rel FROM edges WHERE src=? AND rel='supersedes'", (name,)):
        print(f"   -> {dst}")
    print(f"[{name}] замещён кем (<- supersedes):")
    for src, _, _ in con.execute("SELECT src,dst,rel FROM edges WHERE dst=? AND rel='supersedes'", (name,)):
        print(f"   <- {src}")


def hubs(n=15):
    con = _con()
    rows = con.execute("""
        SELECT name, (SELECT COUNT(*) FROM edges WHERE src=name OR dst=name) deg
        FROM nodes ORDER BY deg DESC LIMIT ?""", (int(n),)).fetchall()
    for name, deg in rows:
        print(f"  {deg:3d}  {name}")


def orphans():
    con = _con()
    for (name,) in con.execute("SELECT name FROM nodes WHERE name NOT IN (SELECT src FROM edges UNION SELECT dst FROM edges) ORDER BY name"):
        print(" ", name)


def search(sub):
    con = _con()
    for name, title in con.execute("SELECT name,title FROM nodes WHERE name LIKE ? OR title LIKE ? LIMIT 40", (f"%{sub}%", f"%{sub}%")):
        print(f"  {name}  -- {title[:80]}")


def dangling():
    con = _con()
    rows = con.execute("""
        SELECT dst, COUNT(*) c FROM edges WHERE dst NOT IN (SELECT name FROM nodes)
        GROUP BY dst ORDER BY c DESC LIMIT 40""").fetchall()
    for dst, c in rows:
        print(f"  x{c}  [[{dst}]]  (ссылаются, но заметки нет -> кандидат)")


def gaps(*args):
    """Gap-анализ графа (паттерн gbrain, БЕЗ LLM): чего память НЕ знает / где дыры.
    4 секции gbrain-таксономии на нашем SQLite: orphans, dangling, stale-hubs, superseded-unmarked.
    Аргумент: [stale_days] — порог устаревания хабов (по умолч. 45)."""
    import time
    con = _con()
    stale_days = int(args[0]) if args else 45
    now = time.time()
    cutoff = now - stale_days * 86400

    # 1. ORPHANS — заметки (mtime>0) без единого ребра: не вплетены в граф
    orph = con.execute(
        "SELECT name FROM nodes WHERE mtime>0 AND name NOT IN "
        "(SELECT src FROM edges UNION SELECT dst FROM edges) ORDER BY name").fetchall()
    print(f"== ORPHANS (заметки без связей: {len(orph)}) — кандидаты на [[link]] ==")
    for (name,) in orph[:30]:
        print("  ", name)

    # 2. DANGLING — [[link]] на несуществующий узел: дыра покрытия (кандидат создать)
    dang = con.execute(
        "SELECT dst, COUNT(*) c FROM edges WHERE rel='link' AND dst NOT IN (SELECT name FROM nodes) "
        "GROUP BY dst ORDER BY c DESC LIMIT 25").fetchall()
    print(f"\n== DANGLING (ссылаются, заметки нет: top {len(dang)}) — кандидаты создать ==")
    for dst, c in dang:
        print(f"  x{c}  [[{dst}]]")

    # 3. STALE HUBS — высокая степень + старый mtime: вероятный дрейф/противоречие с кодом
    hub_rows = con.execute(
        "SELECT name, mtime, (SELECT COUNT(*) FROM edges WHERE src=name OR dst=name) deg "
        "FROM nodes WHERE mtime>0 AND mtime<? ORDER BY deg DESC LIMIT 15", (cutoff,)).fetchall()
    print(f"\n== STALE HUBS (deg высокий, не трогали >{stale_days}д: {len(hub_rows)}) — проверить на дрейф ==")
    for name, mt, deg in hub_rows:
        age = int((now - mt) / 86400)
        print(f"  deg{deg:>3} {age:>4}д  {name}")

    # 4. SUPERSEDED-UNMARKED — узел замещён (цель supersedes-ребра), но status не superseded: bi-temporal контра
    contra = con.execute(
        "SELECT DISTINCT e.dst, n.status FROM edges e JOIN nodes n ON n.name=e.dst "
        "WHERE e.rel='supersedes' AND n.mtime>0 AND "
        "(n.status IS NULL OR n.status='' OR LOWER(n.status) NOT LIKE '%supersed%')").fetchall()
    print(f"\n== SUPERSEDED-UNMARKED (замещён, но status активен: {len(contra)}) — противоречие (эвристика) ==")
    for dst, st in contra[:20]:
        print(f"  {dst}  [status={st or 'none'}]")

    print(f"\n[gaps] orphans={len(orph)} dangling={len(dang)} stale_hubs={len(hub_rows)} contra={len(contra)}  (порог stale={stale_days}д)")


if __name__ == "__main__":
    try:  # cp1251-консоль Windows крашит на не-ASCII (→, ⭐) — ставим UTF-8 один раз ДО диспетчеризации
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"
    args = sys.argv[2:]
    if cmd in ("-h", "--help", "help"):
        print(__doc__); sys.exit(0)
    fn = {"build": build, "stats": stats, "neighbors": neighbors, "path": path,
          "timeline": timeline, "hubs": hubs, "orphans": orphans, "search": search,
          "dangling": dangling, "cases": cases, "gaps": gaps}.get(cmd)
    if not fn:
        print(__doc__); sys.exit(1)
    fn(*args)
