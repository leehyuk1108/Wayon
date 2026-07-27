#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

patterns=(
  'AIza[0-9A-Za-z_-]{20,}'
  '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----'
  'Authorization[^[:cntrl:]]*Bearer[[:space:]]+[0-9A-Za-z._-]{16,}'
  'https://mp\.gmone\.co\.kr/api\?[^[:space:]"]*(id|key)='
  '[A-Za-z0-9._%+-]+@(gmail|naver|daum|kakao|outlook|hotmail|icloud|protonmail)\.'
)

status=0
for pattern in "${patterns[@]}"; do
  if rg -n -i \
    --glob '!local.properties' \
    --glob '!app/google-services.json' \
    --glob '!scripts/check-secrets.sh' \
    --glob '!**/build/**' \
    -- "$pattern" "$root"; then
    status=1
  fi
done

if [[ "$status" -ne 0 ]]; then
  echo "Potential secret or personal identifier found." >&2
  exit "$status"
fi

echo "No committed-source secret patterns found."
