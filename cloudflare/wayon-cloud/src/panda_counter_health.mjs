const COUNTER_FIELDS = [
  "rxBufferOverflow",
  "txBufferOverflow",
  "spiErrorCount",
];

function nonNegativeInteger(value) {
  const number = Number(value);
  return Number.isFinite(number) && number >= 0 ? Math.trunc(number) : null;
}

function counterSnapshot(panda) {
  return Object.fromEntries(
    COUNTER_FIELDS.map((field) => [field, nonNegativeInteger(panda?.[field])]),
  );
}

function secondsBetween(previousAt, currentAt) {
  const previousMillis = Date.parse(previousAt || "");
  const currentMillis = Date.parse(currentAt || "");
  if (!Number.isFinite(previousMillis) || !Number.isFinite(currentMillis)) return null;
  return Math.max(0, Math.round((currentMillis - previousMillis) / 1000));
}

function hasActiveFault(panda) {
  const faultStatus = String(panda?.faultStatus || "").toLowerCase();
  return (
    (faultStatus !== "" && faultStatus !== "none") ||
    (Array.isArray(panda?.faults) && panda.faults.length > 0) ||
    panda?.heartbeatLost === true ||
    panda?.safetyRxChecksInvalid === true
  );
}

export function attachPandaCounterHealth(payload, previousPayload, previousUpdatedAt, updatedAt) {
  if (!payload?.panda || typeof payload.panda !== "object") return payload;

  const currentPanda = payload.panda;
  const previousPanda = previousPayload?.panda;
  const cumulative = counterSnapshot(currentPanda);
  const previous = counterSnapshot(previousPanda);
  const currentUptimeS = nonNegativeInteger(currentPanda.uptimeS);
  const previousUptimeS = nonNegativeInteger(previousPanda?.uptimeS);
  const countersDidNotReset = COUNTER_FIELDS.every((field) => (
    cumulative[field] != null &&
    previous[field] != null &&
    cumulative[field] >= previous[field]
  ));
  const samePandaBoot = (
    currentUptimeS != null &&
    previousUptimeS != null &&
    currentUptimeS >= previousUptimeS &&
    countersDidNotReset
  );
  const delta = Object.fromEntries(COUNTER_FIELDS.map((field) => [
    field,
    samePandaBoot ? cumulative[field] - previous[field] : null,
  ]));
  const newCanOverflowObserved = samePandaBoot && (
    delta.rxBufferOverflow > 0 || delta.txBufferOverflow > 0
  );
  const activeFaultCorroborated = hasActiveFault(currentPanda);

  let assessment = "baselineEstablished";
  if (samePandaBoot && !newCanOverflowObserved) {
    assessment = "okNoNewCanOverflow";
  } else if (newCanOverflowObserved && activeFaultCorroborated) {
    assessment = "newCanOverflowWithActiveFault";
  } else if (newCanOverflowObserved) {
    assessment = "newCanOverflowCounterIncrease";
  }

  payload.panda = {
    ...currentPanda,
    counterHealth: {
      assessment,
      shouldAlert: newCanOverflowObserved,
      newCanOverflowObserved,
      activeFaultCorroborated,
      samePandaBoot,
      sampleIntervalSeconds: secondsBetween(previousUpdatedAt, updatedAt),
      currentUptimeS,
      previousUptimeS,
      deltaSincePreviousSample: delta,
      cumulativeSincePandaBoot: cumulative,
      semantics: "Alert only when shouldAlert is true. Cumulative totals alone are historical.",
    },
  };
  return payload;
}

export function buildAiPandaInterface(rawPanda) {
  const panda = rawPanda && typeof rawPanda === "object" ? rawPanda : {};
  const {
    rxBufferOverflow,
    txBufferOverflow,
    spiErrorCount,
    counterHealth,
    ...healthFields
  } = panda;
  const activeFaultCorroborated = hasActiveFault(panda);
  const resolvedHealth = counterHealth || {
    assessment: "baselineUnavailable",
    shouldAlert: false,
    newCanOverflowObserved: false,
    activeFaultCorroborated,
    samePandaBoot: false,
    sampleIntervalSeconds: null,
    currentUptimeS: nonNegativeInteger(panda.uptimeS),
    previousUptimeS: null,
    deltaSincePreviousSample: {
      rxBufferOverflow: null,
      txBufferOverflow: null,
      spiErrorCount: null,
    },
    semantics: "No same-boot comparison is available. Do not alert from cumulative totals.",
  };

  return {
    ...healthFields,
    counterHealth: resolvedHealth,
    diagnosticCounters: {
      valuesAreCumulativeSincePandaBoot: true,
      rxBufferOverflowTotal: nonNegativeInteger(rxBufferOverflow),
      txBufferOverflowTotal: nonNegativeInteger(txBufferOverflow),
      spiErrorCountTotal: nonNegativeInteger(spiErrorCount),
    },
  };
}
