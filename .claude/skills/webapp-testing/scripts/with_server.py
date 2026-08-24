#!/usr/bin/env python3
"""
Start one or more servers, wait for them to be ready, run a command, then clean up.

Usage:
    # Single server
    python scripts/with_server.py --server "npm run dev" --port 5173 -- python automation.py
    python scripts/with_server.py --server "npm start" --port 3000 -- python test.py

    # Multiple servers
    python scripts/with_server.py \
      --server "cd backend && python server.py" --port 3000 \
      --server "cd frontend && npm run dev" --port 5173 \
      -- python test.py

Process cleanup
---------------
Servers are started through a shell (so `cd x && npm run dev` works), which means
the process we hold is the *shell*, not the server. Signalling only that shell
leaves the real server alive holding the port — the next run then reports
"Server failed to start", while a server is in fact running: the previous one.

So the whole process tree is torn down: a Job-object-free `taskkill /F /T` on
Windows, a process group signal on POSIX. Both are checked afterwards by probing
the port again, and anything left behind is reported loudly instead of ignored.
"""

import argparse
import os
import platform
import signal
import socket
import subprocess
import sys
import tempfile
import time

IS_WINDOWS = platform.system() == 'Windows'


def _capture(cmd, timeout=None):
    """Run a helper command and return (returncode, combined_output).

    Decoding is done by hand with errors='replace': console tools on a
    localized Windows answer in the OEM code page, and `text=True` would blow
    up inside subprocess's reader thread — losing the output we came for while
    the call still looks like it worked.
    """
    proc = subprocess.run(cmd, capture_output=True, timeout=timeout)
    enc = 'cp866' if IS_WINDOWS else (sys.stdout.encoding or 'utf-8')
    out = (proc.stdout or b'').decode(enc, errors='replace')
    err = (proc.stderr or b'').decode(enc, errors='replace')
    return proc.returncode, (out + err)


def port_in_use(port, host='localhost', timeout=0.5):
    """True if something already accepts connections on the port."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def is_server_ready(port, timeout=30, process=None):
    """Wait for server to be ready by polling the port.

    If the server process dies while we wait, stop waiting immediately — the
    30-second silence followed by a generic timeout message hides the real
    cause (a crash on startup) behind a wrong one (a slow server).
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if port_in_use(port, timeout=1):
            return True
        if process is not None and process.poll() is not None:
            return False
        time.sleep(0.5)
    return False


def describe_port_holder(port):
    """Which process holds the port. Never raises, never returns silence.

    Always answers with a string: either the holder, or why it could not be
    determined. "Could not tell" and "nothing there" must not look alike.
    """
    try:
        if IS_WINDOWS:
            _, out = _capture(['netstat', '-ano', '-p', 'TCP'], timeout=20)
            pids = set()
            for line in out.splitlines():
                parts = line.split()
                if len(parts) >= 5 and parts[0] == 'TCP' and parts[1].endswith(f':{port}') \
                        and parts[3] == 'LISTENING':
                    pids.add(parts[4])
            if not pids:
                return 'no LISTENING socket reported by netstat'
            listing = ', '.join(f'PID {pid}' for pid in sorted(pids))
            # Process names are a nicety, and `tasklist` can take half a minute
            # on a busy machine — never let it hold up the PIDs themselves.
            try:
                _, tasks = _capture(['tasklist', '/FO', 'CSV', '/NH'], timeout=8)
            except subprocess.TimeoutExpired:
                return listing + ' (tasklist too slow to resolve names)'
            named = []
            for pid in sorted(pids):
                name = next((l.split('","')[0].strip('"')
                             for l in tasks.splitlines()
                             if f'","{pid}","' in l), '?')
                named.append(f'PID {pid} ({name})')
            return ', '.join(named)
        _, out = _capture(['lsof', '-nP', f'-iTCP:{port}', '-sTCP:LISTEN'], timeout=20)
        lines = out.strip().splitlines()
        if len(lines) > 1:
            return lines[1]
        return 'lsof reported no listener (install lsof if it is missing)'
    except FileNotFoundError as exc:
        return f'could not identify holder: {exc.filename} not available'
    except Exception as exc:
        return f'could not identify holder: {exc.__class__.__name__}: {exc}'


def kill_tree(process, label):
    """Terminate the server AND everything the shell spawned underneath it.

    Returns a short string describing what was done (for the log).
    """
    if process.poll() is not None:
        return f'{label}: already exited (code {process.returncode})'

    if IS_WINDOWS:
        # /T walks the child tree, /F is required because a console app started
        # through cmd.exe will not honour a polite request from another console.
        code, output = _capture(['taskkill', '/F', '/T', '/PID', str(process.pid)])
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        if code != 0:
            return (f'{label}: taskkill /T exited {code} — '
                    f'{output.strip() or "no output"}')
        return f'{label}: process tree killed'

    # POSIX: the shell is a session leader (start_new_session=True), so the
    # whole group — including a server that the shell never exec'd over — gets
    # the signal.
    try:
        pgid = os.getpgid(process.pid)
    except OSError:
        pgid = None

    try:
        if pgid is not None:
            os.killpg(pgid, signal.SIGTERM)
        else:
            process.terminate()
        process.wait(timeout=5)
        return f'{label}: process group terminated'
    except subprocess.TimeoutExpired:
        if pgid is not None:
            os.killpg(pgid, signal.SIGKILL)
        else:
            process.kill()
        process.wait()
        return f'{label}: process group killed (did not exit on SIGTERM)'
    except OSError as exc:
        return f'{label}: could not signal process group: {exc}'


