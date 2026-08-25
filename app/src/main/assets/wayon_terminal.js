(() => {
  "use strict";

  const terminal = {
    connected: false,
    connecting: false,
    output: "",
    decoder: new TextDecoder("utf-8"),
  };
  const byId = id => document.getElementById(id);
  const overlay = byId("terminal-overlay");
  const screen = byId("terminal-screen");
  const state = byId("terminal-state");
  const stateLabel = byId("terminal-state-label");
  const input = byId("terminal-command-input");
  const send = byId("btn-terminal-send");
  const keyCard = byId("terminal-key-card");
  const publicKey = byId("terminal-public-key");
  const quickActions = [...document.querySelectorAll("[data-terminal-command]")];
  const welcome = "Wayon Cloud 원격 터미널\nOffroad 장치에 암호화된 세션으로 연결합니다.\n\n";

  function vehicleOnroad() {
    const feed = window.hylink?.data?.feed || {};
    const value = feed.state?.onroad;
    return value === true || value === 1;
  }

  function setState(next, message) {
    terminal.connected = next === "connected";
    terminal.connecting = next === "connecting";
    state.className = `terminal-state ${next}`;
    stateLabel.textContent = message || ({
      connected: "연결됨",
      connecting: "연결 중",
      error: "연결 실패",
      closed: "연결 종료",
    }[next] || "연결 대기");
    input.disabled = !terminal.connected;
    send.disabled = !terminal.connected;
    quickActions.forEach(button => { button.disabled = !terminal.connected; });
  }

  function cleanAnsi(text) {
    return text
      .replace(/\x1b\][^\x07]*(?:\x07|\x1b\\)/g, "")
      .replace(/\x1b\[[0-?]*[ -\/]*[@-~]/g, "")
      .replace(/\x1b[()][A-Z0-9]/g, "")
      .replace(/\r/g, "");
  }

  function appendOutput(text) {
    const clean = cleanAnsi(text);
    for (const character of clean) {
      if (character === "\b") terminal.output = terminal.output.slice(0, -1);
      else if (character === "\n" || character === "\t" || character >= " ") terminal.output += character;
    }
    if (terminal.output.length > 120000) terminal.output = terminal.output.slice(-100000);
    screen.textContent = terminal.output;
    screen.scrollTop = screen.scrollHeight;
  }

  function resetOutput() {
    terminal.output = welcome;
    screen.textContent = terminal.output;
  }

  function showPublicKey() {
    const key = window.Android?.getWayonTerminalPublicKey?.() || "";
    publicKey.textContent = key;
    keyCard.hidden = !key;
  }

  function openTerminal() {
    if (!window.hylink?.token) {
      window.toast?.("Wayon Cloud 키를 먼저 저장해 주세요.");
      return;
    }
    if (vehicleOnroad()) {
      window.toast?.("원격 터미널은 Offroad에서만 사용할 수 있습니다.");
      return;
    }
    overlay.classList.add("visible");
    overlay.setAttribute("aria-hidden", "false");
    keyCard.hidden = true;
    resetOutput();
    setState("connecting", "보안 세션 준비");
    window.Android?.connectWayonTerminal?.();
  }

  function closeTerminal() {
    window.Android?.disconnectWayonTerminal?.();
    overlay.classList.remove("visible");
    overlay.setAttribute("aria-hidden", "true");
    setState("closed", "연결 종료");
  }

  function writeCommand(command) {
    if (!terminal.connected || !command) return;
    window.Android?.sendWayonTerminalInput?.(`${command}\n`);
  }

  window.onWayonTerminalState = (next, message) => {
    setState(next, message);
    if (next === "connected") {
      keyCard.hidden = true;
      input.focus();
    } else if (next === "auth_required") {
      setState("error", message || "SSH 키 등록 필요");
      appendOutput("\n이 휴대폰의 SSH 공개키가 차량에 등록되지 않았습니다.\n");
      showPublicKey();
    } else if (next === "error") {
      appendOutput(`\n${message || "원격 터미널 연결에 실패했습니다."}\n`);
    }
  };

  window.onWayonTerminalOutput = encoded => {
    try {
      const binary = atob(encoded || "");
      const bytes = Uint8Array.from(binary, character => character.charCodeAt(0));
      appendOutput(terminal.decoder.decode(bytes, { stream: true }));
    } catch (_) {
      appendOutput("\n[터미널 출력 디코딩 오류]\n");
    }
  };

  window.updateWayonTerminalAvailability = () => {
    const available = byId("terminal-availability");
    const button = byId("btn-open-terminal");
    const caption = byId("terminal-launch-caption");
    const hasFeed = Boolean(window.hylink?.data?.feed?.state);
    const onroad = vehicleOnroad();
    available.textContent = !hasFeed ? "상태 확인 중" : onroad ? "ONROAD 차단" : "OFFROAD 사용 가능";
    button.disabled = !window.hylink?.token || !hasFeed || onroad;
    caption.textContent = onroad
      ? "주행 중에는 Wayon 릴레이가 터미널을 차단합니다."
      : "Wayon 키로 해당 동글의 SSH 세션에 연결합니다.";
    if (onroad && overlay.classList.contains("visible")) closeTerminal();
  };

  const previousBack = window.handleHylinkBack;
  window.handleHylinkBack = () => {
    if (overlay.classList.contains("visible")) {
      closeTerminal();
      return true;
    }
    return previousBack?.() || false;
  };

  byId("btn-open-terminal").addEventListener("click", openTerminal);
  byId("btn-close-terminal").addEventListener("click", closeTerminal);
  byId("terminal-command-form").addEventListener("submit", event => {
    event.preventDefault();
    const command = input.value.trim();
    input.value = "";
    writeCommand(command);
  });
  quickActions.forEach(button => button.addEventListener("click", () => writeCommand(button.dataset.terminalCommand)));
  byId("btn-copy-terminal-key").addEventListener("click", () => {
    const text = publicKey.textContent || "";
    const field = document.createElement("textarea");
    field.value = text;
    field.style.position = "fixed";
    field.style.opacity = "0";
    document.body.appendChild(field);
    field.select();
    document.execCommand("copy");
    field.remove();
    window.toast?.("SSH 공개키를 복사했습니다.");
  });

  resetOutput();
  setState("closed", "연결 대기");
  window.updateWayonTerminalAvailability();
})();
