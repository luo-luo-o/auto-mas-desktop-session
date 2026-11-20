"""分身预览与环境修复使用的 Win32 操作。"""

import ctypes as C
import os
from ctypes import wintypes as W

from auto_mas_core.host.windows_session import (
    bind,
    checked,
    child_session,
    process_session,
    user32,
    wtsapi32,
)


def child_sessions_enabled():
    fn = bind(wtsapi32, "WTSIsChildSessionsEnabled", W.BOOL, C.POINTER(W.BOOL))
    enabled = W.BOOL()
    checked(fn(C.byref(enabled)), "WTSIsChildSessionsEnabled")
    return bool(enabled.value)


def set_child_sessions_enabled(*, enabled: bool) -> None:
    fn = bind(wtsapi32, "WTSEnableChildSessions", W.BOOL, W.BOOL)
    checked(fn(enabled), "WTSEnableChildSessions")


def logoff_child(expected: int) -> None:
    current = child_session()
    if current is None:
        return
    if current != expected or current in (0, process_session(os.getpid())):
        raise RuntimeError("session_changed")
    logoff = bind(wtsapi32, "WTSLogoffSession", W.BOOL, W.HANDLE, W.DWORD, W.BOOL)
    checked(logoff(None, current, True), "WTSLogoffSession")


def primary_size() -> tuple[int, int]:
    metric = bind(user32, "GetSystemMetrics", C.c_int, C.c_int)
    return metric(0), metric(1)
