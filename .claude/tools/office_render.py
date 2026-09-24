#!/usr/bin/env python
"""Render DOCX/PPTX/XLSX to PDF through installed Microsoft Office (COM), then to PNG pages.

Windows with Microsoft Office only. An alternative to the LibreOffice (soffice) render
step of the docx/pptx/xlsx skills that needs no LibreOffice. Requires pywin32 and
psutil (pip) and Poppler's pdftoppm (PATH or the PDFTOPPM variable).

    python office_render.py <file> --out <dir> [--dpi 110] [--first N] [--timeout 180]

Prints one JSON object to stdout: {"pdf": ..., "pngs": [...], "app": ..., "seconds": ...}.
On failure: {"error": ..., "app": ...} and a non-zero exit code
(1 render error, 2 bad input, 3 timeout).

Safety:
- a separate Office instance is started with DispatchEx; the file is opened read-only,
  macros are disabled (AutomationSecurity = force disable), alerts are off;
- Close/Quit always run in `finally`;
- a watchdog kills a hung render after --timeout, but only the Office process this
  script started: the new WINWORD/POWERPNT/EXCEL process with `-Embedding` in its
  command line that did not exist before dispatch. PowerPoint is single-instance: if
  the user already has it open, DispatchEx attaches to that instance, and then the
  script neither quits nor kills it and restores the settings it changed. The same holds
  when the user opens PowerPoint while the render runs: their window lands in our process.
- a server still starting when the timer fires is looked for again before the script
  exits, so a cold Word launch does not outlive a timeout;
- Office opens a private copy of the file under %LOCALAPPDATA%\\office_render: after a
  killed render Office asks "a serious error occurred the last time ... open it anyway?"
  on the next open of the same path, which would hang every later render of that file.
"""
import argparse
import gc
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import winreg

import psutil
import pythoncom
import pywintypes
import win32com.client
import win32gui
import win32process

# pdftoppm (Poppler) is taken from PATH, or from the full path in the PDFTOPPM variable.
POPPLER_FALLBACK = os.environ.get("PDFTOPPM", "")
MSO_AUTOMATION_SECURITY_FORCE_DISABLE = 3
WD_EXPORT_FORMAT_PDF = 17
WD_DO_NOT_SAVE_CHANGES = 0
PP_SAVE_AS_PDF = 32
PP_FIXED_FORMAT_TYPE_PDF = 2
XL_TYPE_PDF = 0
# Dummy password: a protected file then fails fast instead of waiting on a prompt.
NO_PASSWORD = "__office_render_no_password__"
# After the grace period the watchdog keeps looking this long for a server that was still
# starting when the timer fired, so it does not outlive the script.
LATE_SERVER_WAIT = 30
# Office opens a private copy under here (see main); stable, unlike TEMP, across shells.
WORK_ROOT = os.path.join(os.environ.get("LOCALAPPDATA") or tempfile.gettempdir(), "office_render")
REG_APP = {"word": "Word", "powerpoint": "PowerPoint", "excel": "Excel"}

APPS = {
    "word": {"progid": "Word.Application", "image": "WINWORD.EXE",
             "ext": {".docx", ".doc", ".docm", ".dotx", ".rtf", ".odt"}},
    "powerpoint": {"progid": "PowerPoint.Application", "image": "POWERPNT.EXE",
                   "ext": {".pptx", ".ppt", ".pptm", ".potx", ".ppsx", ".odp"}},
    "excel": {"progid": "Excel.Application", "image": "EXCEL.EXE",
              "ext": {".xlsx", ".xls", ".xlsm", ".xltx", ".csv", ".ods"}},
}

_emit_lock = threading.Lock()
_emitted = False
_emit_code = None
_work_dir = None  # this run's private copy; the watchdog removes it before os._exit


def log(msg):
    print(f"[office_render] {msg}", file=sys.stderr, flush=True)


def emit(obj, code):
    """Print the single JSON result once; later calls print nothing and return the first code."""
    global _emitted, _emit_code
    with _emit_lock:
        if _emitted:
            return _emit_code
        _emitted, _emit_code = True, code
        print(json.dumps(obj, ensure_ascii=False), flush=True)
    return code


