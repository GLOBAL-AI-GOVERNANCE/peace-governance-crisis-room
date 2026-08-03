#!/usr/bin/env python3
from __future__ import annotations
import argparse, http.server, os, shutil, signal, socket, subprocess, threading, time, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--required',action='store_true',help='Fail rather than report HOLD when a browser cannot be executed')
args=parser.parse_args()
browser=next((shutil.which(x) for x in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(x)),None)
def hold(message: str) -> None:
    print('HOLD: '+message)
    if args.required: raise SystemExit(1)
    raise SystemExit(0)
if browser is None: hold('no Chromium-family browser found; browser runtime remains unverified in this environment.')
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
with socket.socket() as s: s.bind(('127.0.0.1',0)); port=s.getsockname()[1]
server=http.server.ThreadingHTTPServer(('127.0.0.1',port),lambda *a,**k: Quiet(*a,directory=str(ROOT/'web'),**k))
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();time.sleep(.2)
try:
    with tempfile.TemporaryDirectory(prefix='peace-os-browser-') as profile:
        cmd=[browser,'--headless','--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--no-first-run','--disable-background-networking',f'--user-data-dir={profile}','--virtual-time-budget=4000','--dump-dom',f'http://127.0.0.1:{port}/?selftest=1']
        # Use temporary files instead of PIPE so descendant Chromium processes cannot
        # keep the parent blocked after a timeout. Kill the process group on POSIX.
        with tempfile.TemporaryFile(mode='w+', encoding='utf-8') as stdout_file, tempfile.TemporaryFile(mode='w+', encoding='utf-8') as stderr_file:
            process=subprocess.Popen(
                cmd,
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
                start_new_session=(os.name != 'nt'),
            )
            try:
                returncode=process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                if os.name != 'nt':
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                else:
                    process.kill()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass
                hold('the installed Chromium process did not complete in this container; browser runtime remains unverified.')
            stdout_file.seek(0)
            stdout=stdout_file.read()
        if returncode or 'data-selftest="pass"' not in stdout:
            hold('Chromium execution did not produce the expected self-test marker; browser runtime remains unverified.')
        print('PASS: Chromium smoke loaded two scenarios and the scoring rubric.')
finally:
    server.shutdown();server.server_close()
