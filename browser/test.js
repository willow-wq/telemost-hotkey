"use strict";
const assert = require("node:assert/strict");
const { test } = require("node:test");
const core = require("./core.js");

test("only explicit microphone on/off labels match", () => {
  for (const label of ["Включить микрофон", "Выключить микрофон", "Отключить свой микрофон",
    "Unmute microphone", "Mute your microphone", "Turn microphone off", "Turn on the microphone",
    "  Выключить   микрофон (Ctrl+D) "])
    assert.equal(core.isMicLabel(label), true, label);
  for (const label of ["Mute", "Звук", "Микрофон", "Выключить камеру", "Mute all",
    "Выключить микрофон участника", "Mute microphone for everyone", "Настройки микрофона", ""])
    assert.equal(core.isMicLabel(label), false, label);
});
test("right Shift requires focus, no editing, repeat or other modifiers", () => {
  const event = { code: "ShiftRight", shiftKey: true };
  assert.equal(core.shouldHandle(event, true, false), true);
  assert.equal(core.shouldHandle(event, false, false), false);
  assert.equal(core.shouldHandle(event, true, true), false);
  assert.equal(core.shouldHandle({ code: "ShiftLeft" }, true, false), false);
  for (const flag of ["repeat", "ctrlKey", "altKey", "metaKey", "isComposing", "defaultPrevented"])
    assert.equal(core.shouldHandle({ ...event, [flag]: true }, true, false), false, flag);
});
test("candidate must be unique and eligible", () => {
  const button = (label, visible = true) => ({ getAttribute: name => name === "aria-label" ? label : null,
    textContent: "", visible });
  const first = button("Включить микрофон");
  const second = button("Mute microphone");
  const eligible = item => item.visible;
  assert.equal(core.uniqueCandidate([first], eligible), first);
  assert.equal(core.uniqueCandidate([first, second], eligible), null);
  assert.equal(core.uniqueCandidate([button("Mute microphone", false)], eligible), null);
  assert.equal(core.uniqueCandidate([button("Mute"), first], eligible), first);
  assert.equal(core.uniqueCandidate([], eligible), null);
});
test("configured single key replaces default and excludes chords", () => {
  assert.equal(core.shouldHandle({ code: "F8" }, true, false, "F8"), true);
  assert.equal(core.shouldHandle({ code: "ShiftRight" }, true, false, "F8"), false);
  assert.equal(core.shouldHandle({ code: "KeyM", shiftKey: true }, true, false, "KeyM"), false);
  assert.equal(core.shouldHandle({ code: "ControlRight", ctrlKey: true }, true, false, "ControlRight"), true);
  assert.equal(core.validCode("Unidentified"), false);
  assert.equal(core.validCode("Ctrl+M"), false);
  assert.equal(core.validCode("KeyM"), true);
});
test("settings persist and observe updates in Chrome and Firefox API forms", async () => {
  const vm = require("node:vm");
  const fs = require("node:fs");
  for (const promiseApi of [false, true]) {
    let data = {};
    let listener;
    const storage = {
      onChanged: { addListener: callback => { listener = callback; } },
      local: {
        get: (key, callback) => promiseApi ? Promise.resolve(data) : callback(data),
        set: (update, callback) => {
          data = { ...data, ...update };
          if (promiseApi) return Promise.resolve();
          callback();
        }
      }
    };
    const context = { TelemostRightShiftCore: core };
    context[promiseApi ? "browser" : "chrome"] = { storage, runtime: {} };
    vm.runInNewContext(fs.readFileSync(require.resolve("./settings.js"), "utf8"), context);
    const settings = context.TelemostHotkeySettings;
    assert.equal(await settings.read(), "ShiftRight");
    await settings.write("F8");
    assert.equal(await settings.read(), "F8");
    await assert.rejects(settings.write("Ctrl+M"));
    let observed;
    settings.subscribe(code => { observed = code; });
    listener({ hotkeyCode: { newValue: "KeyM" } }, "local");
    assert.equal(observed, "KeyM");
    listener({ hotkeyCode: { newValue: "Unidentified" } }, "local");
    assert.equal(observed, "ShiftRight");
  }
});
