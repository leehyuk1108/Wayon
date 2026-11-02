/* The original Android UI remains the renderer. This file owns web-only login/install/push. */
(() => {
  let session = null;
  let registration = null;
  const login = document.createElement('section');
  login.id = 'pwa-login';
  login.innerHTML = `<form><img src="/app-icon-v2-192.png" alt=""><h1>My Traverse</h1>
    <label for="pwa-password">접속 비밀번호</label>
    <input id="pwa-password" type="password" autocomplete="current-password" required maxlength="128">
    <button type="submit">로그인</button><p id="pwa-error" role="alert"></p></form>`;
  document.body.append(login);

  async function api(path, body, method = 'POST') {
    const response = await fetch(path, {method, credentials:'same-origin', cache:'no-store',
      headers: {'content-type':'application/json', ...(session?.csrfToken ? {'x-csrf-token':session.csrfToken} : {})},
      ...(body === undefined ? {} : {body:JSON.stringify(body)}),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.message || '요청을 처리하지 못했습니다.');
    return result;
  }

  function lock() {
    session = null;
    window.TraverseWeb?.stop();
    document.body.dataset.pwa = 'locked';
    login.hidden = false;
  }

  async function restore() {
    const result = await api('/api/session', undefined, 'GET');
    if (!result.authenticated) { lock(); return; }
    session = result;
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
      const subscription = await registration?.pushManager.getSubscription();
      if (subscription) await subscription.unsubscribe();
      lock(); location.replace('/');
    } catch (error) { window.showStatus?.(error.message, 'danger'); }
  });
  window.addEventListener('traverse-auth-expired', lock);
  window.addEventListener('traverseweb:sessionlost', lock);
  navigator.serviceWorker?.addEventListener('message', event => {
    if (event.data?.type === 'refresh') window.Android?.refreshWayonCloudData();
  });
  window.addEventListener('pageshow', event => { if (event.persisted) restore().catch(lock); });
  restore().catch(() => { lock(); document.getElementById('pwa-error').textContent = '서버 연결을 확인해 주세요.'; });
})();
