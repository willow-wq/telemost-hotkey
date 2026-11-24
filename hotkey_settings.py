"""Single-key configuration; no keyboard hooks or Windows imports."""
import json
from pathlib import Path

KEYS = {
    'RightShift': 0xA1, 'LeftShift': 0xA0,
    **{f'F{i}': 0x6F + i for i in range(1, 25)},
    'ScrollLock': 0x91, 'Insert': 0x2D,
    'Home': 0x24, 'End': 0x23, 'PageUp': 0x21, 'PageDown': 0x22,
    'Space': 0x20, 'Enter': 0x0D, 'Tab': 0x09, 'CapsLock': 0x14,
    **{chr(i): i for i in range(65, 91)},
    **{str(i): 0x30 + i for i in range(10)},
}


def load_key(path):
    try:
        value = json.loads(Path(path).read_text(encoding='utf-8')).get('hotkey')
        return value if value in KEYS else 'RightShift'
    except (OSError, ValueError, TypeError, AttributeError):
        return 'RightShift'


def save_key(path, name):
    if name not in KEYS:
        raise ValueError('Unsupported keyboard key')
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps({'hotkey': name}, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def show_settings(path):
    import tkinter as tk
    from tkinter import ttk, messagebox
    root = tk.Tk()
    root.title('Telemost Hotkey — настройки')
    root.resizable(False, False)
    panel = ttk.Frame(root, padding=20)
    panel.grid()
    ttk.Label(panel, text='Клавиша переключения микрофона:').grid(sticky='w')
    selected = tk.StringVar(value=load_key(path))
    ttk.Combobox(panel, textvariable=selected, values=list(KEYS),
                 state='readonly', width=26).grid(sticky='ew', pady=10)
    ttk.Label(panel, text='Одна клавиша, без сочетаний. Во время звонка она\n'
              'будет занята микрофоном во всех окнах.\n'
              'Буквы обозначены по латинскому расположению клавиш.').grid(sticky='w')
    def apply():
        try:
            save_key(path, selected.get())
        except (OSError, ValueError) as exc:
            messagebox.showerror('Не удалось сохранить', str(exc), parent=root)
            return
        root.destroy()
    ttk.Button(panel, text='Сохранить', command=apply).grid(sticky='e', pady=(15, 0))
    root.mainloop()