def tail(path, lines=40):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as fh:
            content = fh.read().splitlines()
    except OSError as exc:
        return f'(could not read {path}: {exc})'
    if not content:
        return '(no output)'
    return '\n'.join(content[-lines:])


def main():
    parser = argparse.ArgumentParser(description='Run command with one or more servers')
    parser.add_argument('--server', action='append', dest='servers', required=True, help='Server command (can be repeated)')
    parser.add_argument('--port', action='append', dest='ports', type=int, required=True, help='Port for each server (must match --server count)')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout in seconds per server (default: 30)')
    parser.add_argument('--reuse-running', action='store_true',
                        help='If a port is already in use, reuse that server instead of refusing to start')
    parser.add_argument('command', nargs=argparse.REMAINDER, help='Command to run after server(s) ready')

    args = parser.parse_args()

    # Remove the '--' separator if present
    if args.command and args.command[0] == '--':
        args.command = args.command[1:]

    if not args.command:
        print("Error: No command specified to run")
        sys.exit(1)

    # Parse server configurations
    if len(args.servers) != len(args.ports):
        print("Error: Number of --server and --port arguments must match")
        sys.exit(1)

    servers = []
    for cmd, port in zip(args.servers, args.ports):
        servers.append({'cmd': cmd, 'port': port})

    # Refuse to start on top of an occupied port. Starting anyway is how the
    # confusing failure happens: the new server exits "port taken", the port
    # answers (the OLD server does), and the run silently tests stale code.
    occupied = [s for s in servers if port_in_use(s['port'])]
    if occupied and not args.reuse_running:
        print('\nERROR: port already in use before starting anything.', file=sys.stderr)
        for s in occupied:
            holder = describe_port_holder(s['port'])
            print(f"  port {s['port']}: {holder or 'holder could not be identified'}", file=sys.stderr)
        print('\nMost likely a server left over from a previous run (a shell was killed,',
              file=sys.stderr)
        print('the server under it survived). Stop it, then retry:', file=sys.stderr)
        if IS_WINDOWS:
            print(f"  netstat -ano -p TCP | findstr :{occupied[0]['port']}", file=sys.stderr)
            print('  taskkill /F /T /PID <pid>', file=sys.stderr)
        else:
            print(f"  lsof -nP -iTCP:{occupied[0]['port']} -sTCP:LISTEN", file=sys.stderr)
            print('  kill <pid>', file=sys.stderr)
        print('\nOr pass --reuse-running to deliberately test against what is already up.',
              file=sys.stderr)
        sys.exit(3)

    reused = {s['port'] for s in occupied} if args.reuse_running else set()
    for port in sorted(reused):
        print(f'Note: reusing the server already listening on port {port} (--reuse-running)')

    server_processes = []
    log_paths = []

    try:
        # Start all servers
        for i, server in enumerate(servers):
            if server['port'] in reused:
                continue

            print(f"Starting server {i+1}/{len(servers)}: {server['cmd']}")

            # Server output goes to a file, not to an unread PIPE: an unread
            # pipe fills up and freezes a chatty dev server for good, and the
            # output is exactly what is needed when startup fails.
            log = tempfile.NamedTemporaryFile(
                prefix=f'with_server_{server["port"]}_', suffix='.log',
                delete=False, mode='w', encoding='utf-8')
            log_paths.append(log.name)

            popen_kwargs = {
                'shell': True,
                'stdout': log,
                'stderr': subprocess.STDOUT,
            }
            if IS_WINDOWS:
                # Own process group, so Ctrl-C in this console does not race
                # with our own teardown.
                popen_kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                # Own session: killpg later reaches the real server even when
                # the shell never exec'd over itself.
                popen_kwargs['start_new_session'] = True

            process = subprocess.Popen(server['cmd'], **popen_kwargs)
            log.close()
            server_processes.append(process)

            # Wait for this server to be ready
            print(f"Waiting for server on port {server['port']}... (log: {log.name})")
            if not is_server_ready(server['port'], timeout=args.timeout, process=process):
                exited = process.poll()
                reason = (f'the server process exited early with code {exited}'
                          if exited is not None
                          else f'nothing was listening after {args.timeout}s')
                raise RuntimeError(
                    f"Server failed to start on port {server['port']}: {reason}.\n"
                    f"--- last lines of {log.name} ---\n{tail(log.name)}\n"
                    f"--- end of server log ---"
                )

            print(f"Server ready on port {server['port']}")

        print(f"\nAll {len(servers)} server(s) ready")

        # Run the command
        print(f"Running: {' '.join(args.command)}\n")
        result = subprocess.run(args.command)
        sys.exit(result.returncode)

    finally:
        # Clean up all servers
        if server_processes:
            print(f"\nStopping {len(server_processes)} server(s)...")
            for i, process in enumerate(server_processes):
                print('  ' + kill_tree(process, f'Server {i+1}'))

            # Prove it. A "stopped" message over a still-bound port is the very
            # lie that makes the next run fail for the wrong reason.
            time.sleep(0.5)
            leftovers = [s['port'] for s in servers
                         if s['port'] not in reused and port_in_use(s['port'])]
            if leftovers:
                print('\nWARNING: these ports are STILL in use after cleanup: '
                      + ', '.join(str(p) for p in leftovers), file=sys.stderr)
                for port in leftovers:
                    holder = describe_port_holder(port)
                    print(f'  port {port}: {holder or "holder could not be identified"}',
                          file=sys.stderr)
                print('Kill it manually, or the next run will test against this stale server.',
                      file=sys.stderr)
            else:
                print("All servers stopped")

        for path in log_paths:
            print(f'Server log kept at: {path}')


if __name__ == '__main__':
    main()
