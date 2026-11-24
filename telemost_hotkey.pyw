"""Global Telemost microphone hotkey, enabled only while a call exists."""
import ctypes as c
from ctypes import wintypes as w
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
import os
import subprocess
import sys
import time
from hotkey_settings import KEYS, load_key, show_settings

LOG_DIR = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'TelemostHotkey'
LOG_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_PATH = LOG_DIR / 'config.json'
if '--settings' in sys.argv:
    show_settings(CONFIG_PATH)
    raise SystemExit(0)
logging.basicConfig(handlers=[RotatingFileHandler(LOG_DIR / ('watcher.log' if '--watch' in sys.argv else 'worker.log'),
                    maxBytes=256_000, backupCount=1, encoding='utf-8')],
                    level=logging.INFO, format='%(asctime)s %(message)s')
u = c.WinDLL('user32', use_last_error=True)
k = c.WinDLL('kernel32', use_last_error=True)
# Keep client coordinates and child-window mapping in the same physical-pixel
# space, including after moving Telemost between monitors with different DPI.
u.SetProcessDpiAwarenessContext.argtypes = [w.HANDLE]
u.SetProcessDpiAwarenessContext.restype = w.BOOL
if not u.SetProcessDpiAwarenessContext(c.c_void_p(-4)):
    if c.get_last_error() != 5:  # A manifest may already have set awareness.
        raise c.WinError(c.get_last_error())
LRESULT = c.c_ssize_t
HOOKPROC = c.WINFUNCTYPE(LRESULT, c.c_int, w.WPARAM, w.LPARAM)
u.SetWindowsHookExW.argtypes = [c.c_int, HOOKPROC, w.HINSTANCE, w.DWORD]
u.SetWindowsHookExW.restype = w.HANDLE
u.CallNextHookEx.argtypes = [w.HANDLE, c.c_int, w.WPARAM, w.LPARAM]
u.CallNextHookEx.restype = LRESULT
u.GetWindowTextW.argtypes = [w.HWND, w.LPWSTR, c.c_int]
u.GetWindowThreadProcessId.argtypes = [w.HWND, c.POINTER(w.DWORD)]
u.GetClientRect.argtypes = [w.HWND, c.POINTER(w.RECT)]
u.ChildWindowFromPointEx.argtypes = [w.HWND, w.POINT, w.UINT]
u.ChildWindowFromPointEx.restype = w.HWND
u.MapWindowPoints.argtypes = [w.HWND, w.HWND, c.POINTER(w.POINT), w.UINT]
u.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
u.UnhookWindowsHookEx.argtypes = [w.HANDLE]
k.CloseHandle.argtypes = [w.HANDLE]
k.CreateMutexW.argtypes = [w.LPVOID, w.BOOL, w.LPCWSTR]
k.CreateMutexW.restype = w.HANDLE
k.OpenMutexW.argtypes = [w.DWORD, w.BOOL, w.LPCWSTR]
k.OpenMutexW.restype = w.HANDLE
k.GetModuleHandleW.argtypes = [w.LPCWSTR]
k.GetModuleHandleW.restype = w.HMODULE
WNDENUMPROC = c.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
u.EnumWindows.argtypes = [WNDENUMPROC, w.LPARAM]
u.IsWindowVisible.argtypes = [w.HWND]
u.SetTimer.argtypes = [w.HWND, c.c_size_t, w.UINT, c.c_void_p]
u.SetTimer.restype = c.c_size_t
u.KillTimer.argtypes = [w.HWND, c.c_size_t]
u.PostThreadMessageW.argtypes = [w.DWORD, w.UINT, w.WPARAM, w.LPARAM]
u.GetDpiForWindow.argtypes = [w.HWND]
u.GetDpiForWindow.restype = w.UINT
u.GetAsyncKeyState.argtypes = [c.c_int]
u.GetAsyncKeyState.restype = c.c_short
u.GetMessageW.argtypes = [c.POINTER(w.MSG), w.HWND, w.UINT, w.UINT]
u.TranslateMessage.argtypes = [c.POINTER(w.MSG)]
u.DispatchMessageW.argtypes = [c.POINTER(w.MSG)]
u.DispatchMessageW.restype = LRESULT
k.GetCurrentThreadId.restype = w.DWORD
k.CreateEventW.argtypes = [w.LPVOID, w.BOOL, w.BOOL, w.LPCWSTR]
k.CreateEventW.restype = w.HANDLE
k.SetEvent.argtypes = [w.HANDLE]
k.WaitForSingleObject.argtypes = [w.HANDLE, w.DWORD]
k.CreateToolhelp32Snapshot.argtypes = [w.DWORD, w.DWORD]
k.CreateToolhelp32Snapshot.restype = w.HANDLE

