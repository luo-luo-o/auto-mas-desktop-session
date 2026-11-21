
import ctypes as C, json, os, sys, time
from ctypes import wintypes as W
if sys.argv[1]=="wait":
    time.sleep(60)
    raise SystemExit
import tkinter as tk
import win32api, win32con, win32gui
window=tk.Tk()
window.title("AUTO-MAS isolated input probe")
entry=tk.Entry(window);entry.pack();window.attributes("-topmost",True);window.update()
window.focus_force();entry.focus_force();window.update()
for char in "MAS":
    key=ord(char)
    win32api.keybd_event(key,0,0,0)
    win32api.keybd_event(key,0,win32con.KEYEVENTF_KEYUP,0)
for _ in range(30):
    window.update();time.sleep(.02)
sid=W.DWORD()
C.windll.kernel32.ProcessIdToSessionId(os.getpid(), C.byref(sid))
print(json.dumps({"session":sid.value,"typed":entry.get().casefold()=="mas"}),flush=True)
window.destroy()
