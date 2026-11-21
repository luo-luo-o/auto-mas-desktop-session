
import asyncio, json, os, shutil, subprocess, sys, time
from pathlib import Path
import win32gui, win32con

root = Path(__file__).resolve().parent
old = Path(r"E:\AUTO-MAS\AUTO-MAS")
sys.path[:0] = [str(root), str(root / "plugins/auto_mas_core/src")]
from app.utils.common.process.session import DesktopProcessTarget
from app.utils.windows.desktop_session.native import child_session, process_session
from app.utils.windows.desktop_session.process_runner import launch_desktop_process

def report(event, **extra):
    print(json.dumps({"event":event, **extra}),flush=True)

async def probe(session):

    env={**os.environ,"MAS_TEST_CHILD_SESSION":str(session),"PYTHONPATH":str(root/"plugins/auto_mas_core/src")}
    suite=subprocess.Popen([sys.executable,"-m","pytest","tests/core/test_native_l3_dispatch_vm.py","-q","--basetemp=pytest-native-l3"],cwd=root,env=env)
    deadline=time.monotonic()+80
    while suite.poll() is None and time.monotonic()<deadline:
        await asyncio.sleep(.05)
    if suite.poll() is None:
        suite.kill()
        suite.wait()
        raise TimeoutError("native_l3_suite")
    report("l2_native_suite", return_code=suite.returncode)
    if suite.returncode!=0:
        raise RuntimeError("native_l3_suite_failed")


def main():
    if child_session() is not None:
        raise RuntimeError("unexpected_existing_child")
    owner=win32gui.CreateWindow("STATIC","AUTO-MAS VM probe",win32con.WS_OVERLAPPEDWINDOW|win32con.WS_VISIBLE,50,50,1000,760,0,0,0,None)
    path=root/"native-input-profile"/"config/desktop-session/credentials.json"
    path.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(old/"config/desktop-session/credentials.json",path)
    boot=old/"plugins/desktop_session/src/desktop_session/bootstrap.py"
    try:
        host=subprocess.Popen([sys.executable,"-I",str(boot),str(root),"preview",str(path.parents[2])],cwd=root,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,encoding="utf-8")
    finally:
        pass
    from threading import Thread
    from queue import Queue
    rows=Queue()
    def read():
        for line in host.stdout:
            try: rows.put(json.loads(line))
            except ValueError: continue
    Thread(target=read,daemon=True).start()
    def command(msg):
        host.stdin.write(json.dumps(msg)+"\n")
        host.stdin.flush()
    try:
        command({"action":"connect","mode":"native","resolution":"primary","owner":owner,"bounds":[50,50,900,666],"adoptSessionId":None})
        deadline=time.monotonic()+50
        from queue import Empty
        while time.monotonic()<deadline:
            win32gui.PumpWaitingMessages()
            try: row=rows.get(timeout=.05)
            except Empty:
                if host.poll() is not None: raise RuntimeError("preview_exited")
                continue
            if row.get("event") in {"state","command_error","ready"}:
                report("preview_event", **{k:row[k] for k in ("state","code","nativeCode") if k in row})
            session=child_session()
            if row.get("state")=="connected" and session:
                report("connected", main=process_session(os.getpid()), child=session)
                async def run_with_pump():
                    task=asyncio.create_task(probe(session))
                    while not task.done():
                        win32gui.PumpWaitingMessages()
                        await asyncio.sleep(.02)
                    await task
                asyncio.run(run_with_pump())
                return
            if row.get("state") in ("idle","disconnected") and row.get("code"):
                raise RuntimeError(row["code"])
        raise TimeoutError("child_connect_timeout")
    finally:
        if host.poll() is None:
            try:
                command({"action":"close","logoff":True})
                command({"action":"shutdown"})
                close_deadline=time.monotonic()+15
                while host.poll() is None and time.monotonic()<close_deadline:
                    win32gui.PumpWaitingMessages()
                    time.sleep(.05)
            finally:
                if host.poll() is None: host.kill()
        path.unlink(missing_ok=True)

if __name__=="__main__":
    try: main()
    except Exception as e:
        import traceback
        report("failed",kind=type(e).__name__, code=str(e), where=[x.name for x in traceback.extract_tb(e.__traceback__)])
        raise SystemExit(1)
