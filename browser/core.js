/* Pure decisions shared by the content script and dependency-free Node tests. */
(function (root) {
  "use strict";
  function isMicLabel(value) {
    const label = String(value || "").trim().replace(/\s+/g, " ").toLowerCase();
    return /^(?:(?:включить|выключить|отключить) (?:свой )?микрофон|(?:enable|disable|mute|unmute) (?:your |the )?microphone|turn (?:on|off) (?:your |the )?microphone|turn (?:your |the )?microphone (?:on|off))(?:\s*\([^()]*\))?$/.test(label);
  }
  function singleKey(event) {
    return (!event.ctrlKey || /^Control(?:Left|Right)$/.test(event.code)) &&
      (!event.altKey || /^Alt(?:Left|Right)$/.test(event.code)) &&
      (!event.metaKey || /^Meta(?:Left|Right)$/.test(event.code)) &&
      (!event.shiftKey || /^Shift(?:Left|Right)$/.test(event.code));
  }
  function validCode(code) {
    return typeof code === "string" && /^[A-Za-z][A-Za-z0-9]{0,31}$/.test(code) && code !== "Unidentified";
  }
  function shouldHandle(event, pageFocused, editing, configuredCode = "ShiftRight") {
    return pageFocused && !editing && event.code === configuredCode &&
      !event.repeat && singleKey(event) &&
      !event.isComposing && !event.defaultPrevented;
  }
  function uniqueCandidate(buttons, eligible) {
    const matches = buttons.filter(button => eligible(button) &&
      [button.getAttribute("aria-label"), button.getAttribute("title"), button.textContent]
        .some(isMicLabel));
    return matches.length === 1 ? matches[0] : null;
  }
  const api = Object.freeze({ isMicLabel, shouldHandle, uniqueCandidate, singleKey, validCode });
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.TelemostRightShiftCore = api;
})(globalThis);
