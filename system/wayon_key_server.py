#!/usr/bin/env python3
import html
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


CONFIG_PATH = Path("/data/wayon_cloud/config.json")
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 1108


def config_value(name: str) -> str:
  try:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return str(config.get(name) or "")
  except (OSError, TypeError, ValueError):
    return ""


def page() -> bytes:
  key = html.escape(config_value("token"), quote=True)
  device_id = html.escape(config_value("device_id"), quote=True)
  return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="color-scheme" content="dark">
  <title>Wayon Cloud Key</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; padding: 24px;
      background: #0b0c0e; color: #f5f5f7; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }}
    main {{ width: min(620px, 100%); }}
    .eyebrow {{ color: #8e8e93; font-size: 13px; font-weight: 600; }}
    h1 {{ margin: 10px 0 8px; font-size: clamp(32px, 8vw, 54px); line-height: 1; letter-spacing: 0; }}
    p {{ color: #a1a1a6; line-height: 1.55; margin: 0 0 26px; }}
    .key {{ padding: 18px; border: 1px solid #2c2c2e; border-radius: 8px; background: #151517;
      font: 600 15px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace; overflow-wrap: anywhere;
      user-select: all; }}
    button {{ width: 100%; margin-top: 12px; min-height: 52px; border: 0; border-radius: 8px;
      background: #f5f5f7; color: #111113; font-size: 16px; font-weight: 700; cursor: pointer; }}
    button:active {{ transform: scale(.99); }}
    .meta {{ display: flex; justify-content: space-between; gap: 16px; margin-top: 16px;
      color: #6e6e73; font-size: 12px; }}
  </style>
</head>
<body>
  <main>
    <div class="eyebrow">WAYON / OFFROAD LOCAL ACCESS</div>
    <h1>Cloud Key</h1>
    <p>이 키 하나로 차량 데이터, 알림, 360 Live와 원격 터미널에 접근합니다.</p>
    <div class="key" id="key">{key or "키를 준비하는 중입니다."}</div>
    <button type="button" id="copy">키 복사</button>
    <div class="meta"><span>Dongle {device_id or "Unknown"}</span><span>Port {LISTEN_PORT}</span></div>
  </main>
  <script>
    const button = document.querySelector('#copy');
    button.addEventListener('click', async () => {{
      const value = document.querySelector('#key').textContent.trim();
      try {{
        if (navigator.clipboard) await navigator.clipboard.writeText(value);
        else throw new Error('fallback');
      }} catch (_) {{
        const range = document.createRange();
        range.selectNodeContents(document.querySelector('#key'));
        const selection = window.getSelection();
        selection.removeAllRanges(); selection.addRange(range);
        document.execCommand('copy'); selection.removeAllRanges();
      }}
      button.textContent = '복사됨';
      setTimeout(() => button.textContent = '키 복사', 1600);
    }});
  </script>
</body>
</html>""".encode("utf-8")


class Handler(BaseHTTPRequestHandler):
  def do_GET(self) -> None:
    if self.path not in ("/", "/index.html"):
      self.send_error(404)
      return
    body = page()
    self.send_response(200)
    self.send_header("Content-Type", "text/html; charset=utf-8")
    self.send_header("Content-Length", str(len(body)))
    self.send_header("Cache-Control", "no-store")
    self.send_header("X-Content-Type-Options", "nosniff")
    self.send_header("X-Frame-Options", "DENY")
    self.end_headers()
    self.wfile.write(body)

  def log_message(self, _format: str, *_args) -> None:
    pass


def main() -> None:
  server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), Handler)
  print(f"Wayon key page: listening on {LISTEN_HOST}:{LISTEN_PORT}", flush=True)
  server.serve_forever()


if __name__ == "__main__":
  main()