class PROCESSENTRY32(c.Structure):
    _fields_ = [('dwSize', w.DWORD), ('cntUsage', w.DWORD),
                ('th32ProcessID', w.DWORD), ('th32DefaultHeapID', c.c_size_t),
                ('th32ModuleID', w.DWORD), ('cntThreads', w.DWORD),
                ('th32ParentProcessID', w.DWORD), ('pcPriClassBase', w.LONG),
                ('dwFlags', w.DWORD), ('szExeFile', w.WCHAR * 260)]

k.Process32FirstW.argtypes = [w.HANDLE, c.POINTER(PROCESSENTRY32)]
k.Process32NextW.argtypes = [w.HANDLE, c.POINTER(PROCESSENTRY32)]

def telemost_pids():
    snapshot = k.CreateToolhelp32Snapshot(2, 0)
    if snapshot == c.c_void_p(-1).value:
        return set()
    result = set()
    try:
        entry = PROCESSENTRY32()
        entry.dwSize = c.sizeof(entry)
        ok = k.Process32FirstW(snapshot, c.byref(entry))
        while ok:
            if entry.szExeFile.lower() == 'yandextelemost.exe':
                result.add(entry.th32ProcessID)
            ok = k.Process32NextW(snapshot, c.byref(entry))
    finally:
        k.CloseHandle(snapshot)
    return result

class KBD(c.Structure):
    _fields_ = [('vkCode', w.DWORD), ('scanCode', w.DWORD), ('flags', w.DWORD),
                ('time', w.DWORD), ('extra', c.c_size_t)]

if '--self-test' in sys.argv:
    # Exercise bundled imports and native process enumeration without a hook.
    telemost_pids()
    import tkinter as tk
    test_root = tk.Tk()
    test_root.withdraw()
    test_root.destroy()
    raise SystemExit(0)

stop_event = k.CreateEventW(None, True, False, 'Local\\TelemostRightShiftMic_stop')
if not stop_event:
    raise c.WinError(c.get_last_error())
if '--stop' in sys.argv:
    k.SetEvent(stop_event)
    deadline = time.monotonic() + 15
    while True:
        running = False
        for role in ('watcher', 'worker'):
            existing = k.OpenMutexW(0x100000, False, 'Local\\TelemostRightShiftMic_' + role)
            if existing:
                running = True
                k.CloseHandle(existing)
        if not running:
            break
        if time.monotonic() >= deadline:
            k.CloseHandle(stop_event)
            raise SystemExit(1)
        time.sleep(0.1)
    time.sleep(0.5)
    k.CloseHandle(stop_event)
    raise SystemExit(0)

watcher = '--watch' in sys.argv
mutex = k.CreateMutexW(None, False, 'Local\\TelemostRightShiftMic_' + ('watcher' if watcher else 'worker'))
if not mutex or c.get_last_error() == 183:
    raise SystemExit()

if watcher:
    logging.info('Watcher started; no keyboard hook until a Telemost call exists')
    child = None
    retry_at = 0
    try:
        while k.WaitForSingleObject(stop_event, 0) != 0:
            if child is not None and child.poll() is not None:
                retry_at = time.monotonic() + (10 if child.returncode else 0)
                child = None
            if time.monotonic() >= retry_at and telemost_pids() and child is None:
                command = [sys.executable]
                if not getattr(sys, 'frozen', False):
                    command.append(str(Path(__file__).resolve()))
                child = subprocess.Popen(command + ['--worker'],
                                         env={**os.environ, 'PYINSTALLER_RESET_ENVIRONMENT': '1'},
                                         creationflags=subprocess.CREATE_NO_WINDOW)
            time.sleep(1)
    finally:
        k.CloseHandle(mutex)
        k.CloseHandle(stop_event)
    raise SystemExit()

def call_usable(hwnd):
    rect = w.RECT()
    dpi = u.GetDpiForWindow(hwnd)
    return (dpi > 0 and u.GetClientRect(hwnd, c.byref(rect))
            and rect.right >= round(800 * dpi / 96)
            and rect.bottom >= round(450 * dpi / 96))

def microphone_point(height, dpi):
    return round(88 * dpi / 96), height - round(34 * dpi / 96)