def pids_of(image):
    image = image.lower()
    out = set()
    for p in psutil.process_iter(["pid", "name"]):
        if (p.info["name"] or "").lower() == image:
            out.add(p.info["pid"])
    return out


def new_com_servers(image, before):
    """PIDs of `image` processes that appeared after `before` and run as a COM server."""
    found = []
    for pid in pids_of(image) - before:
        try:
            cmd = " ".join(psutil.Process(pid).cmdline()).lower()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        if "-embedding" in cmd:
            found.append(pid)
    return found


def pid_from_hwnd(hwnd):
    try:
        return win32process.GetWindowThreadProcessId(int(hwnd))[1]
    except (pywintypes.error, TypeError, ValueError):
        return None


def private_copy(src):
    """Copy `src` to a fresh directory under WORK_ROOT and return (copy path, directory).

    When a render is killed with a file open, Office remembers that path and, the next time the
    path is opened, asks "a serious error occurred the last time ... open it anyway?" — a modal
    prompt that hangs every later render of the same file until someone clicks it. A copy under
    a new directory never reuses a path, so the prompt never matches.
    """
    os.makedirs(WORK_ROOT, exist_ok=True)
    cutoff = time.time() - 3600
    for name in os.listdir(WORK_ROOT):  # leftovers of runs that ended in os._exit
        old = os.path.join(WORK_ROOT, name)
        if os.path.isdir(old) and os.path.getmtime(old) < cutoff:
            shutil.rmtree(old, ignore_errors=True)
    work = tempfile.mkdtemp(dir=WORK_ROOT)
    copy = os.path.join(work, os.path.basename(src))
    shutil.copyfile(src, copy)
    return copy, work


def _ours(value, root):
    """Does a Resiliency record (type, path size, name size, UTF-16 path, ...) name a path in root?"""
    if not isinstance(value, bytes) or len(value) <= 12:
        return False
    size = int.from_bytes(value[4:8], "little")
    item = value[12:12 + size].decode("utf-16-le", "ignore").rstrip("\0")
    return os.path.normcase(item).startswith(root)


def _values(key):
    i = 0
    while True:
        try:
            yield winreg.EnumValue(key, i)
        except OSError:
            return
        i += 1


def prune_crash_records(app_name):
    """Delete Office's crash records that point into WORK_ROOT (HKCU ...\\Resiliency).

    After a killed render Office files the open copy under DisabledItems (a value) and
    DocumentRecovery (a subkey). They only ever name our own copies, which are gone, and
    would otherwise pile up, e.g. in File > Options > Add-ins > Disabled Items. Records
    for any other path are left alone.
    """
    base = rf"Software\Microsoft\Office\16.0\{REG_APP[app_name]}\Resiliency"
    root = os.path.normcase(WORK_ROOT)
    access = winreg.KEY_READ | winreg.KEY_SET_VALUE
    removed = 0
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, base + r"\DisabledItems", 0, access) as key:
            for name in [n for n, v, _ in _values(key) if _ours(v, root)]:
                winreg.DeleteValue(key, name)
                removed += 1
    except OSError:
        pass
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, base + r"\DocumentRecovery", 0, access) as key:
            subs = []
            for i in range(winreg.QueryInfoKey(key)[0]):
                subs.append(winreg.EnumKey(key, i))
            for sub in subs:
                with winreg.OpenKey(key, sub) as child:
                    vals = [v for _, v, _ in _values(child)]
                    leaf = winreg.QueryInfoKey(child)[0] == 0
                if leaf and vals and all(_ours(v, root) for v in vals):
                    winreg.DeleteKey(key, sub)
                    removed += 1
    except OSError:
        pass
    if removed:
        log(f"removed {removed} {REG_APP[app_name]} crash record(s) of earlier killed renders")


def has_user_frame(pid):
    """True if `pid` shows a visible PowerPoint main window. PowerPoint is single-instance: a
    window the user opens while we render lands in our process, which is then theirs too."""
    found = []

    def check(hwnd, _):
        if (win32gui.IsWindowVisible(hwnd) and win32gui.GetClassName(hwnd) == "PPTFrameClass"
                and pid_from_hwnd(hwnd) == pid):
            found.append(hwnd)
        return True

    try:
        win32gui.EnumWindows(check, None)
    except pywintypes.error:
        return True  # cannot tell: do not kill
    return bool(found)


