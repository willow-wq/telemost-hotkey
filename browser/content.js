(function () {
  "use strict";
  const core = globalThis.TelemostRightShiftCore;
  let configuredCode = null;
  let changed = false;
  globalThis.TelemostHotkeySettings.subscribe(code => { changed = true; configuredCode = code; });
  globalThis.TelemostHotkeySettings.read().then(code => { if (!changed) configuredCode = code; });
  function editing(event) {
    return event.composedPath().some(node => node instanceof Element &&
      (node.isContentEditable || node.closest("input, textarea, select, [role='textbox']")));
  }
  function eligible(button) {
    if (button.matches(":disabled") || button.getAttribute("aria-disabled") === "true" ||
        button.closest("[hidden], [inert], [aria-hidden='true']")) return false;
    for (let node = button; node instanceof Element; node = node.parentElement) {
      const style = getComputedStyle(node);
      if (style.display === "none" || style.visibility !== "visible" || Number(style.opacity) === 0)
        return false;
    }
    const rect = button.getBoundingClientRect();
    if (rect.width <= 0 || rect.height <= 0) return false;
    const front = document.elementFromPoint(rect.left + rect.width / 2, rect.top + rect.height / 2);
    return front !== null && button.contains(front);
  }
  document.addEventListener("keydown", event => {
    if (!core.shouldHandle(event, document.hasFocus() && document.visibilityState === "visible",
                           editing(event), configuredCode)) return;
    const button = core.uniqueCandidate(Array.from(document.querySelectorAll("button, [role='button']")), eligible);
    if (!button) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    button.click();
  }, true);
})();
