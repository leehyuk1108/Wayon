export function databaseLimitResponse(error, now = Date.now()) {
  const seen = new Set();
  let current = error;
  for (let depth = 0; current && depth < 5 && !seen.has(current); depth++, current = current.cause) {
    seen.add(current);
    const message = typeof current.message === 'string' ? current.message : '';
    if (!/exceeded D1's free tier daily (?:row )?(?:read|write) limit/i.test(message)) continue;
    const date = new Date(now);
    const retryAtMs = Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate() + 1);
    return {body: {ok: false, error: 'database_daily_limit', code: 'database_daily_limit',
      message: '서버 데이터베이스의 오늘 사용 한도를 초과했습니다. 매일 오전 9시(한국시간)에 초기화됩니다. 비밀번호 문제는 아닙니다.',
      retryAt: new Date(retryAtMs).toISOString()},
    headers: {'retry-after': String(Math.max(1, Math.ceil((retryAtMs - now) / 1000)))}};
  }
  return null;
}
