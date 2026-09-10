/* Design-only fixture adapter. NEVER imported by app/main.html. */
const $=id=>document.getElementById(id);
const icons=()=>window.lucide?.createIcons();
const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icon=name=>`<i data-lucide="${name}"></i>`;
const fixed=(v,d=0)=>v===null?'—':v.toFixed(d);
let scenario='parked',model,map,marker,recordFilter='trips',lastFocus;
let myMarker,myPosition,locationRequest=0,locationPending=false,mapReturnFocus,mapTouched=false;
let data;
function fixture(kind){
  const now=Date.now(),iso=seconds=>new Date(now-seconds*1000).toISOString();
  const value={feed:{state:{updated_at:iso(120),onroad:0,ignition:0,latitude:37.56650,longitude:126.97800,voltage_v:12.48,power_w:1.75,speed_mps:0,
    raw_json:{gps:{fresh:true,accuracyM:6},device:{type:'comma 3X',network:{type:'wifi',strength:4},usage:{freeSpacePercent:78,memoryPercent:44,gpuPercent:8,cpuPercent:[12,18,20,16]},thermal:{status:'green',fanPercent:0,temperaturesC:{max:42.1}},power:{drawW:1.75}},panda:{type:'tres',faults:[],faultStatus:'none',heartbeatLost:false},vehicle:{available:false,reason:'offroad'},openpilot:{available:false}}}},
    trips:{trips:[{id:'sample-1',started_at:iso(3600),ended_at:iso(1680),distance_m:18400,duration_s:1920,avg_speed_mps:9.58,max_speed_mps:21.6}]},
    snapshots:{snapshots:[0,1,2,3].map((n)=>({camera:n%2?'driver':'wide',captured_at:iso(180+n*300),size_bytes:182000}))},impacts:{impacts:[]}};
  const s=value.feed.state;
  if(kind==='driving'||kind==='warning'){
    Object.assign(s,{updated_at:iso(15),onroad:1,ignition:1,speed_mps:16.1,voltage_v:14.1,power_w:18.7});
    s.raw_json.device.thermal.temperaturesC.max=58;s.raw_json.device.thermal.fanPercent=38;
    s.raw_json.vehicle={available:true,speedKph:58,gear:'drive',standstill:false,doorOpen:false,seatbeltUnlatched:false,can:{valid:kind!=='warning',timeout:false,errorCounter:kind==='warning'?3:0},steeringFault:{temporary:kind==='warning',permanent:false},cruise:{enabled:true,speedKph:80}};
    s.raw_json.openpilot={available:true,active:kind!=='warning',enabled:kind!=='warning',alert:{text1:'',text2:''}};
  }
  if(kind==='stale'){s.updated_at=iso(7200);s.raw_json.gps.fresh=false;value.error=true}
  if(kind==='impact')value.impacts.impacts=[{id:'sample-impact',detected_at:iso(480),severity:'medium',peak_dynamic_g:0.43,peak_total_g:1.27,peak_jerk_g_per_s:3.8}];
  if(kind==='empty')return {feed:{state:{}},trips:{trips:[]},snapshots:{snapshots:[]},impacts:{impacts:[]}};
  return value;
}
function render(){
  model=CloudOverview.derive(data);
  $('vehicle-state').textContent=(model.stale?'마지막 상태 · ':'')+model.status;
  $('freshness-label').textContent=(model.vehicle.available===true&&CloudOverview.number(model.vehicle.speedKph)!==null?model.vehicle.speedKph+' km/h · ':'')+model.received;
  $('state-symbol').innerHTML=icon(model.state.onroad?'navigation':'circle-parking');
  const attention=model.alerts[0];$('attention').hidden=!attention;
  $('attention').innerHTML=attention?icon(attention.icon)+`<div><strong>${esc(attention.title)}</strong><p>${esc(attention.detail)}</p>${model.alerts.length>1?`<button id="all-alerts">수신 알림 ${model.alerts.length}개 보기 →</button>`:''}</div>`:'';
  $('all-alerts')?.addEventListener('click',showAlerts);
  const accuracy=CloudOverview.number(model.raw.gps?.accuracyM);
  $('location-caption').textContent=model.point?`마지막 수신 위치${model.raw.gps?.fresh===false?' · 이전 GPS 기록':accuracy!==null?' · GPS 오차 약 '+accuracy+'m':''}`:'위치 수신 대기';
  const t=model.trip;
  $('recent-trip').disabled=!t;
  $('trip-distance').textContent=t?fixed(CloudOverview.number(t.distance_m)/1000,1):'—';
  $('trip-duration').textContent=t?Math.round(t.duration_s/60)+'분':'—';
  $('trip-average').textContent=t?Math.round(t.avg_speed_mps*3.6):'—';
  document.querySelector('.journey-date').textContent=t?'최근 수신된 주행 기록':'주행 기록이 아직 없어요';
  $('photo-count').textContent=`수신된 사진 ${model.photos.length}장`;
  $('vehicle-age').textContent=model.received+' 기준이에요.';
  $('locate-button').disabled=!model.point;
  document.querySelector('.map-section').hidden=!model.point;
  if(map&&marker){if(model.point){marker.setLngLat(model.point).addTo(map);map.jumpTo({center:model.point})}else marker.remove()}
  renderRecords();renderVehicle();icons();
}
function row(label,value,detail=''){return `<div class="list-row"><span><b>${esc(label)}</b>${detail?`<small>${esc(detail)}</small>`:''}</span><span class="row-value">${esc(value)}</span></div>`}
function metric(label,value,note,name){return `<div class="metric"><span class="metric-label">${icon(name)}${label}</span><strong>${esc(value)}</strong><small>${esc(note)}</small></div>`}
function renderVehicle(){
  const v=model.vehicle,d=model.raw.device||{},p=model.panda,available=v.available===true;
  const yesno=x=>CloudOverview.flag(x)===true?'켜짐':CloudOverview.flag(x)===false?'꺼짐':'미수신';
  $('vehicle-content').innerHTML=`<div class="list-card"><div class="list-row">${icon('radio-tower')}<span><b>${esc(d.type||'연결 장치 확인 대기')}</b><small>${esc(model.received)}</small></span><span class="status-tag ${model.stale?'warning':''}">${model.stale?'수신 지연':model.age===null?'대기':'수신 기록'}</span></div></div>
    ${model.alerts.length?`<button class="sheet-choice" id="vehicle-alerts">${icon('triangle-alert')}<span><b>수신 알림 ${model.alerts.length}개</b><small>경고와 기록을 확인해 주세요</small></span></button>`:''}
    ${available?`<p class="group-label">차량 상태</p><div class="list-card">${row('운행 상태',model.status)}${row('차량 속도',CloudOverview.number(v.speedKph)!==null?v.speedKph+' km/h':'미수신')}${row('기어',({drive:'D',park:'P',reverse:'R',neutral:'N'}[v.gear]||'미수신'))}${row('openpilot 제어',model.raw.openpilot?.available?yesno(model.raw.openpilot.active):'미수신')}${row('크루즈 설정 속도',CloudOverview.number(v.cruise?.speedKph)!==null?v.cruise.speedKph+' km/h':'미수신')}</div>`:`<p class="detail-note">${model.age===null?'차량 정보를 기다리고 있어요.':model.status==='주차 중'?'주차 중에는 장치 정보를 중심으로 보여드려요. 속도·기어·조향 정보는 시동이 켜지면 확인할 수 있어요.':'현재 상세 차량 정보는 수신되지 않았어요.'}</p>`}
    <p class="group-label">장치 상태</p><div class="metric-grid">${metric('입력 전압',fixed(model.voltage,1)+' V','Panda 측정값','battery-medium')}${metric('최고 온도',fixed(model.temperature)+' °C','장치 온도 센서 중 최댓값','thermometer')}${metric('남은 저장공간',fixed(model.freeSpace)+'%','콤마 장치 기준','hard-drive')}${metric('소비 전력',fixed(CloudOverview.number(model.state.power_w),1)+' W','수신된 전력 값','zap')}</div>
    <p class="group-label">통신 · 진단</p><div class="list-card">${row('차량 CAN',!available?'미수신':v.can?.valid===true?'유효':v.can?.valid===false?'경고 수신':'미수신')}${row('조향 상태',!available?'미수신':v.steeringFault?.permanent?'오류 수신':v.steeringFault?.temporary?'일시적 사용 불가':v.steeringFault?'오류 플래그 없음':'미수신')}${row('장치 네트워크',d.network?.type||'미수신')}${row('메모리 사용',fixed(CloudOverview.number(d.usage?.memoryPercent))+'%')}${row('팬 작동',fixed(CloudOverview.number(d.thermal?.fanPercent))+'%')}${row('Panda 하트비트',p.heartbeatLost===true?'손실 감지':p.heartbeatLost===false?'손실 플래그 없음':'미수신')}</div><p class="detail-note">화면은 마지막 수신값을 보여줘요. 수치만으로 차량의 안전 상태를 판단하지 마세요. 연료·타이어 공기압·문 잠금은 지원이 확인되기 전까지 표시하지 않아요.</p><button class="sheet-choice" id="advanced-button">${icon('terminal')}<span><b>고급 도구</b><small>원격 세션 · 연결 설정</small></span></button>`;
  $('vehicle-alerts')?.addEventListener('click',showAlerts);
  $('advanced-button').onclick=()=>showSheet('고급 도구',`<p class="sheet-copy">원격 터미널과 연결 설정은 일반 차량 정보와 분리했어요. 실제 앱에서는 인증과 세션 상태를 확인한 후 접근하도록 구성할 예정이에요.</p><p class="inline-note">이 미리보기에서는 차량 명령을 전송하지 않아요.</p>`);
}
function renderRecords(){
  let html='';
  if(recordFilter==='trips')html=model.trip?`<p class="group-label">최근 주행</p><div class="list-card"><button class="list-row" id="trip-record">${icon('route')}<span><b>18.4 km의 주행</b><small>32분 · 평균 34 km/h</small></span>${icon('chevron-right')}</button></div><p class="detail-note">주행 거리·시간·평균 속도는 저장된 주행 기록 기준이에요. 경로와 추가 리포트는 상세 화면에서 확인해요.</p>`:empty('route','아직 주행 기록이 없어요','차량에서 기록을 받으면 여기에 모아둘게요.');
  if(recordFilter==='photos')html=model.photos.length?`<p class="group-label">최근 사진 · ${model.photos.length}장</p><div class="photo-grid">${model.photos.map((p,i)=>`<button class="photo-placeholder" data-photo="${i}">${icon('image')}<b>${p.camera==='wide'?'전방 카메라':'실내 카메라'}</b><small>예시 항목 ${i+1} · 이미지 미포함</small></button>`).join('')}</div><p class="detail-note">인증된 사진만 불러오는 영역이에요. 미리보기에는 실제 차량 사진이 없어요.</p>`:empty('images','수신된 사진이 없어요','촬영된 사진이 서버에 저장되면 표시돼요.');
  if(recordFilter==='impacts')html=model.impacts.length?`<p class="group-label">최근 충격 감지</p><div class="list-card"><button class="list-row" id="impact-record">${icon('activity')}<span><b>충격 감지 기록</b><small>8분 전 · 중간 강도 분류</small></span>${icon('chevron-right')}</button></div><p class="detail-note">센서 감지는 실제 충돌 여부를 확정하지 않아요. 주변 사진과 차량 상태를 함께 확인해 주세요.</p>`:empty('activity','수신된 충격 기록이 없어요','기록이 없다는 뜻이며, 차량 안전을 보장하는 표시는 아니에요.');
  $('record-content').innerHTML=html;
  $('trip-record')?.addEventListener('click',showTrip);
  $('impact-record')?.addEventListener('click',()=>showSheet('충격 감지 기록',`<p class="sheet-copy">예시 · 8분 전 감지<br>중간 강도 분류</p><div class="sheet-facts"><div><small>동적 가속도 피크</small><b>0.43 g</b></div><div><small>전체 가속도 피크</small><b>1.27 g</b></div></div><p class="inline-note">충돌 여부와 피해 정도를 확정하는 값이 아니에요.</p>`));
  document.querySelectorAll('[data-photo]').forEach(b=>b.onclick=()=>showSheet('주차 사진',`<p class="sheet-copy">실제 앱에서는 이 위치에 인증된 카메라 사진과 촬영 시각을 표시해요. 미리보기에는 이미지가 포함되지 않았어요.</p>`));
  icons();
}
function empty(name,title,copy){return `<div class="empty-state">${icon(name)}<h3>${title}</h3><p>${copy}</p></div>`}
function navigate(name){document.querySelectorAll('.page').forEach(p=>{p.hidden=p.id!=='page-'+name;p.classList.toggle('active',!p.hidden)});document.querySelectorAll('.tab-bar button').forEach(b=>{b.classList.toggle('selected',b.dataset.navigate===name);if(b.dataset.navigate===name)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')});window.scrollTo({top:0,behavior:'instant'});if(name==='now')requestAnimationFrame(()=>map?.resize());}
function showSheet(title,content){lastFocus=document.activeElement;$('sheet-title').textContent=title;$('sheet-content').innerHTML=content;$('sheet').showModal();icons();$('close-sheet').focus()}
function showAlerts(){showSheet('확인할 수신 정보',model.alerts.map(a=>`<div class="sheet-choice">${icon(a.icon)}<span><b>${esc(a.title)}</b><small>${esc(a.detail)}</small></span></div>`).join(''))}
function showTrip(){showSheet('최근 주행',`<p class="sheet-copy">저장된 주행 한 건을 자세히 살펴보세요.</p><div class="sheet-facts"><div><small>거리</small><b>18.4 km</b></div><div><small>주행 시간</small><b>32분</b></div><div><small>평균 속도</small><b>34 km/h</b></div><div><small>최고 속도</small><b>78 km/h</b></div></div><p class="inline-note">예시 데이터입니다. 실제 앱에서는 경로와 서버에 저장된 추가 리포트를 함께 보여줄 예정이에요.</p>`)}
function scenarioSheet(){showSheet('어떤 상황을 볼까요?',[['parked','circle-parking','주차 중','위치와 최근 기록 중심'],['driving','navigation','주행 중','주행 상태와 수신 시각'],['warning','triangle-alert','차량 경고','CAN·조향 경고를 가장 먼저'],['impact','activity','충격 감지','최근 감지 기록 안내'],['stale','cloud-off','수신 지연','마지막 정보임을 명확하게'],['empty','circle-dashed','첫 연결 전','빈 정보를 정상으로 표시하지 않음']].map(([key,ic,title,sub])=>`<button class="sheet-choice" data-scenario="${key}">${icon(ic)}<span><b>${title}</b><small>${sub}</small></span></button>`).join(''));document.querySelectorAll('[data-scenario]').forEach(b=>b.onclick=()=>{scenario=b.dataset.scenario;data=fixture(scenario);render();$('sheet').close();navigate('now')})}
$('scenario-button').onclick=scenarioSheet;
$('close-sheet').onclick=()=>$('sheet').close();$('sheet').addEventListener('close',()=>lastFocus?.focus());
document.querySelectorAll('[data-navigate]').forEach(b=>b.onclick=()=>navigate(b.dataset.navigate));
document.querySelectorAll('[data-filter]').forEach(b=>b.onclick=()=>{recordFilter=b.dataset.filter;document.querySelectorAll('[data-filter]').forEach(x=>x.classList.toggle('selected',x===b));renderRecords()});
$('recent-trip').onclick=showTrip;
$('photos-button').onclick=()=>{recordFilter='photos';document.querySelector('[data-filter="photos"]').click();navigate('records')};
$('live-button').onclick=()=>showSheet('차량 카메라 라이브',`<p class="sheet-copy">실제 앱에서는 차량 연결과 카메라 이용 가능 여부를 확인한 다음 라이브를 시작해요.</p><p class="inline-note">라이브는 데이터와 차량 전력을 사용할 수 있어요. 이 미리보기에서는 세션을 시작하지 않아요.</p><button class="primary-button" id="demo-close">미리보기 확인</button>`);
$('sheet-content').addEventListener('click',e=>{if(e.target.id==='demo-close')$('sheet').close()});
$('locate-button').onclick=openFullMap;
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
  locationRequest++;locationPending=false;myPosition=undefined;
  $('center-me').removeAttribute('aria-busy');
  myMarker?.remove(); // Phone position never appears on the Now tab.
  document.querySelector('.map-section').prepend($('map'));
  document.querySelector('.map-section').append($('map-credits'));
  $('map-credits').open=false;
  document.body.classList.remove('map-opened');
  toggleMapInteraction(false);
  requestAnimationFrame(()=>{map.resize();if(model.point)map.jumpTo({center:model.point,zoom:15.3,padding:{top:0,bottom:0,left:0,right:0}});mapReturnFocus?.focus()});
}
function requestMyLocation(centerOnly=false){
  if(!$('map-dialog').open||locationPending)return;
  if(!navigator.geolocation){setLocationStatus('이 브라우저는 현재 위치를 지원하지 않아요. 차량 위치만 표시해요.');return;}
  const request=++locationRequest;locationPending=true;
  setLocationStatus('내 위치를 확인하고 있어요. 위치 권한을 허용해 주세요.');
  $('center-me').setAttribute('aria-busy','true');
  navigator.geolocation.getCurrentPosition(position=>{
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
    setLocationStatus('내 위치 확인됨'+(Number.isFinite(accuracy)?' · 오차 약 '+Math.round(accuracy)+'m':'')+' · 차량은 예시 위치예요.');
    if(centerOnly)map.jumpTo({center:myPosition.point,zoom:16,padding:mapPadding()});
    else if(!mapTouched)fitLocations();
  },error=>{
    if(request!==locationRequest||!$('map-dialog').open)return;
    locationPending=false;$('center-me').removeAttribute('aria-busy');
    myMarker?.remove();myPosition=undefined;
    setLocationStatus(error.code===1?'위치 권한이 꺼져 있어요. 브라우저에서 허용 후 내 위치를 눌러 주세요.':error.code===3?'현재 위치 확인이 지연돼요. 내 위치를 눌러 다시 시도해 주세요.':'현재 위치를 받지 못했어요. 차량 위치만 표시해요.');
  },{enableHighAccuracy:true,timeout:12000,maximumAge:15000});
}
$('close-map').onclick=()=>$('map-dialog').close();
$('map-dialog').addEventListener('close',closeFullMap);
$('center-vehicle').onclick=centerVehicle;
$('center-me').onclick=()=>requestMyLocation(true);
$('fit-locations').onclick=fitLocations;
new ResizeObserver(()=>{if($('map-dialog').open){updateMapCard();map?.resize()}}).observe(document.querySelector('.full-map-card'));
new ResizeObserver(()=>{if(map&&!$('map-dialog').open)map.resize()}).observe(document.querySelector('.map-section'));
data=fixture(scenario);render();
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
