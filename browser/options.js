(function () {
  "use strict";
  const settings = globalThis.TelemostHotkeySettings;
  const core = globalThis.TelemostRightShiftCore;
  const current = document.getElementById("current");
  const status = document.getElementById("status");
  const capture = document.getElementById("capture");
  let capturing = false;
  function display(code) { current.textContent = code === "ShiftRight" ? "Правый Shift (ShiftRight)" : code; }
  async function save(code) {
    try { await settings.write(code); display(code); status.textContent = "Клавиша сохранена."; }
    catch (error) { status.textContent = "Не удалось сохранить: " + error.message; }
  }
  settings.read().then(display);
  settings.subscribe(display);
  capture.addEventListener("click", () => {
    capturing = true;
    status.textContent = "Нажмите одну клавишу. Escape — отмена.";
    capture.focus();
  });
  document.getElementById("reset").addEventListener("click", () => { capturing = false; save("ShiftRight"); });
  window.addEventListener("blur", () => { capturing = false; });
  document.addEventListener("keydown", event => {
    if (!capturing || event.repeat) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    if (event.code === "Escape") { capturing = false; status.textContent = "Выбор отменён."; return; }
    if (!core.singleKey(event) || !core.validCode(event.code) || event.isComposing) {
      status.textContent = "Нужна одна клавиша без сочетаний.";
      return;
    }
    capturing = false;
    save(event.code);
  }, true);
})();