def call_window(pids):
    matches = []
    @WNDENUMPROC
    def collect(hwnd, _):
        if not u.IsWindowVisible(hwnd):
            return True
        pid = w.DWORD()
        u.GetWindowThreadProcessId(hwnd, c.byref(pid))
        if pid.value in pids:
            title = c.create_unicode_buffer(512)
            u.GetWindowTextW(hwnd, title, len(title))
            if title.value == 'Звонок' and call_usable(hwnd):
                matches.append(hwnd)
        return True
    u.EnumWindows(collect, 0)
    return matches[0] if len(matches) == 1 else None

def toggle_mic(hwnd):
    rect = w.RECT()
    if not call_usable(hwnd) or not u.GetClientRect(hwnd, c.byref(rect)):
        logging.info('Skipped unsupported window size')
        return
    # Toolbar offsets are device-independent pixels in the supported Qt layout.
    # Re-read DPI here: the window may have changed monitor since the timer tick.
    dpi = u.GetDpiForWindow(hwnd)
    if not dpi:
        return
    x, y = microphone_point(rect.bottom, dpi)
    if not (0 <= x < rect.right and 0 <= y < rect.bottom):
        return
    point = w.POINT(x, y)
    target = hwnd
    for _ in range(12):
        child = u.ChildWindowFromPointEx(target, point, 7)
        if not child or child == target:
            break
        u.MapWindowPoints(target, child, c.byref(point), 1)
        target = child
    packed = (point.x & 0xffff) | ((point.y & 0xffff) << 16)
    down = u.PostMessageW(target, 0x201, 1, packed)
    up = u.PostMessageW(target, 0x202, 0, packed)
    logging.info('Microphone click queued' if down and up else 'Microphone click failed')

pressed = False
bound_window = None
cached_call = None
thread_id = k.GetCurrentThreadId()
hotkey_vk = KEYS[load_key(CONFIG_PATH)]

@HOOKPROC
def hook(code, message, data):
    global pressed, bound_window
    try:
        if code >= 0:
            event = c.cast(data, c.POINTER(KBD)).contents
            if event.vkCode == hotkey_vk:
                if message in (0x100, 0x104):
                    if not pressed:
                        # Preserve Shift chords with modifiers already held.
                        modifiers = any(u.GetAsyncKeyState(v) & 0x8000
                                        for v in (0x11, 0x12, 0x5B, 0x5C, 0xA0, 0xA1)
                                        if v != hotkey_vk)
                        bound_window = None if modifiers else cached_call
                        pressed = True
                        if bound_window:
                            if not u.PostThreadMessageW(thread_id, 0x8001, bound_window, 0):
                                bound_window = None
                    if bound_window:
                        return 1
                elif message in (0x101, 0x105):
                    consumed = bool(bound_window)
                    pressed = False
                    bound_window = None
                    if consumed:
                        return 1
    except Exception:
        logging.exception('Hotkey error')
    return u.CallNextHookEx(None, code, message, data)

handle = None
timer = u.SetTimer(None, 0, 400, None)
if not timer:
    raise c.WinError(c.get_last_error())
logging.info('Telemost worker started')
try:
    msg = w.MSG()
    while True:
        result = u.GetMessageW(c.byref(msg), None, 0, 0)
        if result == -1:
            raise c.WinError(c.get_last_error())
        if result == 0:
            break
        if msg.message == 0x113:
            if not pressed:
                hotkey_vk = KEYS[load_key(CONFIG_PATH)]
            if k.WaitForSingleObject(stop_event, 0) == 0:
                break
            pids = telemost_pids()
            if not pids:
                logging.info('Telemost closed; worker stopping')
                break
            cached_call = call_window(pids)
            if cached_call and not handle:
                handle = u.SetWindowsHookExW(13, hook, k.GetModuleHandleW(None), 0)
                if not handle:
                    raise c.WinError(c.get_last_error())
                logging.info('Call detected; configured global key enabled (VK=%s)', hotkey_vk)
            elif not cached_call and handle:
                u.UnhookWindowsHookEx(handle)
                handle = None
                pressed = False
                bound_window = None
                logging.info('Call ended; keyboard hook disabled')
            continue
        if msg.message == 0x8001:
            # Revalidate the destination if the call ended during the key press.
            if msg.wParam == cached_call and call_window(telemost_pids()) == cached_call:
                toggle_mic(cached_call)
            continue
        u.TranslateMessage(c.byref(msg))
        u.DispatchMessageW(c.byref(msg))
finally:
    if handle:
        u.UnhookWindowsHookEx(handle)
    u.KillTimer(None, timer)
    k.CloseHandle(mutex)
    k.CloseHandle(stop_event)