class Watchdog(threading.Thread):
    """Kill our own COM server if the render does not finish in time."""

    def __init__(self, app, image, before, timeout, grace=15):
        super().__init__(daemon=True)
        self.app, self.image, self.before = app, image, before
        self.timeout, self.grace = timeout, grace
        self.own_pid = None  # set by the main thread once identified
        self.shared = False  # attached to a pre-existing instance: never kill
        self.fired = False
        self._done = threading.Event()

    def stop(self):
        self._done.set()

    def _find_own(self):
        """(PID of our server or None, ambiguous?). None also while the server is still starting."""
        if self.own_pid is not None:
            return self.own_pid, False
        candidates = new_com_servers(self.image, self.before)
        return (candidates[0] if len(candidates) == 1 else None), len(candidates) > 1

    def _kill(self, pid):
        if self.image == "POWERPNT.EXE" and has_user_frame(pid):
            log(f"{self.image} PID {pid} now also shows the user's PowerPoint window; not killing it")
            return None
        try:
            psutil.Process(pid).kill()
            log(f"timeout after {self.timeout}s: killed own {self.image} PID {pid}")
        except psutil.NoSuchProcess:
            pass
        return pid

    def _try_kill(self):
        """True once the question is settled: killed, or must not kill (ambiguous / user's)."""
        pid, ambiguous = self._find_own()
        if ambiguous:
            log(f"timeout: several new {self.image} servers, cannot tell which is ours; not killing")
            return True, None
        if pid is None:
            return False, None
        return True, self._kill(pid)

    def run(self):
        if self._done.wait(self.timeout):
            return
        self.fired = True
        settled, killed = (True, None) if self.shared else self._try_kill()
        if self.shared:
            log(f"timeout after {self.timeout}s in a shared {self.image} instance; not killing it")
        if self._done.wait(self.grace):
            return
        # The main thread is still stuck in a COM call. A server that was still starting when the
        # timer fired (cold Word, tiny --timeout) shows up only now: kill it before exiting, or it
        # outlives the script.
        deadline = time.monotonic() + LATE_SERVER_WAIT
        while not settled and time.monotonic() < deadline and not self._done.is_set():
            settled, killed = self._try_kill()
            if not settled:
                time.sleep(1)
        if self._done.is_set():
            return
        emit({"error": f"timeout after {self.timeout}s", "app": self.app, "killed_pid": killed}, 3)
        if _work_dir:  # os._exit skips main's cleanup; the copy is the user's document
            shutil.rmtree(_work_dir, ignore_errors=True)
        os._exit(3)


def wait_exit_or_kill(pid, image, seconds=20):
    try:
        proc = psutil.Process(pid)
        proc.wait(timeout=seconds)
    except psutil.NoSuchProcess:
        return
    except psutil.TimeoutExpired:
        log(f"{image} PID {pid} still alive {seconds}s after Quit; killing own process")
        try:
            proc.kill()
        except psutil.NoSuchProcess:
            pass


def export_word(app, src, pdf):
    app.Visible = False
    app.DisplayAlerts = 0
    app.AutomationSecurity = MSO_AUTOMATION_SECURITY_FORCE_DISABLE
    doc = app.Documents.Open(src, ConfirmConversions=False, ReadOnly=True,
                             AddToRecentFiles=False, PasswordDocument=NO_PASSWORD,
                             Visible=False, NoEncodingDialog=True)
    try:
        doc.ExportAsFixedFormat(pdf, WD_EXPORT_FORMAT_PDF)
    finally:
        doc.Close(WD_DO_NOT_SAVE_CHANGES)


