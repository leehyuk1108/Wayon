/* The original Android UI remains the renderer. This file owns web-only login/install/push. */
(() => {
  let session = null;
  let registration = null;
  let authRevision = 0;
  const login = document.createElement('section');
  login.id = 'pwa-login';
  login.innerHTML = `<form><img src="/app-icon-v2-192.png" alt=""><h1>My Traverse</h1>
    <label for="pwa-password">접속 비밀번호</label>
    <input id="pwa-password" type="password" autocomplete="current-password" required maxlength="128">
    <button type="submit">로그인</button><p id="pwa-error" role="alert"></p></form>`;
  document.body.append(login);
  // A device that has logged in before shows the app at once and checks the session behind it; the
  // password form appears only when the server says the session is gone. The hint holds no secret.
  const AUTH_HINT = 'traverse-web-authenticated';
  const hint = (value) => {
    try {
      if (value === undefined) return window.localStorage?.getItem(AUTH_HINT) === '1';
      if (value) window.localStorage?.setItem(AUTH_HINT, '1'); else window.localStorage?.removeItem(AUTH_HINT);
    } catch { /* storage can be unavailable; the session check still decides */ }
    return false;
  };
  login.hidden = true;
  document.body.dataset.pwa = hint() ? 'resuming' : 'checking';

  async function api(path, body, method = 'POST') {
    const csrfToken = window.TraverseWeb?.csrfToken() || session?.csrfToken;
    let response;
    try {
      response = await fetch(path, {method, credentials:'same-origin', cache:'no-store',
        headers: {'content-type':'application/json', ...(csrfToken ? {'x-csrf-token':csrfToken} : {})},
        ...(body === undefined ? {} : {body:JSON.stringify(body)}),
      });
    } catch { throw new Error('서버 연결을 확인해 주세요.'); }
    if (response.status === 401 && path !== '/api/login') lock();
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.message || '요청을 처리하지 못했습니다.');
    return result;
  }

  function lock() {
    authRevision++;
    session = null;
    hint(false);
    window.TraverseWeb?.stop();
    document.body.dataset.pwa = 'locked';
    login.hidden = false;
  }

  async function restore() {
    const revision = authRevision;
    const result = await api('/api/session', undefined, 'GET');
    if (revision !== authRevision) return;
    if (!result.authenticated) { lock(); return; }
    session = result;
    hint(true);
    login.hidden = true;
    document.body.dataset.pwa = 'ready';
    login.querySelector('input').value = '';
    await window.TraverseWeb.start(result);
    await updatePushStatus().catch(() => { status.textContent='알림 설정에 연결하지 못했습니다.'; });
  }

  login.querySelector('form').addEventListener('submit', async event => {
    event.preventDefault();
    const button = login.querySelector('button');
    const error = document.getElementById('pwa-error');
    button.disabled = true; error.textContent = '';
    try {
      await api('/api/login', {password:login.querySelector('input').value});
      await restore();
    } catch (failure) { error.textContent = failure.message; }
    finally { button.disabled = false; }
  });

  const actions = document.createElement('section');
  actions.className = 'pwa-actions';
  actions.innerHTML = `<h4>My Traverse</h4><div class="pwa-buttons">
    <button id="pwa-notifications" type="button">알림 켜기</button>
    <button id="pwa-test" type="button">테스트 알림</button>
    <button id="pwa-logout" type="button">로그아웃</button>
    </div><p id="pwa-push-status" role="status"></p>`;
  document.querySelector('#tab-settings .settings-section')?.prepend(actions);
  const status = actions.querySelector('#pwa-push-status');
  const notifyButton = actions.querySelector('#pwa-notifications');
  const testButton = actions.querySelector('#pwa-test');
  const settingsButton=document.getElementById('btnSecretSettings');
  if (settingsButton) {
    settingsButton.setAttribute('role','button'); settingsButton.tabIndex=0;
    settingsButton.setAttribute('aria-label','설정'); settingsButton.title='설정';
    settingsButton.innerHTML='<i data-lucide="settings-2" aria-hidden="true"></i>';
    settingsButton.addEventListener('keydown',event=>{
      if (event.key==='Enter'||event.key===' ') { event.preventDefault(); settingsButton.click(); }
    });
    window.lucide?.createIcons();
  }

  for (const item of document.querySelectorAll('.footer-nav .nav-item')) {
    item.setAttribute('role', 'button');
    item.tabIndex = 0;
    item.setAttribute('aria-label', item.querySelector('span')?.textContent.trim() || 'Navigation');
    const syncCurrent = () => {
      if (item.classList.contains('active')) item.setAttribute('aria-current', 'page');
      else item.removeAttribute('aria-current');
    };
    syncCurrent();
    new MutationObserver(syncCurrent).observe(item, {attributes: true, attributeFilter: ['class']});
    item.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); item.click(); }
    });
  }

  // Android-only configuration stays out of the web settings; original DOM IDs remain available.
  for (const id of ['api-input-container','wayon-cloud-key-input-container','toggleAutoRefresh']) {
    document.getElementById(id)?.closest('.control-group-card')?.setAttribute('hidden','');
  }
  for (const id of ['btnSetupBluetooth','btnGoToDev']) {
    document.getElementById(id)?.closest('.control-group-card')?.setAttribute('hidden','');
  }
  async function updatePushStatus() {
    const supported = 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
    if (!supported) {
      status.textContent = /iPhone|iPad/.test(navigator.userAgent)
        ? 'Safari에서 홈 화면에 추가한 뒤 앱을 열어주세요.' : '이 브라우저는 알림을 지원하지 않습니다.';
      notifyButton.disabled = true; testButton.disabled = true; return;
    }
    registration ||= await navigator.serviceWorker.register('/sw.js');
    await navigator.serviceWorker.ready;
    const subscription = await registration.pushManager.getSubscription();
    notifyButton.textContent = subscription ? '알림 끄기' : '알림 켜기';
    testButton.disabled = !subscription;
    status.textContent = subscription ? '알림 켜짐' : Notification.permission === 'denied'
      ? '알림 권한이 차단되어 있습니다.' : '알림 꺼짐';
    if (subscription && session) await api('/api/push/subscribe', {subscription:subscription.toJSON()});
  }
  notifyButton.addEventListener('click', async () => {
    notifyButton.disabled = true;
    try {
      const current = await registration?.pushManager.getSubscription();
      if (current) {
        await api('/api/push/unsubscribe', {endpoint:current.endpoint});
        await current.unsubscribe();
      } else {
        const permission = await Notification.requestPermission();
        if (permission !== 'granted') throw new Error('알림 권한이 필요합니다.');
        const {publicKey} = await api('/api/push/key', undefined, 'GET');
        const bytes = Uint8Array.from(atob(publicKey.replace(/-/g,'+').replace(/_/g,'/')), x => x.charCodeAt(0));
        const subscription = await registration.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:bytes});
        try { await api('/api/push/subscribe', {subscription:subscription.toJSON()}); }
        catch (error) { await subscription.unsubscribe(); throw error; }
      }
      await updatePushStatus();
    } catch (error) { status.textContent = error.message; }
    finally { notifyButton.disabled = false; }
  });
  testButton.addEventListener('click', async () => {
    testButton.disabled = true;
    try {
      const result = await api('/api/push/test', {});
      status.textContent = result.sent ? '테스트 알림을 전송했습니다.' : '알림 전송에 실패했습니다.';
    } catch (error) { status.textContent = error.message; }
    finally { testButton.disabled = false; }
  });
  actions.querySelector('#pwa-logout').addEventListener('click', async () => {
    try {
      await api('/api/logout', {});
      lock();
      try {
        const subscription = await registration?.pushManager.getSubscription();
        if (subscription) await subscription.unsubscribe();
      } finally { location.replace('/'); }
    } catch (error) { window.showStatus?.(error.message, 'danger'); }
  });
  window.addEventListener('traverse-auth-expired', lock);
  window.addEventListener('traverseweb:sessionlost', lock);
  window.addEventListener('traverseweb:sessionupdated', event => {
    if (session) session = {...session, csrfToken:event.detail.csrfToken};
  });
  navigator.serviceWorker?.addEventListener('message', event => {
    if (event.data?.type === 'refresh') window.Android?.refreshWayonCloudData();
  });
  window.addEventListener('pageshow', event => {
    if (!event.persisted) return;
    if (session) window.TraverseWeb.refreshSession();
    else restore().catch(error => { lock(); document.getElementById('pwa-error').textContent = error.message; });
  });
  restore().catch(error => { lock(); document.getElementById('pwa-error').textContent = error.message || '서버 연결을 확인해 주세요.'; });
})();
