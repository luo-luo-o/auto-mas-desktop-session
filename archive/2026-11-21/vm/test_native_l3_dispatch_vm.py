
import asyncio, json, os, sys
from pathlib import Path
import psutil, pytest, win32gui
from auto_mas_core.host.task_execution import use_script_execution_target
from whimbox_adapter.plugin import Plugin as WhimboxAdapter
from app.models.task import TaskMode
from app.task.user_expander import UserExpander
from app.utils.common.process.session import DesktopProcessTarget
from app.utils.windows.desktop_session.native import process_session
from app.utils.windows.desktop_session.process_runner import launch_desktop_process
from tests.support.scheduler import scheduler as scheduler

@pytest.mark.asyncio
@pytest.mark.parametrize("stop", [False, True])
async def test_native_dispatch(scheduler, monkeypatch, stop):
    manager, scripts, _, _ = scheduler
    cls = WhimboxAdapter.decl.script_type
    scripts.add_type(cls)
    await scripts.commit()
    sid = scripts.add(cls)
    await scripts.commit()
    entered = asyncio.Event()
    evidence = {}
    foreground = win32gui.GetForegroundWindow()
    root = Path.cwd()
    session = int(os.environ["MAS_TEST_CHILD_SESSION"])
    assert process_session(os.getpid()) != session

    class LocalL3(UserExpander):
        async def prepare(self):
            raise AssertionError("unexpected parent execution")
        def build_worker(self, user, config):
            raise AssertionError("unexpected parent execution")

    monkeypatch.setattr(manager, "plugin_expander", LocalL3)
    class Target:
        async def run_script(self, script):
            p = await launch_desktop_process(
                DesktopProcessTarget(session, root, root),
                argv=[sys.executable, str(root/"native_input_worker.py"), "wait" if stop else "run"],
                cwd=root, capture=True,
            )
            try:
                evidence["session"] = process_session(p.pid)
                entered.set()
                code, out, _ = await p.wait()
                assert code == 0
                assert json.loads(out.decode()) == {"session": session, "typed": True}
                await script.set_state(status="完成")
            finally:
                await p.stop()
                evidence["exited"] = not psutil.pid_exists(p.pid)

    with use_script_execution_target(Target()):
        uid = await manager.start(TaskMode.AUTO_PROXY, {0: {"uid": "-", "children": {0: {"uid": str(sid)}}}})
    run=manager.task_handler[uid]
    await asyncio.wait_for(entered.wait(), 35)
    if stop:
        await asyncio.wait_for(manager.stop(uid), 20)
    await asyncio.wait_for(run.accomplish.wait(), 30)
    assert manager.get_task_status(str(uid)).status == ("cancelled" if stop else "success")
    assert evidence["session"] == session and evidence["exited"]
    assert win32gui.GetForegroundWindow() == foreground