def export_powerpoint(app, src, pdf):
    # The instance may be the user's (single-instance PowerPoint): put their settings back.
    prev = (app.DisplayAlerts, app.AutomationSecurity)
    app.DisplayAlerts = 1  # ppAlertsNone
    app.AutomationSecurity = MSO_AUTOMATION_SECURITY_FORCE_DISABLE
    try:
        pres = app.Presentations.Open(src, ReadOnly=True, Untitled=False, WithWindow=False)
        try:
            try:
                pres.SaveAs(pdf, PP_SAVE_AS_PDF)
            except pywintypes.com_error as e:
                log(f"SaveAs PDF failed ({e.args[1] if len(e.args) > 1 else e}); trying ExportAsFixedFormat")
                pres.ExportAsFixedFormat(pdf, PP_FIXED_FORMAT_TYPE_PDF)
        finally:
            pres.Close()
    finally:
        try:
            app.DisplayAlerts, app.AutomationSecurity = prev
        except pywintypes.com_error:
            pass


def export_excel(app, src, pdf):
    app.Visible = False
    app.DisplayAlerts = False
    app.AskToUpdateLinks = False
    app.AutomationSecurity = MSO_AUTOMATION_SECURITY_FORCE_DISABLE
    wb = app.Workbooks.Open(src, UpdateLinks=0, ReadOnly=True, Password=NO_PASSWORD,
                            IgnoreReadOnlyRecommended=True, AddToMru=False)
    try:
        wb.ExportAsFixedFormat(XL_TYPE_PDF, pdf)
    finally:
        wb.Close(SaveChanges=False)


EXPORTERS = {"word": export_word, "powerpoint": export_powerpoint, "excel": export_excel}


def render_pdf(app_name, src, pdf, timeout):
    spec = APPS[app_name]
    image = spec["image"]
    before = pids_of(image)
    dog = Watchdog(app_name, image, before, timeout)
    dog.start()
    app = None
    own_pid = None
    pythoncom.CoInitialize()
    try:
        app = win32com.client.DispatchEx(spec["progid"])
        new = new_com_servers(image, before)
        hwnd_pid = None
        if app_name in ("excel", "powerpoint"):
            try:
                hwnd_pid = pid_from_hwnd(app.Hwnd if app_name == "excel" else app.HWND)
            except pywintypes.com_error:
                hwnd_pid = None
        if hwnd_pid is not None and hwnd_pid in before:
            dog.shared = True
        elif hwnd_pid is not None and hwnd_pid in new:
            own_pid = hwnd_pid
        elif len(new) == 1:
            own_pid = new[0]
        elif not new and before:
            dog.shared = True
        dog.own_pid = own_pid
        log(f"{image}: own PID {own_pid}" if own_pid else
            f"{image}: attached to an existing instance, will not quit it" if dog.shared else
            f"{image}: could not identify own PID (new servers: {new}); watchdog will not kill")
        EXPORTERS[app_name](app, src, pdf)
    except (pywintypes.com_error, AttributeError) as e:
        # A killed server surfaces as com_error, or as AttributeError from late-bound dispatch.
        if dog.fired:  # the watchdog killed the server under a blocked call
            raise TimeoutError(f"timeout after {timeout}s") from e
        if isinstance(e, AttributeError):
            raise RuntimeError(f"{image} stopped responding ({e})") from e
        raise
    finally:
        joined = False
        if app is not None and app_name == "powerpoint" and not dog.shared:
            # A window the user opened during the render lands in our single-instance process:
            # quitting or killing it would take their presentations down.
            try:
                joined = app.Presentations.Count > 0 or bool(app.Visible)
            except (pywintypes.com_error, AttributeError):  # AttributeError: server already dead
                joined = own_pid is not None and psutil.pid_exists(own_pid) and has_user_frame(own_pid)
            if joined:
                log("the user opened PowerPoint during the render; leaving that instance running")
        if app is not None and not dog.shared and not joined:
            try:
                if app_name == "word":
                    app.Quit(WD_DO_NOT_SAVE_CHANGES)
                else:
                    app.Quit()
            except (pywintypes.com_error, AttributeError):  # server already dead or gone
                pass
        app = None
        gc.collect()
        pythoncom.CoUninitialize()
        if own_pid is not None and not joined:
            wait_exit_or_kill(own_pid, image)
        dog.stop()
    if dog.fired:
        raise TimeoutError(f"timeout after {timeout}s")


