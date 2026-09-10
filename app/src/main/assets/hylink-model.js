/* Pure presentation model. No credentials, polling, vehicle commands or network calls. */
(function(root){
  const number=v=>v===null||v===undefined||typeof v==='boolean'||(typeof v==='string'&&!v.trim())?null:Number.isFinite(Number(v))?Number(v):null;
  const flag=v=>v===true||v===1?true:v===false||v===0?false:null;
  function derive(data,now=Date.now()){
    const state=data.feed?.state||{};
    let raw=state.raw_json||{};if(typeof raw==='string'){try{raw=JSON.parse(raw)}catch{raw={}}}
    if(!raw||typeof raw!=='object'||Array.isArray(raw))raw={};
    const time=Date.parse(state.updated_at),age=Number.isFinite(time)&&time<=now+60000?Math.max(0,(now-time)/1000):null;
    const onroad=flag(state.onroad),ignition=flag(state.ignition),stale=age!==null&&age>(onroad===true?60:900);
    const received=age===null?'수신 시각 확인 불가':age<60?'방금 차량에서 수신':age<3600?`${Math.floor(age/60)}분 전 차량에서 수신`:`${Math.floor(age/3600)}시간 전 차량에서 수신`;
    const status=age===null?'상태 확인 대기':onroad===true?'주행 중':ignition===true?'시동 켜짐':onroad===false&&ignition===false?'주차 중':'상태 확인 중';
    const alerts=[];
    if(data.error||stale||age===null)alerts.push({kind:'stale',icon:'cloud-off',title:data.error?'새 정보를 가져오지 못했어요':'차량 정보가 갱신되지 않았어요',detail:'아래는 마지막 수신 기록이에요. 현재 차량 상태는 확인이 필요해요.'});
    const vehicle=raw.vehicle||{},panda=raw.panda||{},alert=raw.openpilot?.alert;
    if(!stale&&age!==null&&vehicle.available===true){
      if(flag(vehicle.can?.valid)===false||flag(vehicle.can?.timeout)===true)alerts.push({kind:'can',icon:'triangle-alert',title:'차량 통신 경고가 수신됐어요',detail:'CAN 상태를 차량에서 직접 확인해 주세요. 앱에서 해제할 수 없어요.'});
      if(vehicle.steeringFault?.permanent||vehicle.steeringFault?.temporary)alerts.push({kind:'steering',icon:'triangle-alert',title:'조향 제어 경고가 수신됐어요',detail:vehicle.steeringFault.permanent?'조향 오류가 보고됐어요. 차량의 경고를 확인해 주세요.':'일시적 조향 사용 불가가 보고됐어요. 차량에서 확인해 주세요.'});
      if(alert?.text1)alerts.push({kind:'openpilot',icon:'message-square-warning',title:alert.text1,detail:alert.text2||'차량에서 수신한 openpilot 알림이에요.'});
    }
    if(!stale&&age!==null){
      if(panda.heartbeatLost===true||(Array.isArray(panda.faults)&&panda.faults.length))alerts.push({kind:'device',icon:'cpu',title:'연결 장치 경고가 수신됐어요',detail:'Panda의 오류 또는 하트비트 손실이 보고됐어요. 장치 정보를 확인해 주세요.'});
      if(['red','danger'].includes(raw.device?.thermal?.status))alerts.push({kind:'thermal',icon:'thermometer',title:'장치 온도 경고가 수신됐어요',detail:'콤마 장치가 높은 온도 상태를 보고했어요. 장치의 안내를 확인해 주세요.'});
    }
    const impacts=data.impacts?.impacts||[];
    const recentImpact=impacts.find(i=>{const t=Date.parse(i.detected_at);return Number.isFinite(t)&&now>=t&&now-t<86400000});
    if(recentImpact)alerts.push({kind:'impact',icon:'activity',title:'최근 충격 감지 기록이 있어요',detail:'감지 시각과 센서 수치를 확인해 보세요. 충돌 여부를 확정하는 정보는 아니에요.'});
    const lat=number(state.latitude),lon=number(state.longitude);
    return {state,raw,vehicle,panda,age,stale,received,status,alerts,point:lat!==null&&lon!==null&&Math.abs(lat)<=90&&Math.abs(lon)<=180?[lon,lat]:null,
      voltage:number(state.voltage_v),temperature:number(raw.device?.thermal?.temperaturesC?.max),freeSpace:number(raw.device?.usage?.freeSpacePercent),
      trip:data.trips?.trips?.[0]||null,photos:data.snapshots?.snapshots||[],impacts};
  }
  const api={number,flag,derive};if(typeof module==='object')module.exports=api;else root.CloudOverview=api;
})(typeof window==='object'?window:globalThis);
