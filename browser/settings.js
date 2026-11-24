(function () {
  "use strict";
  const core = globalThis.TelemostRightShiftCore;
  const api = typeof browser !== "undefined" ? browser : chrome;
  const normalize = value => core.validCode(value) ? value : "ShiftRight";
  function read() {
    if (typeof browser !== "undefined")
      return api.storage.local.get("hotkeyCode").then(data => normalize(data.hotkeyCode), () => "ShiftRight");
    return new Promise(resolve => api.storage.local.get("hotkeyCode", data => {
      const error = api.runtime.lastError;
      resolve(error ? "ShiftRight" : normalize(data.hotkeyCode));
    }));
  }
  function write(code) {
    if (!core.validCode(code)) return Promise.reject(new Error("Неизвестный код клавиши"));
    if (typeof browser !== "undefined") return api.storage.local.set({ hotkeyCode: code });
    return new Promise((resolve, reject) => api.storage.local.set({ hotkeyCode: code }, () => {
      const error = api.runtime.lastError;
      if (error) reject(new Error(error.message)); else resolve();
    }));
  }
  function subscribe(callback) {
    api.storage.onChanged.addListener((changes, area) => {
      if (area === "local" && changes.hotkeyCode) callback(normalize(changes.hotkeyCode.newValue));
    });
  }
  globalThis.TelemostHotkeySettings = Object.freeze({ read, write, subscribe });
})();
