#!/usr/bin/env python3
"""Experimental X11/AT-SPI microphone button activation for Telemost."""
import logging
import argparse
import json
import os
import select
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

MIC_LABELS = frozenset({
    'выключить микрофон', 'отключить микрофон', 'включить микрофон',
    'mute microphone', 'unmute microphone',
    'turn microphone on', 'turn microphone off',
})


def configured_key(cli_key, config_path):
    if cli_key is not None:
        value = cli_key
    elif config_path.exists():
        config = json.loads(config_path.read_text(encoding='utf-8'))
        if not isinstance(config, dict):
            raise ValueError('Config must be a JSON object.')
        value = config.get('hotkey', 'Shift_R')
    else:
        value = 'Shift_R'
    if not isinstance(value, str) or not value.strip():
        raise ValueError('hotkey must be a nonempty X11 keysym, such as F8 or Shift_R.')
    return value.strip()


def is_mic_label(name):
    return ' '.join(name.casefold().split()) in MIC_LABELS


def find_button(atspi):
    """Return one unambiguous, enabled visible button; incomplete scans fail closed."""
    matches = []
    desktop = atspi.Registry.getDesktop(0)
    stack = [(desktop, False)]
    budget = 12000
    try:
        while stack and budget:
            node, scoped = stack.pop()
            budget -= 1
            role = node.getRole()
            if role == atspi.ROLE_APPLICATION:
                scoped = node.name.casefold() in {'yandextelemost', 'yandex telemost', 'telemost', 'яндекс телемост', 'телемост'}
                if not scoped:
                    continue
            if scoped and role in (atspi.ROLE_PUSH_BUTTON, atspi.ROLE_TOGGLE_BUTTON, atspi.ROLE_CHECK_BOX):
                states = node.getState()
                if (is_mic_label(node.name) and states.contains(atspi.STATE_ENABLED)
                        and states.contains(atspi.STATE_SHOWING)
                        and not states.contains(atspi.STATE_DEFUNCT)):
                    action = node.queryAction()
                    indexes = [i for i in range(action.nActions)
                               if action.getName(i).casefold() in {'click', 'press', 'toggle', 'activate'}]
                    if len(indexes) == 1:
                        matches.append((node, indexes[0]))
                        if len(matches) > 1:
                            return None
            stack.extend((node.getChildAtIndex(i), scoped) for i in range(node.childCount))
    except Exception:
        logging.debug('Accessibility scan failed', exc_info=True)
        return None
    return matches[0] if not stack and len(matches) == 1 else None


def activate(atspi):
    current = find_button(atspi)
    if not current:
        return False
    try:
        node, index = current
        return bool(node.queryAction().doAction(index))
    except Exception:
        logging.warning('The microphone button became unavailable.')
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--toggle-once', action='store_true',
                        help='Invoke the accessible mic button once, without intercepting keys.')
    parser.add_argument('--key', metavar='KEYSYM',
                        help='X11 key, for example F8 or Shift_R; overrides config.json.')
    args = parser.parse_args()
    if args.toggle_once:
        import pyatspi
        if not activate(pyatspi):
            raise SystemExit('No unique accessible Telemost microphone action was found or it was rejected.')
        return
    if os.environ.get('XDG_SESSION_TYPE', '').lower() != 'x11':
        raise SystemExit('Global interception requires X11. On Wayland assign --toggle-once to a desktop shortcut.')
    import fcntl
    import pyatspi
    from Xlib import X, XK, display, error

    logging.basicConfig(level=logging.INFO, format='%(message)s')
    runtime = os.environ.get('XDG_RUNTIME_DIR')
    if not runtime:
        raise SystemExit('XDG_RUNTIME_DIR is required.')
    lock = open(os.path.join(runtime, 'telemost-right-shift.lock'), 'a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit('Another instance is already running.')
    connection = display.Display()
    root = connection.screen().root
    config_path = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'telemost-hotkey' / 'config.json'
    try:
        key_name = configured_key(args.key, config_path)
    except (OSError, ValueError) as exc:
        raise SystemExit(f'Cannot read hotkey configuration: {exc}') from exc
    keysym = XK.string_to_keysym(key_name)
    if not keysym:
        raise SystemExit(f'Unknown X11 keysym: {key_name}')
    key = connection.keysym_to_keycode(keysym)
    if not key:
        raise SystemExit(f'No keycode was found for {key_name}.')
    grabbed = False
    last_press = 0.0
    candidate = None
    next_scan = 0.0
    executor = ThreadPoolExecutor(max_workers=1)
    scan_future = None
    action_future = None

    def grab_error(err, _request):
        nonlocal grabbed
        if isinstance(err, error.BadAccess):
            grabbed = False
            logging.warning('%s is reserved by another application.', key_name)
        else:
            raise err

    try:
        while True:
            now = time.monotonic()
            if action_future is not None and action_future.done():
                try:
                    if not action_future.result():
                        logging.warning('No microphone action was performed.')
                except Exception:
                    logging.exception('Microphone action failed')
                action_future = None
            if now >= next_scan and scan_future is None:
                scan_future = executor.submit(find_button, pyatspi)
            if scan_future is not None and scan_future.done():
                candidate = scan_future.result()
                scan_future = None
                next_scan = time.monotonic() + 1
                if candidate and not grabbed:
                    grabbed = True
                    root.grab_key(key, X.AnyModifier, False, X.GrabModeAsync,
                                  X.GrabModeSync, onerror=grab_error)
                    connection.sync()
                elif not candidate and grabbed:
                    root.ungrab_key(key, X.AnyModifier)
                    connection.sync()
                    grabbed = False
            if not connection.pending_events():
                select.select([connection.fileno()], [], [], 0.1)
            while connection.pending_events():
                event = connection.next_event()
                if event.type == X.KeyPress:
                    # Replay the original modifier immediately, releasing the
                    # active keyboard grab before doing any accessibility I/O.
                    connection.allow_events(X.ReplayKeyboard, event.time)
                    connection.flush()
                    modifiers = X.ControlMask | X.Mod1Mask | X.Mod4Mask | X.Mod5Mask | X.ShiftMask
                    if (event.detail == key and not event.state & modifiers
                            and time.monotonic() - last_press > 0.4
                            and (action_future is None or action_future.done())):
                        last_press = time.monotonic()
                        action_future = executor.submit(activate, pyatspi)
                elif event.type == X.MappingNotify:
                    # Stop rather than keep a stale grab after layout changes.
                    raise SystemExit('Keyboard mapping changed; restart the helper.')
    finally:
        if grabbed:
            root.ungrab_key(key, X.AnyModifier)
            connection.sync()
        connection.close()
        lock.close()
        executor.shutdown(wait=False, cancel_futures=True)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
