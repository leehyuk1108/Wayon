/* Production Wayon dashboard. No demo data; native owns authentication and polling. */
const $=id=>document.getElementById(id);
const icons=()=>window.lucide?.createIcons();
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icon=name=>'<i data-lucide="'+name+'"></i>';
const num=CloudOverview.number;
const fixed=(v,d=0)=>v===null||!Number.isFinite(v)?'—':v.toFixed(d);
const list=v=>Array.isArray(v)?v:[];
const date=v=>Number.isFinite(Date.parse(v))?new Intl.DateTimeFormat('ko-KR',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}).format(new Date(v)):'시각 미수신';
const scaled=(v,f=1,d=0)=>fixed(num(v)===null?null:num(v)*f,d);
const duration=v=>num(v)===null?'—':Math.round(num(v)/60)+'분';
const clipDuration=v=>num(v)===null?'길이 미수신':Math.round(num(v))+'초';
const isVideoCapture=v=>v.kind==='clip'||v.kind==='video';
const point=v=>{const lat=num(v?.latitude??v?.lat),lon=num(v?.longitude??v?.lon??v?.lng);return lat!==null&&lon!==null&&Math.abs(lat)<=90&&Math.abs(lon)<=180?[lon,lat]:null};
const hylink={token:'',baseUrl:'',data:null};window.hylink=hylink;
let data={},model,map,marker,recordFilter='trips',lastFocus,currentPage='now';
let myMarker,myPosition,locationRequest=0,locationPending=false,mapReturnFocus,mapTouched=false;
let recordLimit=8,recordSignature='',detailRequest=0,tripMap,mediaEpoch=0;
const mediaCache=new Map(),mediaPending=new Map();
window.getWayonCloudViewToken=()=>hylink.token;
window.getWayonCloudBaseUrl=()=>hylink.baseUrl;
function toast(message){$('toast').textContent=message;$('toast').classList.add('visible');clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').classList.remove('visible'),5000)}
window.toast=toast;
function render(){
  model=CloudOverview.derive(data);
  // A valid old position stays a last-received location, never a phone position.
  if(!model.point)model.point=point(model.raw.gps);
  $('vehicle-state').textContent=!hylink.token?'차량을 연결해 주세요':(model.stale||data.error?'마지막 상태 · ':'')+model.status;
  $('freshness-label').textContent=!hylink.token?'연결 키로 내 차량의 정보를 받아보세요':model.received;
  $('state-symbol').innerHTML=icon(CloudOverview.flag(model.state.onroad)===true?'navigation':'circle-parking');
  const attention=hylink.token?model.alerts[0]:null;
  $('attention').hidden=!attention;
  $('attention').innerHTML=attention?icon(attention.icon)+'<div><strong>'+esc(attention.title)+'</strong><p>'+esc(attention.detail)+'</p><button id="all-alerts">자세히 확인하기 →</button></div>':'';
  $('all-alerts')?.addEventListener('click',showAlerts);
  const accuracy=num(model.raw.gps?.accuracyM);
  $('location-caption').textContent=model.point?'마지막 수신 위치'+(model.raw.gps?.fresh===false?' · 이전 GPS 기록':accuracy!==null?' · GPS 오차 약 '+Math.round(accuracy)+'m':''):'위치 수신 대기';
  const t=model.trip;
  $('recent-trip').disabled=!t;
  $('trip-distance').textContent=scaled(t?.distance_m,.001,1);
  $('trip-duration').textContent=duration(t?.duration_s);
  $('trip-average').textContent=scaled(t?.avg_speed_mps,3.6);
  document.querySelector('.journey-date').textContent=t?date(t.started_at):data.trips?'아직 저장된 주행이 없어요':'주행 기록 수신 대기';
  $('photo-count').textContent=data.snapshots?'수신된 사진 '+model.photos.length+'장':'사진 수신 대기';
  $('vehicle-age').textContent=model.received+' 기준이에요.';
  $('locate-button').disabled=!model.point;
  $('btnWayonLive').disabled=!hylink.token;
  $('photos-button').disabled=!hylink.token;
  document.querySelector('.map-section').hidden=!model.point;
  if(!model.point&&$('map-dialog').open)$('map-dialog').close();
  ensureMap();
  if(map&&marker){if(model.point){marker.setLngLat(model.point).addTo(map);if(!$('map-dialog').open)map.jumpTo({center:model.point})}else marker.remove()}
  renderVehicle();
  if(currentPage==='records')renderRecords();
  window.updateWayonTerminalAvailability?.();
  icons();
}
function empty(name,title,copy){return '<div class="empty-state">'+icon(name)+'<h3>'+esc(title)+'</h3><p>'+esc(copy)+'</p></div>'}
function navigate(name){
  currentPage=name;
  document.querySelectorAll('.page').forEach(p=>{p.hidden=p.id!=='page-'+name;p.classList.toggle('active',!p.hidden)});
  document.querySelectorAll('.tab-bar button').forEach(b=>{b.classList.toggle('selected',b.dataset.navigate===name);if(b.dataset.navigate===name)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')});
  window.scrollTo({top:0,behavior:'instant'});
  if(name==='now')requestAnimationFrame(()=>map?.resize());
  if(name==='records')renderRecords();
}
function closeTrip(){detailRequest++;tripMap?.remove();tripMap=null}
function showSheet(title,content){
  closeTrip();lastFocus=document.activeElement;
  $('sheet-title').textContent=title;$('sheet-content').innerHTML=content;
  if(!$('sheet').open)$('sheet').showModal();
  icons();$('close-sheet').focus();
}
function showAlerts(){
  showSheet('확인할 수신 정보',model.alerts.map(a=>'<div class="sheet-choice">'+icon(a.icon)+'<span><b>'+esc(a.title)+'</b><small>'+esc(a.detail)+'</small></span></div>').join('')+'<button class="primary-button" id="retry-data">다시 가져오기</button>');
  $('retry-data').onclick=()=>{$('sheet').close();refresh()};
}
function refresh(){if(hylink.token)window.Android?.refreshWayonData?.();else showConnection()}
function showConnection(){
  showSheet('차량 연결','<p class="sheet-copy">차량의 Wayon 연결 키를 입력해 주세요. 키는 이 휴대폰에만 저장되며 다른 사람과 공유하면 안 돼요.</p><label for="connection-key">차량 연결 키</label><input id="connection-key" type="password" autocomplete="off" autocapitalize="none" spellcheck="false" placeholder="새 연결 키 붙여넣기"><button class="primary-button" id="save-key">저장 및 연결</button><button class="sheet-choice" id="refresh-data">'+icon('refresh-cw')+'새로고침</button>'+(hylink.token?'<button class="sheet-choice danger-text" id="disconnect-key">'+icon('unlink')+'이 휴대폰의 연결 해제</button>':'')+'<p class="detail-note">차량의 기록은 삭제되지 않아요. 연결 서버: '+esc(hylink.baseUrl)+'</p>');
  $('save-key').onclick=()=>{const key=$('connection-key').value.trim();if(!key)return toast('연결 키를 입력해 주세요.');window.Android?.saveWayonCloudKey?.(key)};
  $('refresh-data').onclick=()=>{$('sheet').close();refresh()};
  $('disconnect-key')?.addEventListener('click',()=>{
    showSheet('연결을 해제할까요?','<p class="sheet-copy">다시 연결하려면 차량의 연결 키가 필요해요. 차량에 저장된 기록은 유지돼요.</p><button class="primary-button" id="confirm-disconnect">연결 해제</button>');
    $('confirm-disconnect').onclick=()=>window.Android?.clearWayonCloudKey?.();
  });
}
function sourceFor(filter){return ({trips:['trips','trips'],photos:['snapshots','snapshots'],captures:['liveCaptures','captures'],impacts:['impacts','impacts']})[filter]}
function recordsFor(filter){
  const [source,field]=sourceFor(filter);
  return list(data[source]?.[field]);
}
function renderRecords(force=false){
  const [source]=sourceFor(recordFilter),items=recordsFor(recordFilter);
  const failure=list(data.errors).find(e=>e.name===source);
  const signature=JSON.stringify([recordFilter,recordLimit,items,Boolean(data[source]),failure?.message]);
  if(!force&&recordSignature===signature)return;
  recordSignature=signature;
  let html=failure?'<p class="attention record-warning" role="status">이 기록을 갱신하지 못했어요. 이전에 받은 내용만 표시해요.</p>':'';
  if(!data[source]){
    html+=empty('cloud-off',hylink.token?'기록을 아직 받지 못했어요':'먼저 차량을 연결해 주세요',failure?'연결을 확인한 뒤 새로고침해 주세요.':'차량에서 받은 기록만 표시해요.');
  }else if(!items.length){
    html+=empty('archive','아직 수신된 기록이 없어요','서버에 저장된 기록을 받으면 여기에 표시해요.');
  }else{
    html+='<div class="'+(['photos','captures'].includes(recordFilter)?'photo-grid':'list-card')+'">';
    html+=items.slice(0,recordLimit).map((v,i)=>{
      if(recordFilter==='trips')return '<button class="list-row record-button" data-record="'+i+'">'+icon('route')+'<span><b>'+scaled(v.distance_m,.001,1)+' km의 주행</b><small>'+esc(date(v.started_at))+' · '+duration(v.duration_s)+'</small></span>'+icon('chevron-right')+'</button>';
      if(recordFilter==='impacts')return '<button class="list-row record-button" data-record="'+i+'">'+icon('activity')+'<span><b>충격 감지 · '+esc(({light:'가벼움',medium:'보통',heavy:'강함',severe:'심함'})[v.severity]||v.severity||'분류 없음')+'</b><small>'+esc(date(v.detected_at))+'</small></span>'+icon('chevron-right')+'</button>';
      const video=recordFilter==='captures'&&isVideoCapture(v);
      return '<button class="media-card" data-record="'+i+'"><span class="media-image">'+icon(video?'play':'image')+(!video?'<img data-thumbnail="'+i+'" alt="'+(recordFilter==='photos'?(v.camera==='driver'?'실내':'전방'):'저장된')+' 카메라 사진" loading="lazy">':'')+'</span><b>'+ (video?clipDuration(v.duration_s)+' 영상':v.camera==='driver'?'실내 사진':recordFilter==='photos'?'전방 사진':'저장한 사진')+'</b><small>'+esc(date(v.captured_at||v.created_at))+'</small><small>'+scaled(v.size_bytes,1/1048576,1)+' MB'+(v.impact_id?' · 충격 시점':'')+'</small><small data-media-status="'+i+'">'+(video?'눌러서 재생':'사진 불러오는 중')+'</small></button>';
    }).join('');
    html+='</div>';
    if(items.length>recordLimit)html+='<button class="sheet-choice" id="more-records">더 보기 · '+(items.length-recordLimit)+'개</button>';
    if(recordFilter==='impacts')html+='<p class="detail-note">센서 감지는 실제 충돌 여부나 피해 정도를 확정하지 않아요.</p>';
  }
  $('record-content').innerHTML=html;
  $('more-records')?.addEventListener('click',()=>{recordLimit+=8;renderRecords()});
  document.querySelectorAll('[data-record]').forEach(b=>b.onclick=()=>openRecord(items[Number(b.dataset.record)],recordFilter));
  document.querySelectorAll('[data-thumbnail]').forEach(img=>{
    const i=Number(img.dataset.thumbnail),status=document.querySelector('[data-media-status="'+i+'"]');
    const path=mediaPath(items[i],recordFilter);
    fetchMedia(path).then(url=>{if(!img.isConnected)return;img.src=url;status.textContent='눌러서 크게 보기'}).catch(()=>{if(img.isConnected){img.hidden=true;status.textContent='불러오기 실패 · 눌러 다시 시도'}});
  });
  icons();
}
function mediaPath(v,type){return type==='photos'?'/api/snapshot?key='+encodeURIComponent(v.kv_key):'/api/live-capture?id='+encodeURIComponent(v.id)}
async function fetchMedia(path){
  if(!hylink.token)throw new Error('연결 키가 없어요.');
  if(mediaCache.has(path))return mediaCache.get(path);
  if(mediaPending.has(path))return mediaPending.get(path).promise;
  const epoch=mediaEpoch,token=hylink.token,controller=new AbortController();
  const promise=(async()=>{
    const response=await fetch(hylink.baseUrl+path,{headers:{Authorization:'Bearer '+token},signal:controller.signal,cache:'no-store'});
    if(!response.ok)throw new Error('사진을 받지 못했어요. HTTP '+response.status);
    const blob=await response.blob();
    if(epoch!==mediaEpoch)throw new Error('차량 연결이 변경됐어요.');
    const url=URL.createObjectURL(blob);mediaCache.set(path,url);
    // Bound memory without revoking an image currently shown on screen.
    for(const [key,cached]of mediaCache){if(mediaCache.size<=40)break;if(![...document.images].some(img=>img.src===cached)){URL.revokeObjectURL(cached);mediaCache.delete(key)}}
    return url;
  })().finally(()=>{if(mediaPending.get(path)?.controller===controller)mediaPending.delete(path)});
  mediaPending.set(path,{controller,promise});return promise;
}
async function openRecord(v,type){
  if(type==='trips')return showTrip(v);
  if(type==='impacts')return showSheet('충격 감지 기록','<p class="sheet-copy">'+esc(date(v.detected_at))+'</p><div class="sheet-facts"><div><small>동적 가속도 피크</small><b>'+scaled(v.peak_dynamic_g,1,2)+' g</b></div><div><small>전체 가속도 피크</small><b>'+scaled(v.peak_total_g,1,2)+' g</b></div><div><small>저크 피크</small><b>'+scaled(v.peak_jerk_g_per_s,1,2)+' g/s</b></div></div><p class="detail-note">센서 감지값이며 충돌 여부를 확정하지 않아요. 촬영 기록에서 같은 시각의 사진을 함께 확인해 주세요.</p>');
  const path=mediaPath(v,type);
  if(type==='captures'&&isVideoCapture(v))return window.startWayonSavedClip?.({url:hylink.baseUrl+path,token:hylink.token,capture:{durationS:v.duration_s}});
  const epoch=mediaEpoch;
  try{const url=await fetchMedia(path);if(epoch!==mediaEpoch)return;
    lastFocus=document.activeElement;$('full-image').src=url;
    $('image-overlay').classList.add('visible');$('image-overlay').setAttribute('aria-hidden','false');
    document.querySelector('.app-shell').inert=true;$('btn-close-image').focus();
  }catch(error){toast(error.message||'사진을 가져오지 못했어요.')}
}
function closeImage(){
  $('image-overlay').classList.remove('visible');$('image-overlay').setAttribute('aria-hidden','true');
  $('full-image').removeAttribute('src');document.querySelector('.app-shell').inert=false;lastFocus?.focus();
}
function showTrip(trip=model.trip){
  if(!trip?.id)return;
  showSheet('주행 상세','<p role="status">주행 경로를 가져오고 있어요.</p>');
  const request=++detailRequest;
  window.onHylinkTripDetail=detail=>{if(request!==detailRequest||!$('sheet').open)return;renderTrip(detail.trip||detail)};
  window.onHylinkTripError=message=>{if(request!==detailRequest||!$('sheet').open)return;$('sheet-content').innerHTML='<p class="sheet-copy">'+esc(message)+'</p><button class="primary-button" id="retry-trip">다시 시도</button>';$('retry-trip').onclick=()=>showTrip(trip)};
  window.Android?.requestTripDetail?.(String(trip.id));
}
function renderTrip(t){
  const route=list(t.route).map(point).filter(Boolean);
  $('sheet-content').innerHTML='<p class="sheet-copy">'+esc(date(t.started_at))+' — '+esc(date(t.ended_at))+'</p><div class="sheet-facts">'+[['거리',scaled(t.distance_m,.001,1)+' km'],['시간',duration(t.duration_s)],['평균 속도',scaled(t.avg_speed_mps,3.6)+' km/h'],['최고 속도',scaled(t.max_speed_mps,3.6)+' km/h']].map(([k,v])=>'<div><small>'+k+'</small><b>'+v+'</b></div>').join('')+'</div>'+(route.length?'<div id="trip-map" aria-label="저장된 주행 경로"></div><p class="detail-note">파란 경로 · 시작점과 종료점 · '+route.length+'개 위치 기록</p>':'<p class="detail-note">이 주행에는 표시할 경로가 없어요.</p>');
  if(!route.length||!window.maplibregl)return;
  tripMap=new maplibregl.Map({container:'trip-map',style:'https://tiles.openfreemap.org/styles/positron',center:route[0],zoom:13,attributionControl:{compact:true}});
  const current=tripMap;
  current.on('load',()=>{
    if(current!==tripMap)return;
    current.addSource('trip-route',{type:'geojson',data:{type:'Feature',geometry:{type:route.length>1?'LineString':'Point',coordinates:route.length>1?route:route[0]}}});
    if(route.length>1)current.addLayer({id:'trip-route',type:'line',source:'trip-route',paint:{'line-color':'#1765d1','line-width':5}});
    for(const [label,coords]of [['출발',route[0]],['도착',route.at(-1)]]){
      const pin=document.createElement('span');pin.className='route-label';pin.textContent=label;new maplibregl.Marker({element:pin}).setLngLat(coords).addTo(current);
    }
    const bounds=new maplibregl.LngLatBounds(route[0],route[0]);route.forEach(p=>bounds.extend(p));current.fitBounds(bounds,{padding:40,maxZoom:16,duration:0});
  });
  current.on('error',()=>{if(current===tripMap&&!current.isStyleLoaded())toast('경로 배경 지도를 불러오지 못했어요.')});
}
function resetVehicle(){
  // Invalidate media and location before switching credentials; no old-vehicle content survives.
  mediaEpoch++;for(const {controller}of mediaPending.values())controller.abort();mediaPending.clear();
  for(const url of mediaCache.values())URL.revokeObjectURL(url);mediaCache.clear();
  if($('wayon-live-overlay').classList.contains('active'))window.stopWayonLiveView?.();
  window.closeWayonTerminal?.();closeImage();
  if($('sheet').open)$('sheet').close();
  if($('map-dialog').open)$('map-dialog').close();
  closeTrip();data={};hylink.data=null;recordSignature='';recordLimit=8;
  $('record-content').replaceChildren();
  if(map){map.remove();map=null;marker=null;myMarker=null;}
}
window.onHylinkFontScale=value=>{const scale=Math.min(2,Math.max(1,Number(value)||1));document.documentElement.style.fontSize=16*scale+'px';document.body.classList.toggle('large-text',scale>=1.3)};
window.onHylinkNativeReady=(key,url)=>{hylink.token=key||'';hylink.baseUrl=(url||'').replace(/\/$/,'');render()};
window.onHylinkKeySaved=key=>{resetVehicle();hylink.token=key||'';render();toast('연결 키를 저장했어요.')};
window.onHylinkKeyCleared=()=>{resetVehicle();hylink.token='';render();navigate('now');toast('이 휴대폰의 차량 연결을 해제했어요.')};
window.onHylinkLoading=()=>{$('connection-button').setAttribute('aria-busy','true')};
window.onHylinkError=message=>{$('connection-button').removeAttribute('aria-busy');data={...data,error:true};hylink.data=data;render();toast(message||'연결을 확인해 주세요.')};
window.onHylinkData=value=>{if(!hylink.token)return;$('connection-button').removeAttribute('aria-busy');data=value||{};hylink.data=data;render()};
window.handleHylinkBack=()=>{
  if($('wayon-live-overlay').classList.contains('active')){window.stopWayonLiveView?.();return true}
  if($('image-overlay').classList.contains('visible')){closeImage();return true}
  if($('sheet').open){$('sheet').close();return true}
  if($('map-dialog').open){$('map-dialog').close();return true}
  if(currentPage!=='now'){navigate('now');return true}return false;
};
$('close-sheet').onclick=()=>$('sheet').close();
$('sheet').addEventListener('close',()=>{closeTrip();lastFocus?.focus()});
$('btn-close-image').onclick=closeImage;
$('connection-button').onclick=showConnection;
document.querySelector('.overview-heading').addEventListener('click',()=>{if(!hylink.token)showConnection()});
document.querySelectorAll('[data-navigate]').forEach(b=>b.onclick=()=>navigate(b.dataset.navigate));
document.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>{recordFilter=b.dataset.filter;recordLimit=8;document.querySelectorAll('[data-filter]').forEach(x=>{x.classList.toggle('selected',x===b);x.setAttribute('aria-pressed',String(x===b))});renderRecords()});
$('recent-trip').onclick=()=>showTrip();
$('photos-button').onclick=()=>{document.querySelector('[data-filter="photos"]').click();navigate('records')};
$('locate-button').onclick=openFullMap;
window.addEventListener('wayon-live-capture-saved',()=>setTimeout(refresh,1200));
// Update age labels locally; do not increase cloud traffic.
setInterval(()=>{if(!document.hidden)render()},30000);
let phoneCallback;
function locatePhone(success,failure,options){
  if(window.Android?.requestCurrentLocation){
    phoneCallback={id:locationRequest,success,failure};
    window.Android.requestCurrentLocation(locationRequest);
  }else navigator.geolocation.getCurrentPosition(success,failure,options);
}
window.onHylinkLocation=(id,result)=>{
  if(!phoneCallback||id!==phoneCallback.id||id!==locationRequest||!$('map-dialog').open)return;
  const callback=phoneCallback;phoneCallback=null;
  if(result.error)callback.failure({code:result.code||2});
  else callback.success({coords:result});
};
document.addEventListener('click',event=>{
  const link=event.target.closest('a[href]');
  if(link&&window.Android?.openMapAttribution){event.preventDefault();window.Android.openMapAttribution(link.href)}
});

function row(label,value,detail=''){return `<div class="list-row"><span><b>${esc(label)}</b>${detail?`<small>${esc(detail)}</small>`:''}</span><span class="row-value">${esc(value)}</span></div>`}
function metric(label,value,note,name){return `<div class="metric"><span class="metric-label">${icon(name)}${label}</span><strong>${esc(value)}</strong><small>${esc(note)}</small></div>`}
function renderVehicle(){
  const detailsOpen=$('telemetry-details')?.open===true;
  const v=model.vehicle,d=model.raw.device||{},p=model.panda,available=v.available===true;
  const yesno=x=>CloudOverview.flag(x)===true?'켜짐':CloudOverview.flag(x)===false?'꺼짐':'미수신';
  $('vehicle-content').innerHTML=`<div class="list-card"><div class="list-row">${icon('radio-tower')}<span><b>${esc(d.type||'연결 장치 확인 대기')}</b><small>${esc(model.received)}</small></span><span class="status-tag ${model.stale?'warning':''}">${model.stale?'수신 지연':model.age===null?'대기':'수신 기록'}</span></div></div>
    ${model.alerts.length?`<button class="sheet-choice" id="vehicle-alerts">${icon('triangle-alert')}<span><b>수신 알림 ${model.alerts.length}개</b><small>경고와 기록을 확인해 주세요</small></span></button>`:''}
    ${available?`<p class="group-label">차량 상태</p><div class="list-card">${row('운행 상태',model.status)}${row('차량 속도',CloudOverview.number(v.speedKph)!==null?v.speedKph+' km/h':'미수신')}${row('기어',({drive:'D',park:'P',reverse:'R',neutral:'N'}[v.gear]||'미수신'))}${row('openpilot 제어',model.raw.openpilot?.available?yesno(model.raw.openpilot.active):'미수신')}${row('크루즈 설정 속도',CloudOverview.number(v.cruise?.speedKph)!==null?v.cruise.speedKph+' km/h':'미수신')}</div>`:`<p class="detail-note">${model.age===null?'차량 정보를 기다리고 있어요.':model.status==='주차 중'?'주차 중에는 장치 정보를 중심으로 보여드려요. 속도·기어·조향 정보는 시동이 켜지면 확인할 수 있어요.':'현재 상세 차량 정보는 수신되지 않았어요.'}</p>`}
    <p class="group-label">장치 상태</p><div class="metric-grid">${metric('입력 전압',fixed(model.voltage,1)+' V','Panda 측정값','battery-medium')}${metric('최고 온도',fixed(model.temperature)+' °C','장치 온도 센서 중 최댓값','thermometer')}${metric('남은 저장공간',fixed(model.freeSpace)+'%','콤마 장치 기준','hard-drive')}${metric('소비 전력',fixed(CloudOverview.number(model.state.power_w),1)+' W','수신된 전력 값','zap')}</div>
    <p class="group-label">통신 · 진단</p><div class="list-card">${row('차량 CAN',!available?'미수신':v.can?.valid===true?'유효':v.can?.valid===false?'경고 수신':'미수신')}${row('조향 상태',!available?'미수신':v.steeringFault?.permanent?'오류 수신':v.steeringFault?.temporary?'일시적 사용 불가':v.steeringFault?.permanent===false&&v.steeringFault?.temporary===false?'오류 플래그 없음':'미수신')}${row('장치 네트워크',d.network?.type||'미수신')}${row('메모리 사용',fixed(CloudOverview.number(d.usage?.memoryPercent))+'%')}${row('팬 작동',fixed(CloudOverview.number(d.thermal?.fanPercent))+'%')}${row('Panda 하트비트',p.heartbeatLost===true?'손실 감지':p.heartbeatLost===false?'손실 플래그 없음':'미수신')}</div><p class="detail-note">화면은 마지막 수신값을 보여줘요. 수치만으로 차량의 안전 상태를 판단하지 마세요. 연료·타이어 공기압·문 잠금은 지원이 확인되기 전까지 표시하지 않아요.</p>`;
  $('vehicle-alerts')?.addEventListener('click',showAlerts);
  const details=document.createElement('details');details.id='telemetry-details';details.className='telemetry-details';details.open=detailsOpen;
  details.innerHTML='<summary>장치 상세 데이터</summary><div class="list-card">'+diagnosticRows()+'</div><p class="detail-note">받은 항목만 표시해요. 배터리 에너지는 장치의 추정치이며 연료량이나 배터리 잔량이 아니에요.</p>';
  $('vehicle-content').append(details);
}
function diagnosticRows(){
  const raw=model.raw,d=raw.device||{},p=model.panda,o=raw.openpilot||{},s=model.state;
  const mean=values=>{const n=list(values).map(num).filter(x=>x!==null);return n.length?n.reduce((a,b)=>a+b,0)/n.length:null};
  const entries=[],add=(label,value,unit='')=>{if(value!==null&&value!==undefined&&value!=='')entries.push(row(label,typeof value==='number'?fixed(value,1)+unit:String(value)+unit))};
  add('최근 갱신',s.updated_at?date(s.updated_at):null);
  add('CPU 평균 사용',mean(d.usage?.cpuPercent),'%');add('GPU 사용',num(d.usage?.gpuPercent),'%');
  const t=d.thermal?.temperaturesC||{};
  for(const [label,value]of [['CPU 온도',mean(t.cpu)],['메모리 온도',num(t.memory)],['GNSS 온도',num(t.gnss)],['모뎀 온도',mean(t.modem)],['PMIC 온도',mean(t.pmic)],['흡기 온도',num(t.intake)],['배기 온도',num(t.exhaust)]])add(label,value,' °C');
  add('입력 전류',num(s.current_ma??raw.currentMa),' mA');add('장치 소비 전력',num(s.device_power_w??raw.devicePowerW),' W');
  add('SoM 전력',num(d.power?.somDrawW),' W');add('Offroad 누적 사용',num(d.power?.offroadUsageWh),' Wh');add('배터리 에너지 추정',num(d.power?.carBatteryCapacityWh),' Wh');
  add('장치 화면 밝기',num(s.screen_brightness_percent??d.screenBrightnessPercent),'%');add('네트워크 강도',d.network?.strength);
  add('Panda 종류',p.type);add('하네스 상태',p.harnessStatus);add('안전 모델',p.safetyModel);add('안전 파라미터',p.safetyParam);
  if(CloudOverview.flag(p.safetyRxChecksInvalid)!==null)add('수신 검사',p.safetyRxChecksInvalid?'오류 플래그 수신':'오류 플래그 없음');
  add('Panda 오류 상태',p.faultStatus);add('SPI 오류 누적',num(p.spiErrorCount));add('RX overflow 누적',num(p.rxBufferOverflow));
  add('TX overflow 누적',num(p.counterHealth?.cumulativeSincePandaBoot?.txBufferOverflow));add('카운터 평가',p.counterHealth?.assessment);
  add('Panda 작동 시간',num(p.uptimeS)===null?null:duration(p.uptimeS));add('인터럽트 부하',num(p.interruptLoad),'%');
  if(o.available===true){add('openpilot 주행 성향',o.personality);if(CloudOverview.flag(o.experimentalMode)!==null)add('실험 모드',o.experimentalMode?'켜짐':'꺼짐')}
  add('텔레메트리 버전',raw.schemaVersion);
  return entries.join('')||row('상세 정보','수신 대기');
}


function mapPadding(){
  const height=document.querySelector('.full-map-card').getBoundingClientRect().height;
  return {top:100,bottom:Math.min(height+44,innerHeight*.55),left:48,right:48};
}
function updateMapCard(){
  $('map-dialog').style.setProperty('--map-card-height',document.querySelector('.full-map-card').getBoundingClientRect().height+'px');
}
function setLocationStatus(text){$('my-location-status').textContent=text;updateMapCard()}
function centerVehicle(){if(model.point)map.jumpTo({center:model.point,zoom:15.3,padding:mapPadding()})}
function fitLocations(){
  if(!model.point||!myPosition){centerVehicle();return;}
  const bounds=new maplibregl.LngLatBounds(model.point,model.point).extend(myPosition.point);
  map.fitBounds(bounds,{padding:mapPadding(),maxZoom:16,duration:0});
}
function toggleMapInteraction(enabled){
  for(const name of ['dragPan','scrollZoom','doubleClickZoom','touchZoomRotate','keyboard'])map[name]?.[enabled?'enable':'disable']();
  map.touchZoomRotate?.disableRotation();
  $('map').inert=!enabled;
}
function openFullMap(){
  if(!map||$('map-dialog').open)return;
  mapReturnFocus=document.activeElement;mapTouched=false;
  $('full-map-host').append($('map'));
  $('map-dialog').append($('map-credits'));
  $('map-credits').open=false;
  document.body.classList.add('map-opened');
  $('map-dialog').showModal();
  toggleMapInteraction(true);
  requestAnimationFrame(()=>{if(!$('map-dialog').open)return;map.resize();updateMapCard();centerVehicle();$('close-map').focus();requestMyLocation(false)});
}
function closeFullMap(){
  window.Android?.cancelCurrentLocation?.();
  locationRequest++;locationPending=false;myPosition=undefined;
  $('center-me').removeAttribute('aria-busy');
  myMarker?.remove(); // Phone position never appears on the Now tab.
  document.querySelector('.map-section').prepend($('map'));
  document.querySelector('.map-section').append($('map-credits'));
  $('map-credits').open=false;
  document.body.classList.remove('map-opened');
  toggleMapInteraction(false);
  requestAnimationFrame(()=>{if(map){map.resize();if(model.point)map.jumpTo({center:model.point,zoom:15.3,padding:{top:0,bottom:0,left:0,right:0}})}mapReturnFocus?.focus()});
}
function requestMyLocation(centerOnly=false){
  if(!$('map-dialog').open||locationPending)return;
  if(!window.Android?.requestCurrentLocation&&!navigator.geolocation){setLocationStatus('이 브라우저는 현재 위치를 지원하지 않아요. 차량 위치만 표시해요.');return;}
  const request=++locationRequest;locationPending=true;
  setLocationStatus('내 위치를 확인하고 있어요. 위치 권한을 허용해 주세요.');
  $('center-me').setAttribute('aria-busy','true');
  locatePhone(position=>{
    if(request!==locationRequest||!$('map-dialog').open)return;
    locationPending=false;$('center-me').removeAttribute('aria-busy');
    const {longitude,latitude,accuracy}=position.coords;
    if(!Number.isFinite(longitude)||!Number.isFinite(latitude)||Math.abs(longitude)>180||Math.abs(latitude)>90){setLocationStatus('위치를 확인하지 못했어요. 내 위치 버튼으로 다시 시도해 주세요.');return;}
    myPosition={point:[longitude,latitude],accuracy,receivedAt:Date.now()};
    if(!myMarker){
      const dot=document.createElement('div');dot.className='my-location-marker';dot.setAttribute('role','img');dot.setAttribute('aria-label','내 현재 위치');
      myMarker=new maplibregl.Marker({element:dot});
    }
    myMarker.setLngLat(myPosition.point).addTo(map);
    setLocationStatus('내 위치 확인됨'+(Number.isFinite(accuracy)?' · 오차 약 '+Math.round(accuracy)+'m':'')+' · 차량은 마지막 수신 위치예요.');
    if(centerOnly)map.jumpTo({center:myPosition.point,zoom:16,padding:mapPadding()});
    else if(!mapTouched)fitLocations();
  },error=>{
    if(request!==locationRequest||!$('map-dialog').open)return;
    locationPending=false;$('center-me').removeAttribute('aria-busy');
    myMarker?.remove();myPosition=undefined;
    setLocationStatus(error.code===1?'위치 권한이 꺼져 있어요. 앱 권한에서 허용 후 내 위치를 눌러 주세요.':error.code===3?'현재 위치 확인이 지연돼요. 내 위치를 눌러 다시 시도해 주세요.':'현재 위치를 받지 못했어요. 차량 위치만 표시해요.');
  },{enableHighAccuracy:true,timeout:12000,maximumAge:15000});
}
$('close-map').onclick=()=>$('map-dialog').close();
$('map-dialog').addEventListener('close',closeFullMap);
$('center-vehicle').onclick=centerVehicle;
$('center-me').onclick=()=>requestMyLocation(true);
$('fit-locations').onclick=fitLocations;
new ResizeObserver(()=>{if($('map-dialog').open){updateMapCard();map?.resize()}}).observe(document.querySelector('.full-map-card'));
new ResizeObserver(()=>{if(map&&!$('map-dialog').open)map.resize()}).observe(document.querySelector('.map-section'));
function ensureMap(){
if(map||!model.point)return;
if(window.maplibregl){
  map=new maplibregl.Map({container:'map',style:'https://tiles.openfreemap.org/styles/positron',center:model.point,zoom:15.3,attributionControl:false,interactive:false,dragRotate:false,pitchWithRotate:false,scrollZoom:false});
  const pin=document.createElement('button');pin.className='car-pin';pin.setAttribute('aria-label','마지막 차량 위치');pin.innerHTML=icon('car-front');pin.onclick=()=>{$('map-dialog').open?centerVehicle():openFullMap()};marker=new maplibregl.Marker({element:pin}).setLngLat(model.point).addTo(map);icons();
  $('map').inert=true;
  map.on('dragstart',e=>{if(e.originalEvent)mapTouched=true});
  map.on('zoomstart',e=>{if(e.originalEvent)mapTouched=true});
  map.on('style.load',()=>{
    for(const layer of map.getStyle().layers){
      if(layer.type!=='symbol')continue;
      if(layer.id.startsWith('label_')||layer.id==='airport'||layer.id.includes('shield')){map.setLayoutProperty(layer.id,'visibility','none');continue;}
      if(layer.layout?.['text-field'])map.setLayoutProperty(layer.id,'text-field',['coalesce',['get','name:ko'],['get','name:nonlatin'],['get','name']]);
    }
  });
  map.on('load',()=>{document.documentElement.dataset.mapReady='true';$('map-error').hidden=true;map.resize()});
  map.on('error',()=>{if(!map.isStyleLoaded())$('map-error').hidden=false});
}else $('map-error').hidden=false;
}

render();
