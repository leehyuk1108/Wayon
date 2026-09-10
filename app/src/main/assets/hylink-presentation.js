/* Presentation only. Never authorizes a vehicle operation or changes polling. */
(function (root) {
  'use strict';
  const number = value => value === null || value === undefined || typeof value === 'boolean' || (typeof value === 'string' && !value.trim())
    ? null : Number.isFinite(Number(value)) ? Number(value) : null;
  const flag = value => value === true || value === 1 ? true : value === false || value === 0 ? false : null;
  function freshness(updated, onroad, now = Date.now()) {
    const time = Date.parse(updated || '');
    if (!Number.isFinite(time) || time > now + 60000) return 'unknown';
    return now - time > (onroad === true ? 60000 : 900000) ? 'stale' : 'recent';
  }
  function summary(state = {}, raw = {}, options = {}) {
    const onroad = flag(state.onroad);
    const ignition = flag(state.ignition ?? raw.ignition);
    const updated = state.updated_at || raw.updatedAt;
    const fresh = freshness(updated, onroad, options.now);
    const condition = !options.hasKey ? 'unlinked' : options.error ? 'error' : fresh;
    const known = fresh !== 'unknown';
    const status = !known ? '확인 대기' : onroad === true ? '주행 중' : ignition === true ? '시동 켜짐'
      : onroad === false && ignition === false ? '주차 중' : '상태 확인 중';
    const connection = {unlinked:'차량 연결 필요',error:'연결 확인 필요',unknown:'첫 데이터 대기',stale:'업데이트 지연',recent:'최근 데이터 수신'}[condition];
    const description = condition === 'unlinked' ? '설정에서 차량 연결 키를 등록하세요.'
      : condition === 'error' ? '새 데이터를 받지 못했어요. 마지막 수신 정보를 표시합니다.'
      : condition === 'stale' ? '마지막 수신 상태입니다. 현재 차량 상태와 다를 수 있어요.'
      : condition === 'unknown' ? '차량 데이터를 받으면 상태가 표시됩니다.'
      : raw.openpilot?.active === true ? '주행 보조 활성 · 마지막 수신 기준'
      : status === '주차 중' ? '비주행 상태 · 마지막 수신 기준' : '마지막 수신 기준';
    return {condition, connection, description, status, updated, known, onroad, fresh};
  }
  const api = {number, flag, freshness, summary};
  if (typeof module !== 'undefined') module.exports = api;
  root.HylinkPresentation = api;
})(typeof window !== 'undefined' ? window : globalThis);