def find_pdftoppm():
    exe = shutil.which("pdftoppm")
    if exe:
        return exe
    if POPPLER_FALLBACK and os.path.isfile(POPPLER_FALLBACK):
        return POPPLER_FALLBACK
    raise FileNotFoundError("pdftoppm not found: install Poppler (winget install oschwartz10612.Poppler) "
                            "and open a new terminal, or set PDFTOPPM to the full path of pdftoppm.exe")


def render_pngs(pdf, out_dir, stem, dpi, first, timeout):
    prefix = os.path.join(out_dir, stem)
    cmd = [find_pdftoppm(), "-png", "-r", str(dpi)]
    if first:
        cmd += ["-f", "1", "-l", str(first)]
    started = time.time()
    subprocess.run(cmd + [pdf, prefix], check=True, capture_output=True, timeout=timeout)
    pattern = re.compile(re.escape(stem) + r"-(\d+)\.png$")
    pages = []
    for name in os.listdir(out_dir):
        m = pattern.match(name)
        path = os.path.join(out_dir, name)
        # Only files written by this run: older renders of the same stem stay untouched.
        if m and os.path.getmtime(path) >= started - 1:
            pages.append((int(m.group(1)), path))
    return [p for _, p in sorted(pages)]


def main(argv=None):
    global _work_dir
    ap = argparse.ArgumentParser(description="Render DOCX/PPTX/XLSX to PDF via Office COM, then PNG via pdftoppm.")
    ap.add_argument("file")
    ap.add_argument("--out", required=True, help="output directory (created if missing)")
    ap.add_argument("--dpi", type=int, default=110)
    ap.add_argument("--first", type=int, default=0, help="render only the first N pages to PNG")
    ap.add_argument("--timeout", type=int, default=180,
                    help="seconds for the Office part (cold start of Word can exceed 60 s)")
    args = ap.parse_args(argv)

    src = os.path.abspath(args.file)
    ext = os.path.splitext(src)[1].lower()
    app_name = next((name for name, spec in APPS.items() if ext in spec["ext"]), None)
    if not os.path.isfile(src):
        return emit({"error": f"file not found: {src}"}, 2)
    if app_name is None:
        return emit({"error": f"unsupported extension: {ext}"}, 2)
    if args.timeout < 1:
        return emit({"error": "--timeout must be at least 1 second"}, 2)
    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)
    # The source type is part of the name: report.docx and report.xlsx rendered into one --out
    # must not overwrite each other's PDF and pages.
    stem = os.path.splitext(os.path.basename(src))[0] + "-" + ext.lstrip(".")
    pdf = os.path.join(out_dir, stem + ".pdf")

    started = time.time()
    work = None
    try:
        copy, work = private_copy(src)
        _work_dir = work
        render_pdf(app_name, copy, pdf, args.timeout)
        if not os.path.isfile(pdf) or os.path.getmtime(pdf) < started - 1:
            raise RuntimeError("Office reported success but no fresh PDF was written")
        pngs = render_pngs(pdf, out_dir, stem, args.dpi, args.first, max(60, args.timeout))
    except TimeoutError as e:
        return emit({"error": str(e), "app": app_name}, 3)
    except pywintypes.com_error as e:
        detail = e.excepinfo[2] if e.excepinfo and len(e.excepinfo) > 2 and e.excepinfo[2] else str(e)
        return emit({"error": f"COM error: {detail}", "app": app_name}, 1)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        stderr = getattr(e, "stderr", b"") or b""
        return emit({"error": f"pdftoppm failed: {e} {stderr.decode(errors='replace')[:300]}",
                     "app": app_name, "pdf": pdf}, 1)
    except (RuntimeError, FileNotFoundError, OSError) as e:
        return emit({"error": str(e), "app": app_name}, 1)
    finally:
        if work:
            shutil.rmtree(work, ignore_errors=True)
        prune_crash_records(app_name)
    return emit({"pdf": pdf, "pngs": pngs, "app": app_name,
                 "seconds": round(time.time() - started, 1)}, 0)


if __name__ == "__main__":
    sys.exit(main())
